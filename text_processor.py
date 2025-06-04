"""
Text processing utilities for the Social Media Carousel Generator.
"""
import re
import textwrap
import markdown
from html.parser import HTMLParser
from PIL import ImageFont

from config import (
    REGULAR_FONT_PATH, BOLD_FONT_PATH, ITALIC_FONT_PATH, BOLD_ITALIC_FONT_PATH
)


class HTMLTextParser(HTMLParser):
    """HTML Parser to convert HTML to formatted text."""
    
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
    """Parse markdown text into segments with style information."""
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
    """Get the appropriate font based on style."""
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
