import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import zipfile
import base64
import tempfile
import re
import markdown
from html.parser import HTMLParser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import sys
import platform

# --- Configuration ---
# Always use the carousel_bg.png image as background
BACKGROUND_IMAGE_PATH = "carousel_bg.png" # Background image with special effects
OUTPUT_FILENAME_PREFIX = "carousel_slide_"

# Font configuration
# Try to use system fonts based on the platform
if platform.system() == "Darwin":  # macOS
    REGULAR_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
    BOLD_FONT_PATH = "/System/Library/Fonts/Helvetica-Bold.ttf"
    ITALIC_FONT_PATH = "/System/Library/Fonts/Helvetica-Oblique.ttf"
    BOLD_ITALIC_FONT_PATH = "/System/Library/Fonts/Helvetica-BoldOblique.ttf"
elif platform.system() == "Windows":
    REGULAR_FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
    BOLD_FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"
    ITALIC_FONT_PATH = "C:\\Windows\\Fonts\\ariali.ttf"
    BOLD_ITALIC_FONT_PATH = "C:\\Windows\\Fonts\\arialbi.ttf"
else:  # Linux and others
    REGULAR_FONT_PATH = None
    BOLD_FONT_PATH = None
    ITALIC_FONT_PATH = None
    BOLD_ITALIC_FONT_PATH = None

# Image dimensions
IMAGE_WIDTH = 2048
IMAGE_HEIGHT = 2048

# Font sizes scaled for 2048x2048 images (approximately doubled from 1080x1080)
TITLE_FONT_SIZE = 150 # For main title
HEADING_FONT_SIZE = 120 # For slide numbers and headings
CONTENT_FONT_SIZE = 80 # For content text

# Text color and padding
TEXT_COLOR = "white"
PADDING = 150 # Pixels from the edge (scaled up from 80)
MAX_WIDTH_PX = IMAGE_WIDTH - (2 * PADDING)

# --- Helper Functions ---
# HTML Parser to convert HTML to formatted text
class HTMLTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.format_stack = []
        self.list_stack = []
        self.in_list_item = False
        self.current_link = None
        
    def handle_starttag(self, tag, attrs):
        if tag == 'strong' or tag == 'b':
            self.format_stack.append('bold')
        elif tag == 'em' or tag == 'i':
            self.format_stack.append('italic')
        elif tag == 'u':
            self.format_stack.append('underline')
        elif tag == 'a':
            href = next((attr[1] for attr in attrs if attr[0] == 'href'), None)
            self.current_link = href
        elif tag == 'ul' or tag == 'ol':
            list_type = 'ul' if tag == 'ul' else 'ol'
            self.list_stack.append({'type': list_type, 'count': 0})
        elif tag == 'li':
            self.in_list_item = True
            if self.list_stack:
                current_list = self.list_stack[-1]
                current_list['count'] += 1
                prefix = '• ' if current_list['type'] == 'ul' else f"{current_list['count']}. "
                indent = '  ' * (len(self.list_stack) - 1)
                self.text.append(f"\n{indent}{prefix}")
            
    def handle_endtag(self, tag):
        if tag in ('strong', 'b', 'em', 'i', 'u'):
            if self.format_stack:
                self.format_stack.pop()
        elif tag == 'a':
            if self.current_link:
                self.text.append(f" ({self.current_link})")
                self.current_link = None
        elif tag == 'p':
            self.text.append('\n\n')
        elif tag == 'br':
            self.text.append('\n')
        elif tag == 'li':
            self.in_list_item = False
        elif tag in ('ul', 'ol'):
            if self.list_stack:
                self.list_stack.pop()
            self.text.append('\n')
            
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)

