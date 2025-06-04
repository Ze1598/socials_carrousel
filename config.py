"""
Configuration settings for the Social Media Carousel Generator.
"""
import platform
import os

# --- Configuration ---
# Path to resources folder
RESOURCES_DIR = "resources"

# Background image with special effects
BACKGROUND_IMAGE_PATH = os.path.join(RESOURCES_DIR, "carousel_bg.png")
OUTPUT_FILENAME_PREFIX = "carousel_slide_"

# Image dimensions
IMAGE_WIDTH = 2048
IMAGE_HEIGHT = 2048

# Font sizes scaled for 2048x2048 images
TITLE_FONT_SIZE = 150  # For main title
HEADING_FONT_SIZE = 120  # For slide numbers and headings
CONTENT_FONT_SIZE = 80  # For content text

# Text color and padding
TEXT_COLOR = "white"
PADDING = 150  # Pixels from the edge
MAX_WIDTH_PX = IMAGE_WIDTH - (2 * PADDING)

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
