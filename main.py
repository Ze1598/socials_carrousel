import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os

# --- Configuration ---
TEMPLATE_IMAGE_PATH = "template.png" # Make sure this image is in the same directory
OUTPUT_FILENAME = "generated_quote_image.png"
FONT_PATH = None # Set to a path like "arial.ttf" if needed, otherwise PIL uses a default font
FONT_SIZE_TOP = 120 # Adjust as needed
FONT_SIZE_BOTTOM = 55 # Adjust as needed
TEXT_COLOR = "white"
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1080
PADDING = 80 # Pixels from the edge
MAX_WIDTH_PX = IMAGE_WIDTH - (2 * PADDING)

# --- Helper Function to Draw Text with Wrapping ---
def draw_text_with_wrap(draw, text, position, font, max_width, fill):
    """Draws text on an image, wrapping it within max_width."""
    x, y = position
    lines = textwrap.wrap(text, width=40) # Adjust width heuristic based on font/size if needed

    # Estimate line width more accurately (simple heuristic)
    # A more precise way involves font.getlength(line) but can be slower
    avg_char_width = font.size * 0.45 # Rough estimate
    max_chars_per_line = int(max_width / avg_char_width) if avg_char_width > 0 else 10
    lines = textwrap.wrap(text, width=max_chars_per_line if max_chars_per_line > 0 else 1)

    current_y = y
    for line in lines:
        # Get text size using getbbox or textbbox (newer Pillow versions)
        try:
            # Newer Pillow versions (>= 9.2.0) use textbbox
            line_bbox = draw.textbbox((x, current_y), line, font=font)
        except AttributeError:
            # Older Pillow versions use textsize
             # textsize is deprecated, but provide fallback
            line_width, line_height = draw.textsize(line, font=font)
            line_bbox = (x, current_y, x + line_width, current_y + line_height)


        # Calculate line width and height from bounding box
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]

        # Center the text horizontally
        # line_x = x + (max_width - line_width) / 2
        line_x = PADDING
        
        # Handle potential negative x if text is wider than max_width (shouldn't happen with wrap)
        line_x = max(x, line_x) 

        draw.text((line_x, current_y), line, font=font, fill=fill)
        current_y += line_height * 1.35 # Add line spacing (adjust 1.2 factor as needed)
    return current_y # Return the y position after the last line


# --- Streamlit App ---
st.set_page_config(layout="centered")
st.title("Quote Image Generator")

# Check if template image exists
if not os.path.exists(TEMPLATE_IMAGE_PATH):
    st.error(f"Error: Template image '{TEMPLATE_IMAGE_PATH}' not found.")
    st.info("Please make sure the template image file is in the same directory as the script.")
    st.stop() # Stop execution if template is missing

# Load the template image
try:
    template_image = Image.open(TEMPLATE_IMAGE_PATH).convert("RGBA")
    if template_image.size != (IMAGE_WIDTH, IMAGE_WIDTH):
         st.warning(f"Template image is not {IMAGE_WIDTH}x{IMAGE_WIDTH}. Resizing...")
         template_image = template_image.resize((IMAGE_WIDTH, IMAGE_WIDTH))

except Exception as e:
    st.error(f"Error opening template image: {e}")
    st.stop()


# Get user input
st.header("Enter Your Quotes")
top_quote = st.text_area("Top Quote:", "Just do it well.", height=100)
bottom_quote = st.text_area("Bottom Quote:", "Don't think of excuses, just show up and do the work well.", height=150)

# --- Image Generation ---
if st.button("Generate Image"):
    if not top_quote and not bottom_quote:
        st.warning("Please enter text for at least one quote.")
    else:
        # Create a copy to draw on
        img_with_text = template_image.copy()
        draw = ImageDraw.Draw(img_with_text)
        # draw = Image.new(mode="RGB", size=(IMAGE_WIDTH, IMAGE_HEIGHT), color=(0, 0, 0))


        # Load font
        try:
            font_top = ImageFont.truetype(FONT_PATH, FONT_SIZE_TOP) if FONT_PATH else ImageFont.load_default(size=FONT_SIZE_TOP)
            font_bottom = ImageFont.truetype(FONT_PATH, FONT_SIZE_BOTTOM) if FONT_PATH else ImageFont.load_default(size=FONT_SIZE_BOTTOM)
        except IOError:
            st.error(f"Error loading font. Using default font.")
            # Use Pillow's default font if custom font fails or is not specified
            font_top = ImageFont.load_default(size=FONT_SIZE_TOP)
            font_bottom = ImageFont.load_default(size=FONT_SIZE_BOTTOM)
        except Exception as e:
             st.error(f"An unexpected error occurred loading the font: {e}")
             st.stop()


        # Define text positions (adjust Y values as needed)
        top_text_y = 150
        bottom_text_y = 480 # Start position for bottom text (will be adjusted by top text height if top text exists)


        # Draw top quote if present
        if top_quote:
             last_y_top = draw_text_with_wrap(draw, top_quote, (PADDING, top_text_y), font_top, MAX_WIDTH_PX, TEXT_COLOR)
             # Adjust bottom text start position based on where top text ended
             bottom_text_y = last_y_top + 50 # Add some spacing between quotes


        # Draw bottom quote if present
        if bottom_quote:
             draw_text_with_wrap(draw, bottom_quote, (PADDING, bottom_text_y), font_bottom, MAX_WIDTH_PX, TEXT_COLOR)


        # --- Display and Download ---
        st.header("Generated Image")
        st.image(img_with_text, caption="Generated Image")

        # Prepare image for download
        img_byte_arr = io.BytesIO()
        img_with_text.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        st.download_button(
            label="Download Image",
            data=img_byte_arr,
            file_name=OUTPUT_FILENAME,
            mime="image/png"
        )
else:
     st.info("Enter your quotes and click 'Generate Image'.")