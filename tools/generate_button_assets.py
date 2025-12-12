"""
Generate pixel-art button container assets for the project.
Creates two images in `Assets/Images`: `button_container.png` and `button_container_pressed.png`.
Run: python tools/generate_button_assets.py
Requires: Pillow (pip install pillow)
"""
from PIL import Image, ImageDraw
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(BASE_DIR, "Assets", "Images")
if not os.path.isdir(OUT_DIR):
    os.makedirs(OUT_DIR, exist_ok=True)


def make_button(filename, width=64, height=20, scale=4, outer=(12,12,16), frame=(60,60,90), fill=(28,28,48), accent=(120,200,255), pressed=False):
    # Work in a small pixel canvas then scale up with NEAREST to keep crisp pixels
    w, h = width, height
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Outer border
    d.rectangle((0, 0, w - 1, h - 1), fill=outer)
    # Inner frame (one-pixel inset)
    d.rectangle((1, 1, w - 2, h - 2), fill=frame)
    # Inner fill (two-pixel inset)
    inner_fill_color = tuple(max(0, c - 6) for c in fill) if pressed else fill
    d.rectangle((2, 2, w - 3, h - 3), fill=inner_fill_color)

    # Add subtle top highlight and bottom shadow for non-pressed
    if not pressed:
        hl = tuple(min(255, int(c * 1.25)) for c in inner_fill_color)
        sh = tuple(max(0, int(c * 0.7)) for c in inner_fill_color)
        # highlight row
        for x in range(3, w - 3):
            d.point((x, 3), fill=hl)
        # shadow row
        for x in range(3, w - 3):
            d.point((x, h - 4), fill=sh)
    else:
        # pressed: darker inset line to indicate depth
        for x in range(3, w - 3):
            d.point((x, h - 4), fill=tuple(max(0, int(c * 0.6)) for c in inner_fill_color))

    # Small corner pixel accents (pixel-art style)
    d.point((2, 2), fill=accent)
    d.point((w - 3, 2), fill=accent)

    # Scale up
    out = im.resize((w * scale, h * scale), resample=Image.NEAREST)
    out.save(filename)
    print(f"Wrote {filename}")


if __name__ == '__main__':
    normal_path = os.path.join(OUT_DIR, "button_container.png")
    pressed_path = os.path.join(OUT_DIR, "button_container_pressed.png")

    # Larger buttons for more padding
    make_button(normal_path, width=64, height=20, scale=4, outer=(12,12,16), frame=(60,60,90), fill=(28,28,48), accent=(150,220,255), pressed=False)
    make_button(pressed_path, width=64, height=20, scale=4, outer=(10,10,12), frame=(45,45,70), fill=(22,22,38), accent=(100,180,230), pressed=True)

    print("Done generating button assets.")
