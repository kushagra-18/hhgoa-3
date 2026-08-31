from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_sample_faces():
    samples_dir = Path("./data/samples")
    samples_dir.mkdir(parents=True, exist_ok=True)

    faces_info = [
        ("sample_sataboris.jpg", "Satoshi Borisov", (30, 41, 59), (56, 189, 248)),
        ("sample_elena.jpg", "Dr. Elena Rostova", (49, 46, 129), (192, 132, 252)),
        ("sample_alex.jpg", "Alex Vance", (15, 23, 42), (52, 211, 153)),
    ]

    for filename, name, bg_color, accent_color in faces_info:
        img = Image.new("RGB", (480, 480), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw subtle background grid/tech pattern
        for y in range(0, 480, 40):
            draw.line([(0, y), (480, y)], fill=(bg_color[0] + 10, bg_color[1] + 10, bg_color[2] + 10), width=1)
        for x in range(0, 480, 40):
            draw.line([(x, 0), (x, 480)], fill=(bg_color[0] + 10, bg_color[1] + 10, bg_color[2] + 10), width=1)

        # Draw stylized face
        # Shoulders
        draw.ellipse([80, 320, 400, 580], fill=(40, 50, 70), outline=accent_color, width=2)
        # Head / Face oval
        draw.ellipse([140, 100, 340, 340], fill=(235, 210, 190), outline=(200, 170, 150), width=3)
        # Hair
        draw.chord([140, 80, 340, 220], 180, 360, fill=(45, 30, 20))
        # Eyes
        draw.ellipse([180, 180, 210, 200], fill=(255, 255, 255), outline=(50, 50, 50), width=1)
        draw.ellipse([190, 185, 202, 197], fill=(30, 80, 140))
        draw.ellipse([270, 180, 300, 200], fill=(255, 255, 255), outline=(50, 50, 50), width=1)
        draw.ellipse([278, 185, 290, 197], fill=(30, 80, 140))
        # Eyebrows
        draw.line([(175, 170), (215, 172)], fill=(45, 30, 20), width=3)
        draw.line([(265, 172), (305, 170)], fill=(45, 30, 20), width=3)
        # Nose
        draw.line([(240, 205), (235, 240)], fill=(180, 140, 120), width=3)
        draw.line([(235, 240), (248, 240)], fill=(180, 140, 120), width=3)
        # Mouth / Smile
        draw.arc([205, 255, 275, 285], 20, 160, fill=(180, 70, 70), width=3)

        # Label tag
        draw.rectangle([20, 20, 460, 60], fill=(15, 23, 42, 200), outline=accent_color, width=1)
        draw.text((35, 30), f"TEST SCAN: {name}", fill=accent_color)

        save_path = samples_dir / filename
        img.save(str(save_path), quality=95)
        print(f"Generated sample: {save_path}")

if __name__ == "__main__":
    create_sample_faces()
