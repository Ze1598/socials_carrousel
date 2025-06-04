"""
PDF generation utilities for the Social Media Carousel Generator.
"""
import io
import tempfile
import os
from PIL import Image
from reportlab.pdfgen import canvas


def generate_pdf(carousel_slides):
    """
    Generate a PDF from carousel slides.
    
    Args:
        carousel_slides: List of PIL Image objects
        
    Returns:
        BytesIO: PDF file as a BytesIO object
    """
    # Create a PDF buffer
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
    return pdf_buffer
