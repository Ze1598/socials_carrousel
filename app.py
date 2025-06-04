"""
Social Media Carousel Generator - Main Application

A Streamlit app that generates social media carousel slides with custom backgrounds
and markdown text formatting.
"""
import streamlit as st
import io
import os
import zipfile
import textwrap
from PIL import Image, ImageDraw

from config import (
    BACKGROUND_IMAGE_PATH, OUTPUT_FILENAME_PREFIX,
    IMAGE_WIDTH, IMAGE_HEIGHT,
    TITLE_FONT_SIZE, HEADING_FONT_SIZE, CONTENT_FONT_SIZE,
    PADDING, MAX_WIDTH_PX, TEXT_COLOR, RESOURCES_DIR
)
from text_processor import get_font
from image_processor import resize_image_to_square, create_slide, draw_text_with_wrap
from pdf_generator import generate_pdf


def main():
    """Main application function."""
    # --- Streamlit App ---
    st.set_page_config(layout="centered")
    st.title("Social Media Carousel Generator")
    
    # Background image selection
    st.header("Background Image")
    
    use_custom_bg = st.checkbox("Use custom background image", value=False)
    
    if use_custom_bg:
        uploaded_bg = st.file_uploader("Upload a background image", type=["png", "jpg", "jpeg"])
        
        if uploaded_bg is not None:
            try:
                # Load the uploaded image
                background_image = Image.open(uploaded_bg).convert("RGBA")
                
                # Resize to required dimensions
                if background_image.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
                    st.info(f"Resizing uploaded image to {IMAGE_WIDTH}x{IMAGE_HEIGHT}...")
                    background_image = resize_image_to_square(background_image, IMAGE_WIDTH)
                    
                # Show preview
                st.image(background_image, caption="Custom Background Preview", width=300)
            except Exception as e:
                st.error(f"Error processing uploaded image: {e}")
                st.stop()
        else:
            st.info("Please upload a background image or uncheck the custom background option.")
            # Create a blank background as fallback
            background_image = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 255))
    else:
        # Use the default background image
        try:
            if os.path.exists(BACKGROUND_IMAGE_PATH):
                background_image = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
                if background_image.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
                    st.info(f"Resizing default background to {IMAGE_WIDTH}x{IMAGE_HEIGHT}...")
                    background_image = resize_image_to_square(background_image, IMAGE_WIDTH)
                st.image(background_image, caption="Default Background", width=300)
            else:
                st.warning(f"Default background image '{BACKGROUND_IMAGE_PATH}' not found. Using a blank background.")
                background_image = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 255))
        except Exception as e:
            st.error(f"Error opening background image: {e}")
            st.warning("Using a blank background instead.")
            background_image = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 255))
    
    # Get user input for carousel
    st.header("Enter Your Carousel Content")
    
    st.markdown("""
    ### Markdown Support
    You can use markdown in your text:
    - **Bold text** with `**bold**`
    - *Italic text* with `*italic*`
    - Lists with `- item` or `1. item`
    - And more!
    """)
    
    # Main title for the first slide
    main_title = st.text_area("Main Title (First Slide):", "**HOW TO GROW YOUR BUSINESS?**", height=80)
    
    # Session state to keep track of slides between reruns
    if 'num_content_slides' not in st.session_state:
        st.session_state.num_content_slides = 4  # Default: 4 content slides + 1 title slide
    
    # Add/remove slide controls
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Slide", key="add_slide") and st.session_state.num_content_slides < 9:
            st.session_state.num_content_slides += 1
            st.rerun()
    
    with col2:
        if st.button("➖ Remove Slide", key="remove_slide") and st.session_state.num_content_slides > 1:
            st.session_state.num_content_slides -= 1
            st.rerun()
    
    # Display total number of slides
    st.caption(f"Total slides: {st.session_state.num_content_slides + 1} (1 title slide + {st.session_state.num_content_slides} content slides)")
    
    # Create slide data structure
    slide_data = []
    slide_data.append({"heading": main_title, "content": ""})  # First slide is just the title
    
    # Collect content for content slides
    for i in range(1, st.session_state.num_content_slides + 1):
        with st.expander(f"Slide #{i+1} Content", expanded=(i == 1)):
            heading = st.text_input(f"Slide #{i+1} Heading:", f"**SUB CONTENT**", key=f"heading_{i}")
            content = st.text_area(f"Slide #{i+1} Content:", 
                                 "**Lorem ipsum** dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n\n- Point 1\n- Point 2\n\nUt enim ad minim veniam, quis nostrud ut laboris.", 
                                 height=150, key=f"content_{i}")
            slide_data.append({"heading": heading, "content": content})
    
    # --- Image Generation ---
    if st.button("Generate Carousel"):
        # Load fonts
        title_font = get_font(TITLE_FONT_SIZE)
        heading_font = get_font(HEADING_FONT_SIZE)
        content_font = get_font(CONTENT_FONT_SIZE)
        
        # Generate all slides
        carousel_slides = []
        
        # First slide is special - it's the title slide
        title_slide = background_image.copy()
        draw = ImageDraw.Draw(title_slide)
        
        # Estimate title height for better vertical centering
        title_lines = len(textwrap.wrap(main_title, width=40))  # Rough estimate for title
        title_height = title_lines * (title_font.size * 1.35)
        
        # Position title more centered vertically (at 40% from top)
        title_y = (IMAGE_HEIGHT - title_height) * 0.4
        
        # Draw main title on first slide with better wrapping
        # Use a more conservative width estimate for the title font
        title_max_width = MAX_WIDTH_PX - 100  # Extra margin to prevent overflow
        draw_text_with_wrap(draw, main_title, (PADDING, title_y), 
                           title_font, title_max_width, TEXT_COLOR, align="left")
        
        carousel_slides.append(title_slide)
        
        # Generate content slides (variable number based on user selection)
        for i in range(1, len(slide_data)):
            slide = create_slide(
                i+1,  # Slide number
                slide_data[i]["heading"],
                slide_data[i]["content"],
                background_image,
                (heading_font, content_font)
            )
            carousel_slides.append(slide)
        
        # Display preview of all slides
        st.header("Generated Carousel Slides")
        total_slides = len(carousel_slides)
        cols = st.columns(min(3, total_slides))
        
        for i, slide in enumerate(carousel_slides):
            with cols[i % 3]:
                st.image(slide, caption=f"Slide {i+1}")
        
        # Create a zip file containing all slides
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for i, slide in enumerate(carousel_slides):
                img_byte_arr = io.BytesIO()
                slide.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"{OUTPUT_FILENAME_PREFIX}{i+1}.png", img_byte_arr.getvalue())
        
        # Create a PDF from the slides
        pdf_buffer = generate_pdf(carousel_slides)
        
        # Display download buttons side by side
        col1, col2 = st.columns(2)
        
        # Offer download of the zip file
        with col1:
            st.download_button(
                label="Download All Slides (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="carousel_slides.zip",
                mime="application/zip"
            )
        
        # Offer download of the PDF
        with col2:
            st.download_button(
                label="Download PDF",
                data=pdf_buffer.getvalue(),
                file_name="carousel_slides.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Fill in the content for each slide and click 'Generate Carousel'.")


if __name__ == "__main__":
    main()
