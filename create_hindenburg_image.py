from PIL import Image, ImageDraw, ImageFont
import textwrap

# Create a 1080x1350 image (the Cluefolio format)
img = Image.new('RGB', (1080, 1350), color='#1a1a2e')
draw = ImageDraw.Draw(img)

# Draw the lower area (ground/river)
draw.rectangle([0, 900, 1080, 1350], fill='#2d3748')

# Draw the airship as a dark shape - simplified representation
# The Hindenburg was coming in for a landing
ship_y = 700
# Upper fin area (where the fire started - visible as a bright point)
draw.polygon([(400, ship_y), (680, ship_y-100), (680, ship_y+100), (400, ship_y)], fill='#4a5568')
# Hull below
draw.polygon([(350, ship_y+100), (730, ship_y+100), (730, 900), (350, 900)], fill='#2d3748')

# Add "flame" detail at the upper fin (the fire ignition point)
draw.polygon([(550, ship_y-120), (620, ship_y-180), (690, ship_y-120)], fill='#fc8181')
# Additional flames spreading
draw.polygon([(450, ship_y+80), (520, ship_y+150), (590, ship_y+80)], fill='#fc8181')

# Add headline text
try:
    font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 32)
    small_font = ImageFont.truetype("C:/Windows/Fonts/georgiai.ttf", 20)
except:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
    small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)

# headline-like text
title_text = "THE AIRSHIP FELL FROM THE SKY"
draw.text((60, 50), title_text, fill='white', font=font)
dateline_text = "Lakehurst, New Jersey · May 6, 1937"
draw.text((60, 90), dateline_text, fill='#a0aec0', font=small_font)

# description
desc_text = "The Hindenburg was coming in for a landing when it caught fire and fell from the sky.\n36 people died in thirty-four seconds. The cause remains officially undetermined."
lines = desc_text.split('\n')
y = 130
for line in lines:
    draw.text((60, y), line, fill='#718096', font=small_font)
    y += 22

# Save the image
img.save('C:\\Users\\Lenovo\\AI\\Cluefolio\\content\\hinderburg\\images\\01-cover.jpg', 'JPEG', quality=92, progressive=True)
print('Image created successfully at content/hinderburg/images/01-cover.jpg')