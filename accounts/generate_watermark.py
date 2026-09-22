from PIL import Image, ImageDraw, ImageFont
import math

def create_watermark(text="ગીતાંજલી કોલેજ", output_path="watermark.png"):
    # Create a large transparent image
    width, height = 800, 1000
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    
    # Try to load a font, fallback to default
    try:
        # Nirmala UI usually supports Gujarati on Windows
        font = ImageFont.truetype("Nirmala.ttf", 60)
    except IOError:
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            font = ImageFont.load_default()
            
    # Create a drawing context
    draw = ImageDraw.Draw(image)
    
    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Position text in the center
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Draw text in a light gray color with some transparency
    draw.text((x, y), text, font=font, fill=(200, 200, 200, 128))
    
    # Rotate the image
    rotated = image.rotate(45, expand=1)
    
    # Save the watermark
    rotated.save(output_path, 'PNG')
    print(f"Watermark saved to {output_path}")

if __name__ == "__main__":
    create_watermark()
