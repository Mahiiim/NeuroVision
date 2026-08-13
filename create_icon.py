"""
create_icon.py — Generate assets/app_icon.ico programmatically.

Draws a professional NeuroDrishti icon using Pillow:
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

        # ── Background circle ──────────────────────────────────
        draw.ellipse([0, 0, size - 1, size - 1], fill=(10, 15, 30, 255))

        # ── Outer glow ring ────────────────────────────────────
        ring_w = max(1, size // 32)
        draw.ellipse(
            [ring_w, ring_w, size - 1 - ring_w, size - 1 - ring_w],
            outline=(0, 180, 255, 180),
            width=ring_w,
        )

        # ── Eye white shape (horizontal ellipse) ───────────────
        ew = size * 0.72
        eh = size * 0.36
        ex1 = cx - ew / 2
        ey1 = cy - eh / 2
        ex2 = cx + ew / 2
        ey2 = cy + eh / 2
        draw.ellipse([ex1, ey1, ex2, ey2], fill=(0, 30, 60, 255))

        # ── Iris ───────────────────────────────────────────────
        ir = size * 0.155
        draw.ellipse(
            [cx - ir, cy - ir, cx + ir, cy + ir],
            fill=(0, 90, 160, 255),
        )

        # ── Inner iris glow ────────────────────────────────────
        ig = ir * 0.65
        draw.ellipse(
            [cx - ig, cy - ig, cx + ig, cy + ig],
            fill=(0, 180, 255, 255),
        )

        # ── Pupil ──────────────────────────────────────────────
        pp = ig * 0.45
        draw.ellipse(
            [cx - pp, cy - pp, cx + pp, cy + pp],
            fill=(5, 10, 25, 255),
        )

        # ── Pupil highlight ────────────────────────────────────
        hl = pp * 0.35
        draw.ellipse(
            [cx - hl * 0.5, cy - pp * 0.7, cx + hl * 0.5, cy - pp * 0.2],
            fill=(255, 255, 255, 200),
        )

        # ── Neural dots (radiating from iris) ──────────────────
        if size >= 48:
            n_dots = 8
            dot_r_start = ir * 1.35
            dot_r_end = ir * 2.0
            dot_size = max(1, size // 48)
            for i in range(n_dots):
                angle = (2 * math.pi / n_dots) * i
                for frac in (0.55, 1.0):
                    rr = dot_r_start + (dot_r_end - dot_r_start) * frac
                    dx = cx + rr * math.cos(angle)
                    dy = cy + rr * math.sin(angle)
                    alpha = 220 if frac == 0.55 else 120
                    draw.ellipse(
                        [dx - dot_size, dy - dot_size, dx + dot_size, dy + dot_size],
                        fill=(0, 200, 255, alpha),
                    )

        # ── Eye outline ────────────────────────────────────────
        lw = max(1, size // 48)
        draw.ellipse([ex1, ey1, ex2, ey2], outline=(0, 200, 255, 220), width=lw)

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
