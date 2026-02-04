import sys
import argparse
import os
from PIL import Image, ImageDraw, ImageFont

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def find_font(language, font_size):
    """Attempt to find a suitable font for the given language."""
    # Common font paths for Linux (Cloud Run) and macOS (Local)
    possible_fonts = []
    
    if language == "punjabi":
        possible_fonts.extend([
            "/usr/share/fonts/truetype/lohit-punjabi/Lohit-Punjabi.ttf",
            "/System/Library/Fonts/Supplemental/KohinoorGurmukhi.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansGurmukhi-Regular.ttf"
        ])
    elif language == "hindi":
        possible_fonts.extend([
            "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
            "/System/Library/Fonts/Supplemental/KohinoorDevanagari.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf"
        ])
    
    # Generic fallbacks
    possible_fonts.extend([
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "Arial Unicode.ttf",
        "Arial.ttf"
    ])

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
    
    # Ultimate fallback
    return ImageFont.load_default()

def render_line_pil(text, output_path, width=1080, font_size=50, color="#FFFFFF", language=None):
    r, g, b = hex_to_rgb(color)
    
    if language:
        language = language.lower()
    
    # Adjust font size for Pillow vs CoreText
    adj_font_size = int(font_size * 1.2)
    
    font = find_font(language, adj_font_size)
    
    # Measure text size
    # Create a dummy image to get a drawing context
    dummy_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)
    
    # Get text bounding box
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    img_width = width
    img_height = int(text_height + 60) # Padding
    
    # Create the actual image
    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Center position
    x_pos = (img_width - text_width) // 2
    y_pos = (img_height - text_height) // 2 - bbox[1] # Adjust for baseline
    
    # Draw shadow first
    draw.text((x_pos + 2, y_pos + 2), text, font=font, fill=(0, 0, 0, 180))
    
    # Draw main text
    draw.text((x_pos, y_pos), text, font=font, fill=(r, g, b, 255))
    
    # Save
    img.save(output_path, "PNG")
    
    return img_height

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("text", help="Text to render")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--color", default="#FFFFFF", help="Hex color")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--fontsize", type=int, default=60)
    parser.add_argument("--language", default=None, help="Target language (punjabi/hindi)")
    
    args = parser.parse_args()
    
    h = render_line_pil(args.text, args.output, width=args.width, font_size=args.fontsize, color=args.color, language=args.language)
    print(h)
