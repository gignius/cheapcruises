#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

def create_og_image():
    # Create image with cruise blue gradient background
    width, height = 1200, 630
    img = Image.new('RGB', (width, height), color='#0284c7')
    draw = ImageDraw.Draw(img)
    
    # Create gradient effect
    for i in range(height):
        shade = int(2 + (133 - 2) * (i / height))  # From #0284c7 to #0369a1
        color = (shade, 132 + int((161 - 132) * (i / height)), 199)
        draw.line([(0, i), (width, i)], fill=color)
    
    # Add semi-transparent overlay for text readability
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 80))
    img.paste(overlay, (0, 0), overlay)
    
    # Use default font (we'll make it bold by drawing twice)
    try:
        # Try to use a system font
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        # Fallback to default
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        price_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add emoji and title
    emoji = "🚢"
    title = "CheapCruises.au"
    
    # Calculate positions for centered text
    title_y = 80
    
    # Draw title with shadow for depth
    draw.text((620, title_y + 2), emoji, fill=(0, 0, 0, 128), font=title_font, anchor="mm")
    draw.text((620, title_y), emoji, fill='white', font=title_font, anchor="mm")
    
    # Draw main message
    main_text = "South Pacific & Aussie Cruises"
    draw.text((600, 200 + 2), main_text, fill=(0, 0, 0, 128), font=subtitle_font, anchor="mm")
    draw.text((600, 200), main_text, fill='white', font=subtitle_font, anchor="mm")
    
    # Draw price highlight
    price_text = "from $50 AUD/night"
    draw.text((600, 320 + 3), price_text, fill=(0, 0, 0, 128), font=price_font, anchor="mm")
    draw.text((600, 320), price_text, fill='#FCD34D', font=price_font, anchor="mm")
    
    quad_text = "(quad occupancy)"
    draw.text((600, 430 + 2), quad_text, fill=(0, 0, 0, 128), font=subtitle_font, anchor="mm")
    draw.text((600, 430), quad_text, fill='white', font=subtitle_font, anchor="mm")
    
    # Draw bottom text
    bottom_text = "Australia & New Zealand • 11 Cruise Lines"
    draw.text((600, 550 + 2), bottom_text, fill=(0, 0, 0, 128), font=small_font, anchor="mm")
    draw.text((600, 550), bottom_text, fill='white', font=small_font, anchor="mm")
    
    # Save image
    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    output_path = os.path.join(static_dir, 'og-image.jpg')
    img.convert('RGB').save(output_path, 'JPEG', quality=95)
    print(f"✅ Created OG image: {output_path}")
    print(f"   Size: {width}x{height}")
    return output_path

if __name__ == "__main__":
    create_og_image()
