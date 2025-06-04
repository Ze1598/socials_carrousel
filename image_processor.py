"""
Image processing utilities for the Social Media Carousel Generator.
"""
import textwrap
from PIL import Image, ImageDraw

from config import (
    IMAGE_WIDTH, IMAGE_HEIGHT, PADDING, MAX_WIDTH_PX, TEXT_COLOR
)
from text_processor import parse_markdown, get_font


def resize_image_to_square(image, target_size):
    """
    Resize an image to a square with the specified dimensions.
    Maintains aspect ratio and centers the image, filling with transparency.
    """
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
    new_image.paste(resized_image, (paste_x, paste_y), 
                   resized_image if resized_image.mode == 'RGBA' else None)
    
    return new_image


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
    """Creates a single slide for the carousel."""
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
