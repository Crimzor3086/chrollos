from PIL import Image, ImageDraw

# Create a 32x32 image with a transparent background
img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a simple chart-like icon
# Background circle
draw.ellipse([2, 2, 30, 30], fill='#2d2d2d')
# Chart line
draw.line([(8, 20), (12, 16), (16, 18), (20, 12), (24, 14)], fill='#0d6efd', width=2)
# Chart dots
for x, y in [(8, 20), (12, 16), (16, 18), (20, 12), (24, 14)]:
    draw.ellipse([x-2, y-2, x+2, y+2], fill='#0d6efd')

# Save as ICO
img.save('static/favicon.ico', format='ICO') 