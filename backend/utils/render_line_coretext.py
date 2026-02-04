import Cocoa
import Quartz
import CoreText
from Foundation import NSURL
import sys
import argparse

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

def render_line_coretext(text, output_path, width=1080, font_name="Arial Unicode MS", font_size=50, color="#FFFFFF", language=None):
    r, g, b = hex_to_rgb(color)
    
    # Auto-detect script for better font shaping on macOS
    # Standardize language input
    if language: language = language.lower()

    if language == "punjabi" or any(0x0A00 <= ord(c) <= 0x0A7F for c in text):
        font_name = "Kohinoor Gurmukhi"
        # Reduce font size slightly for Kohinoor as it's larger
        font_size = int(font_size * 0.9) 
    elif language == "hindi" or any(0x0900 <= ord(c) <= 0x097F for c in text):
        font_name = "Kohinoor Devanagari"
        font_size = int(font_size * 0.9)
        
    font = CoreText.CTFontCreateWithName(font_name, font_size, None)
    
    attributes = {
        CoreText.kCTFontAttributeName: font,
        CoreText.kCTForegroundColorAttributeName: Quartz.CGColorCreateGenericRGB(r, g, b, 1),
    }
    
    attr_string = CoreText.CFAttributedStringCreate(None, text, attributes)
    framesetter = CoreText.CTFramesetterCreateWithAttributedString(attr_string)
    
    # Suggest size
    constraints = Quartz.CGSizeMake(width - 50, 500) # Max 500px high per line
    fit_range = CoreText.CFRangeMake(0, 0)
    suggested_size, _ = CoreText.CTFramesetterSuggestFrameSizeWithConstraints(
        framesetter, fit_range, attributes, constraints, None
    )
    
    img_width = width
    img_height = int(suggested_size.height + 40) # Padding
    
    # Context
    color_space = Quartz.CGColorSpaceCreateDeviceRGB()
    context = Quartz.CGBitmapContextCreate(
        None,
        img_width,
        img_height,
        8,
        img_width * 4,
        color_space,
        Quartz.kCGImageAlphaPremultipliedLast
    )
    
    # Draw Background (Transparent) - Default
    
    # Center Text Logic
    text_width = suggested_size.width
    x_pos = (width - text_width) / 2
    
    # Path
    path = Quartz.CGPathCreateMutable()
    # rect = Quartz.CGRectMake(25, 20, img_width - 50, img_height - 40) 
    # Use calculated center position
    rect = Quartz.CGRectMake(x_pos, 20, text_width, img_height - 40)
    Quartz.CGPathAddRect(path, None, rect)
    
    frame = CoreText.CTFramesetterCreateFrame(framesetter, CoreText.CFRangeMake(0, 0), path, None)
    
    # Shadow (Black, soft)
    Quartz.CGContextSetShadow(context, Quartz.CGSizeMake(2, -2), 3)
    
    CoreText.CTFrameDraw(frame, context)
    
    # Save
    image_ref = Quartz.CGBitmapContextCreateImage(context)
    url = NSURL.fileURLWithPath_(output_path)
    dest = Quartz.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(dest, image_ref, None)
    Quartz.CGImageDestinationFinalize(dest)
    
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
    
    h = render_line_coretext(args.text, args.output, width=args.width, font_size=args.fontsize, color=args.color, language=args.language)
    print(h)