def parse_markdown(text):
    """Parse markdown text into segments with style information"""
    segments = []
    
    # Process bold and italic
    # First, split the text by markdown indicators
    i = 0
    in_bold = False
    in_italic = False
    current_text = ""
    
    while i < len(text):
        # Check for bold marker
        if i < len(text) - 1 and text[i:i+2] == "**":
            # Add current segment
            if current_text:
                segments.append({
                    "text": current_text,
                    "bold": in_bold,
                    "italic": in_italic
                })
                current_text = ""
            
            # Toggle bold state
            in_bold = not in_bold
            i += 2
        # Check for italic marker
        elif text[i] == "*":
            # Add current segment
            if current_text:
                segments.append({
                    "text": current_text,
                    "bold": in_bold,
                    "italic": in_italic
                })
                current_text = ""
            
            # Toggle italic state
            in_italic = not in_italic
            i += 1
        else:
            current_text += text[i]
            i += 1
    
    # Add final segment if any
    if current_text:
        segments.append({
            "text": current_text,
            "bold": in_bold,
            "italic": in_italic
        })
    
    # Process lists
    for i, segment in enumerate(segments):
        # Process bullet points
        segment["text"] = re.sub(r'^\s*-\s+', '• ', segment["text"], flags=re.MULTILINE)
        segment["text"] = re.sub(r'^\s*\*\s+', '• ', segment["text"], flags=re.MULTILINE)
        
        # Process numbered lists
        segment["text"] = re.sub(r'^\s*\d+\.\s+', lambda m: f"{m.group()}", segment["text"], flags=re.MULTILINE)
    
    return segments

def get_font(size, bold=False, italic=False):
    """Get the appropriate font based on style"""
    try:
        if bold and italic and BOLD_ITALIC_FONT_PATH:
            return ImageFont.truetype(BOLD_ITALIC_FONT_PATH, size)
        elif bold and BOLD_FONT_PATH:
            return ImageFont.truetype(BOLD_FONT_PATH, size)
        elif italic and ITALIC_FONT_PATH:
            return ImageFont.truetype(ITALIC_FONT_PATH, size)
        elif REGULAR_FONT_PATH:
            return ImageFont.truetype(REGULAR_FONT_PATH, size)
        else:
            # Fall back to default font
            return ImageFont.load_default(size=size)
    except Exception:
        # Silently fall back to default font without showing a warning
        return ImageFont.load_default(size=size)

def draw_text_with_wrap(draw, text, position, font, max_width, fill, align="left"):
    """Draws text on an image with markdown formatting."""
    x, y = position
    font_size = font.size
    
    # Parse markdown
    text_segments = parse_markdown(text)
    
    # More aggressive estimate for line width to use more space
    if font_size > 100:  # For very large fonts like title
        avg_char_width = font_size * 0.45  # Less conservative for large fonts
    else:
        avg_char_width = font_size * 0.4  # Less conservative for normal fonts
    
    # Apply a less restrictive safety factor to allow more text per line
    max_chars_per_line = int((max_width * 0.95) / avg_char_width) if avg_char_width > 0 else 10
    max_chars_per_line = max(5, max_chars_per_line)
    
    # Combine all text for initial wrapping
    combined_text = "".join(segment["text"] for segment in text_segments)
    
    # Split by newlines first to preserve intentional line breaks
    paragraphs = combined_text.split('\n')
    
    current_y = y
    for paragraph in paragraphs:
        if not paragraph.strip():  # Empty paragraph, add extra spacing
            current_y += font_size * 0.7
            continue
        
        # Wrap the paragraph text
        lines = textwrap.wrap(paragraph, width=max_chars_per_line)
        if not lines:  # Empty line
            lines = ['']
        
        for line in lines:
            # Calculate line width for alignment
            # Use regular font for width calculation for simplicity
            regular_font = get_font(font_size)
            try:
                line_bbox = draw.textbbox((x, current_y), line, font=regular_font)
            except AttributeError:
                line_width, line_height = draw.textsize(line, font=regular_font)
                line_bbox = (x, current_y, x + line_width, current_y + line_height)
            
            line_width = line_bbox[2] - line_bbox[0]
            line_height = line_bbox[3] - line_bbox[1]
            
            # Determine x position based on alignment
            if align == "center":
                line_x = x + (max_width - line_width) / 2
            elif align == "right":
                line_x = x + max_width - line_width
            else:  # left alignment
                line_x = x
            
            # Handle potential negative x if text is wider than max_width
            line_x = max(x, line_x)
            
            # Now render the line with proper styling
            # For simplicity, we'll just use the appropriate font for the whole line
            # based on the first segment's style
            current_x = line_x
            
            # Find which segments apply to this line
            # For simplicity, we'll just use bold/italic for the whole line if any segment has it
            has_bold = any(segment["bold"] for segment in text_segments if segment["text"] in line)
            has_italic = any(segment["italic"] for segment in text_segments if segment["text"] in line)
            
            styled_font = get_font(font_size, bold=has_bold, italic=has_italic)
            draw.text((current_x, current_y), line, font=styled_font, fill=fill)
            
            current_y += line_height * 1.35  # Add line spacing
    
    return current_y

