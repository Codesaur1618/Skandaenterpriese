"""
Generate PWA icons with "Skanda" app name text.
No input image needed - creates icons with text.

Usage:
    python generate_skanda_icons.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_skanda_icons(output_dir='static/icons', app_name='Skanda'):
    """Generate PWA icons with app name text."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Required icon sizes for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    # Color scheme matching your app (from style.css)
    bg_color = (59, 130, 246)  # Primary blue #3b82f6
    text_color = (255, 255, 255)  # White
    
    try:
        for size in sizes:
            # Create new image with background color
            img = Image.new('RGB', (size, size), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Calculate font size (approximately 40% of icon size)
            font_size = int(size * 0.4)
            
            # Try to use a nice font, fallback to default
            try:
                # Try to load a system font (adjust path for your OS)
                # Windows
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    # Linux/Mac
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                    except:
                        font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), app_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position to center text
            x = (size - text_width) / 2
            y = (size - text_height) / 2 - bbox[1]  # Adjust for baseline
            
            # Draw text
            draw.text((x, y), app_name, fill=text_color, font=font)
            
            # Save icon
            icon_path = output_path / f'icon-{size}x{size}.png'
            img.save(icon_path, 'PNG', optimize=True)
            print(f'Generated: {icon_path}')
        
        print(f'\n✅ Successfully generated {len(sizes)} icons with "{app_name}" text in {output_path}')
        print('\nNext steps:')
        print('1. Review the generated icons')
        print('2. Commit the icons to your repository')
        print('3. Deploy your app!')
        
    except Exception as e:
        print(f'❌ Error generating icons: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    generate_skanda_icons()