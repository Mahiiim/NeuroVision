"""
create_icon.py — Generate assets/app_icon.ico programmatically.

Draws a professional NeuroVision icon using Pillow:
  - Dark navy background circle
  - Glowing cyan eye shape
  - Neural dot pattern radiating from iris
  - Works on any machine without external image files
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    frames = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = cy = size / 2
        r = size / 2

        # ── Background ─────────────────────────────────────────
        # Transparent background

        # ── Eye shape (blue outline, white interior) ───────────
        ew = size * 0.9
        eh = size * 0.45
        ex1 = cx - ew / 2
        ey1 = cy - eh / 2
        ex2 = cx + ew / 2
        ey2 = cy + eh / 2
        
        # Draw white interior
        draw.ellipse([ex1, ey1, ex2, ey2], fill=(255, 255, 255, 255))
        
        # Draw blue outline
        lw = max(1, size // 24)
        draw.ellipse([ex1, ey1, ex2, ey2], outline=(0, 50, 120, 255), width=lw)

        # ── Neuron shape (yellow) ──────────────────────────────
        ir = size * 0.18
        # Main neuron body
        draw.ellipse(
            [cx - ir, cy - ir, cx + ir, cy + ir],
            fill=(255, 180, 0, 255),
        )

        # Neural branches (dendrites)
        if size >= 32:
            n_branches = 6
            branch_len = ir * 1.5
            for i in range(n_branches):
                angle = (2 * math.pi / n_branches) * i
                dx = cx + branch_len * math.cos(angle)
                dy = cy + branch_len * math.sin(angle)
                
                # Draw branch line
                draw.line([(cx, cy), (dx, dy)], fill=(255, 180, 0, 255), width=max(1, size//32))
                
                # Draw terminal bouton
                bouton_r = max(1, size // 40)
                draw.ellipse([dx - bouton_r, dy - bouton_r, dx + bouton_r, dy + bouton_r], fill=(255, 180, 0, 255))

        frames.append(img)

    # Save as multi-size .ico
    os.makedirs("assets", exist_ok=True)
    frames[0].save(
        "assets/app_icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Icon saved to assets/app_icon.ico  ({len(sizes)} sizes)")

if __name__ == "__main__":
    create_icon()
