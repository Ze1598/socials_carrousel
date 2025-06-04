# Social Media Carousel Generator

A Streamlit application that generates social media carousel slides with custom backgrounds and markdown text formatting.

## Features

- Create carousel slides with customizable content
- Support for markdown formatting (bold, italic, lists)
- Custom background image upload
- Automatic image resizing and centering
- PDF generation without external dependencies
- Download slides as PNG images or PDF

## Project Structure

The project follows PEP 8 best practices with a modular structure:

- `app.py` - Main application entry point
- `config.py` - Configuration settings and constants
- `text_processor.py` - Text and markdown processing utilities
- `image_processor.py` - Image manipulation and slide generation
- `pdf_generator.py` - PDF creation functionality
- `resources/` - Directory containing image assets
  - `carousel_bg.png` - Default background image
  - Other image assets

## Requirements

- Python 3.7+
- Streamlit
- Pillow (PIL)
- ReportLab
- Markdown

## Installation

```bash
pip install streamlit pillow reportlab markdown
```

## Usage

Run the application with:

```bash
streamlit run app.py
```

## How to Use

1. Choose between the default background or upload a custom one
2. Enter your main title for the first slide
3. Add content for each slide (supports markdown formatting)
4. Click "Generate Carousel" to create your slides
5. Download all slides as PNG images (ZIP) or as a PDF document

## Markdown Support

You can use markdown in your text:
- **Bold text** with `**bold**`
- *Italic text* with `*italic*`
- Lists with `- item` or `1. item`