def create_slide(slide_number, heading, content, background_image, fonts):
    """Creates a single slide for the carousel"""
    # Create a copy of the background image
    slide = background_image.copy()
    draw = ImageDraw.Draw(slide)
    
    # Unpack fonts
    heading_font, content_font = fonts
    
    # Calculate the total height of the content to help with vertical centering
    # First, create a temporary drawing context to measure text heights
    temp_img = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Estimate heading height
    heading_height = 0
    if heading.strip():
        # Estimate heading height based on font size and number of lines
        heading_lines = len(textwrap.wrap(heading, width=50))  # Rough estimate
        heading_height = heading_lines * (heading_font.size * 1.35)
    
    # Estimate content height
    content_lines = len(textwrap.wrap(content, width=80))  # Rough estimate
    content_height = content_lines * (content_font.size * 1.35)
    
    # Add spacing between heading and content if heading exists
    spacing = 100 if heading.strip() else 0
    
    # Calculate total content height
    total_content_height = heading_height + spacing + content_height
    
    # Calculate vertical position to center content better
    # Use 40% from top instead of 50% to give slightly more space at the bottom
    vertical_start = (IMAGE_HEIGHT - total_content_height) * 0.4
    
    # Ensure minimum top margin
    heading_y = max(PADDING + 200, vertical_start)  # At least 200px more than standard padding
    
    # Draw heading if it exists
    if heading.strip():
        last_y = draw_text_with_wrap(draw, heading, (PADDING, heading_y), 
                                  heading_font, MAX_WIDTH_PX, TEXT_COLOR)
        # Draw content with spacing below heading
        content_y = last_y + spacing
    else:
        # If no heading, position content directly
        content_y = heading_y
    
    # Draw content
    draw_text_with_wrap(draw, content, (PADDING, content_y), 
                      content_font, MAX_WIDTH_PX, TEXT_COLOR)
    
    return slide


# --- Helper function for image resizing ---
def resize_image_to_square(image, target_size):
    """Resize an image to a square with the specified dimensions.
    Maintains aspect ratio and centers the image, filling with transparency."""
    # Get the original image dimensions
    original_width, original_height = image.size
    
    # Create a new square transparent image
    new_image = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    
    # Calculate the resize ratio
    ratio = min(target_size / original_width, target_size / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    
    # Resize the original image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Calculate position to paste (centered)
    paste_x = (target_size - new_width) // 2
    paste_y = (target_size - new_height) // 2
    
    # Paste the resized image onto the new square image
    new_image.paste(resized_image, (paste_x, paste_y), resized_image if resized_image.mode == 'RGBA' else None)
    
    return new_image

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
    
    # Create a PDF using reportlab where each page is just the image
    pdf_buffer = io.BytesIO()
    
    # Create a temporary directory to store images
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_image_paths = []
        
        # Save each slide as a temporary file
        for i, slide in enumerate(carousel_slides):
            temp_image_path = os.path.join(temp_dir, f"temp_slide_{i}.png")
            slide.save(temp_image_path, format='PNG')
            temp_image_paths.append(temp_image_path)
        
        # First image dimensions will determine our page size
        first_img = Image.open(temp_image_paths[0])
        img_width, img_height = first_img.size
        first_img.close()
        
        # Create canvas with page size matching the image dimensions
        c = canvas.Canvas(pdf_buffer, pagesize=(img_width, img_height))
        
        # Add each image to the PDF as a full page
        for temp_image_path in temp_image_paths:
            # Add the image to the PDF at position (0,0) with full dimensions
            c.drawImage(temp_image_path, 0, 0, width=img_width, height=img_height)
            c.showPage()
    
    c.save()
    pdf_buffer.seek(0)
    
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
        
    # PDF preview removed as requested
else:
    st.info("Fill in the content for each slide and click 'Generate Carousel'.")