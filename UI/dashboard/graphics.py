"""
UI/dashboard/graphics.py
------------------------
Anti-aliased PIL rendering primitives, vector-style icon synthesis,
illustrations, and reusable RoundedCard container for Tkinter.
"""

import math
import tkinter as tk
from functools import lru_cache
from typing import Callable, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageTk

from UI.dashboard.theme import THEME


def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hex_to_rgba(color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    r, g, b = _hex_to_rgb(color)
    return (r, g, b, alpha)


def _lerp_color(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def create_rounded_rect_image(
    width: int,
    height: int,
    radius: int,
    fill: str,
    border_color: Optional[str] = None,
    border_width: int = 1,
    bg_color: Optional[str] = None,
    shadow_color: Optional[str] = None,
    gradient_end: Optional[str] = None,
    corner_wave_color: Optional[str] = None,
    scale: int = 2,
) -> ImageTk.PhotoImage:
    """Render an anti-aliased rounded rectangle card with optional gradient, shadow, and corner wave."""
    w = max(4, int(width))
    h = max(4, int(height))
    sw, sh = w * scale, h * scale
    r = min(radius * scale, min(sw, sh) // 2 - 2)

    base_rgba = _hex_to_rgba(bg_color, 255) if bg_color else (0, 0, 0, 0)
    img = Image.new("RGBA", (sw, sh), base_rgba)
    draw = ImageDraw.Draw(img)

    pad = 2 * scale if shadow_color else 0

    if shadow_color:
        # Subtle multi-step soft drop shadow
        sr, sg, sb = _hex_to_rgb(shadow_color)
        for offset, alpha in [(2 * scale, 55), (1 * scale, 80)]:
            draw.rounded_rectangle(
                [pad, pad + offset, sw - pad - 1, sh - 1],
                radius=r,
                fill=(sr, sg, sb, alpha),
            )

    card_box = [pad, pad, sw - pad - 1, sh - pad - 1]

    if gradient_end:
        c1 = _hex_to_rgb(fill)
        c2 = _hex_to_rgb(gradient_end)
        grad = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(grad)
        for x in range(sw):
            t = x / max(1, sw - 1)
            col = _lerp_color(c1, c2, t) + (255,)
            gdraw.line([(x, 0), (x, sh)], fill=col)

        mask = Image.new("L", (sw, sh), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle(card_box, radius=r, fill=255)

        if corner_wave_color:
            wr, wg, wb = _hex_to_rgb(corner_wave_color)
            wave = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            wdraw = ImageDraw.Draw(wave)
            wdraw.ellipse([int(sw * 0.56), int(-sh * 0.25), int(sw * 1.15), int(sh * 1.18)], fill=(wr, wg, wb, 85))
            wdraw.ellipse([int(sw * 0.68), int(sh * 0.18), int(sw * 1.22), int(sh * 1.35)], fill=(wr, wg, wb, 65))
            grad = Image.alpha_composite(grad, wave)

        img.paste(grad, (0, 0), mask)
    else:
        draw.rounded_rectangle(card_box, radius=r, fill=_hex_to_rgba(fill, 255))
        if corner_wave_color:
            wave = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
            wdraw = ImageDraw.Draw(wave)
            wr, wg, wb = _hex_to_rgb(corner_wave_color)
            wdraw.ellipse([int(sw * 0.48), int(sh * 0.45), int(sw * 1.20), int(sh * 1.38)], fill=(wr, wg, wb, 75))
            mask = Image.new("L", (sw, sh), 0)
            ImageDraw.Draw(mask).rounded_rectangle(card_box, radius=r, fill=255)
            img.paste(Image.alpha_composite(img, wave), (0, 0), mask)

    if border_color and border_width > 0:
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            card_box,
            radius=r,
            outline=_hex_to_rgba(border_color, 255),
            width=max(1, border_width * scale),
        )

    out = img.resize((w, h), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(out)


@lru_cache(maxsize=128)
def _render_vector_icon_pil(
    name: str,
    size: int = 20,
    color: str = "#FFFFFF",
    bg_circle: Optional[str] = None,
) -> Image.Image:
    """
    Synthesize crisp anti-aliased icons (navigation, KPI badges, actions, header)
    using 3x supersampled PIL drawings so there are no blurry or missing assets.
    """
    scale = 3
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if bg_circle:
        draw.ellipse([0, 0, s - 1, s - 1], fill=_hex_to_rgba(bg_circle, 255))
        pad = int(s * 0.25)
    else:
        pad = int(s * 0.12)

    fg = _hex_to_rgba(color, 255)
    lw = max(2, int(s * 0.085))
    x0, y0, x1, y1 = pad, pad, s - pad, s - pad
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    span = x1 - x0

    if name == "brand_doc":
        draw.rounded_rectangle([x0 + span * 0.12, y0, x1 - span * 0.12, y1], radius=int(span * 0.16), outline=fg, width=lw)
        draw.line([(x0 + span * 0.28, y0 + span * 0.34), (x1 - span * 0.28, y0 + span * 0.34)], fill=fg, width=lw)
        draw.line([(x0 + span * 0.28, y0 + span * 0.54), (x1 - span * 0.28, y0 + span * 0.54)], fill=fg, width=lw)
        draw.line([(x0 + span * 0.28, y0 + span * 0.74), (x1 - span * 0.42, y0 + span * 0.74)], fill=fg, width=lw)

    elif name == "home":
        roof = [(cx, y0 + span * 0.06), (x0, cy - span * 0.02), (x1, cy - span * 0.02)]
        draw.polygon(roof, fill=fg)
        draw.rectangle([x0 + span * 0.16, cy - span * 0.04, x1 - span * 0.16, y1 - span * 0.04], fill=fg)
        draw.rectangle([cx - span * 0.13, cy + span * 0.16, cx + span * 0.13, y1 - span * 0.04], fill=_hex_to_rgba(THEME["colors"]["sidebar_active"], 255))

    elif name == "invoice":
        draw.rounded_rectangle([x0 + span * 0.14, y0, x1 - span * 0.14, y1], radius=int(span * 0.14), outline=fg, width=lw)
        for frac in (0.34, 0.54, 0.74):
            draw.line([(x0 + span * 0.28, y0 + span * frac), (x1 - span * 0.28, y0 + span * frac)], fill=fg, width=max(2, lw - 1))

    elif name == "clients":
        hr = span * 0.17
        draw.ellipse([cx - hr, y0 + span * 0.08, cx + hr, y0 + span * 0.08 + 2 * hr], outline=fg, width=lw)
        draw.arc([x0 + span * 0.12, cy + span * 0.06, x1 - span * 0.12, y1 + span * 0.25], start=180, end=360, fill=fg, width=lw)

    elif name == "users":
        hr = span * 0.15
        draw.ellipse([cx - span * 0.18 - hr, y0 + span * 0.1, cx - span * 0.18 + hr, y0 + span * 0.1 + 2 * hr], outline=fg, width=lw)
        draw.arc([x0 + span * 0.04, cy + span * 0.08, cx + span * 0.16, y1 + span * 0.2], start=180, end=360, fill=fg, width=lw)
        draw.ellipse([cx + span * 0.18 - hr * 0.85, y0 + span * 0.16, cx + span * 0.18 + hr * 0.85, y0 + span * 0.16 + 1.7 * hr], outline=fg, width=lw)
        draw.arc([cx - span * 0.02, cy + span * 0.12, x1 - span * 0.02, y1 + span * 0.2], start=190, end=355, fill=fg, width=lw)

    elif name == "payments":
        draw.rounded_rectangle([x0 + span * 0.04, y0 + span * 0.16, x1 - span * 0.04, y1 - span * 0.16], radius=int(span * 0.14), outline=fg, width=lw)
        draw.line([(x0 + span * 0.06, y0 + span * 0.38), (x1 - span * 0.06, y0 + span * 0.38)], fill=fg, width=lw)
        draw.line([(x0 + span * 0.18, y1 - span * 0.32), (x0 + span * 0.42, y1 - span * 0.32)], fill=fg, width=lw)

    elif name == "expense":
        draw.rounded_rectangle([x0 + span * 0.14, y0 + span * 0.06, x1 - span * 0.14, y1 - span * 0.04], radius=int(span * 0.14), outline=fg, width=lw)
        draw.line([(x0 + span * 0.28, y0 + span * 0.36), (x1 - span * 0.28, y0 + span * 0.36)], fill=fg, width=max(2, lw - 1))
        draw.line([(x0 + span * 0.28, y0 + span * 0.58), (x1 - span * 0.38, y0 + span * 0.58)], fill=fg, width=max(2, lw - 1))

    elif name == "reports":
        bw = span * 0.18
        draw.rounded_rectangle([x0 + span * 0.10, cy + span * 0.06, x0 + span * 0.10 + bw, y1 - span * 0.06], radius=3, fill=fg)
        draw.rounded_rectangle([cx - bw / 2, y0 + span * 0.16, cx + bw / 2, y1 - span * 0.06], radius=3, fill=fg)
        draw.rounded_rectangle([x1 - span * 0.10 - bw, y0 + span * 0.32, x1 - span * 0.10, y1 - span * 0.06], radius=3, fill=fg)

    elif name == "cheques":
        draw.rounded_rectangle([x0 + span * 0.04, y0 + span * 0.2, x1 - span * 0.04, y1 - span * 0.2], radius=int(span * 0.12), outline=fg, width=lw)
        draw.line([(x0 + span * 0.18, cy - span * 0.06), (x1 - span * 0.32, cy - span * 0.06)], fill=fg, width=max(2, lw - 1))
        draw.line([(x0 + span * 0.18, cy + span * 0.12), (x1 - span * 0.18, cy + span * 0.12)], fill=fg, width=max(2, lw - 1))

    elif name == "settings":
        cr = span * 0.22
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=fg, width=lw)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            tx = cx + math.cos(rad) * span * 0.37
            ty = cy + math.sin(rad) * span * 0.37
            ix = cx + math.cos(rad) * span * 0.25
            iy = cy + math.sin(rad) * span * 0.25
            draw.line([(ix, iy), (tx, ty)], fill=fg, width=lw)

    elif name == "logout":
        draw.arc([x0 + span * 0.08, y0 + span * 0.08, x0 + span * 0.72, y1 - span * 0.08], start=70, end=290, fill=fg, width=lw)
        draw.line([(cx - span * 0.05, cy), (x1 - span * 0.06, cy)], fill=fg, width=lw)
        draw.line([(x1 - span * 0.24, cy - span * 0.18), (x1 - span * 0.06, cy), (x1 - span * 0.24, cy + span * 0.18)], fill=fg, width=lw)

    elif name == "search":
        rr = span * 0.30
        draw.ellipse([x0 + span * 0.08, y0 + span * 0.08, x0 + span * 0.08 + 2 * rr, y0 + span * 0.08 + 2 * rr], outline=fg, width=lw)
        hx = x0 + span * 0.08 + 1.7 * rr
        hy = y0 + span * 0.08 + 1.7 * rr
        draw.line([(hx, hy), (x1 - span * 0.06, y1 - span * 0.06)], fill=fg, width=lw)

    elif name == "bell":
        draw.arc([x0 + span * 0.18, y0 + span * 0.1, x1 - span * 0.18, y1 - span * 0.18], start=180, end=360, fill=fg, width=lw)
        draw.line([(x0 + span * 0.18, cy + span * 0.04), (x0 + span * 0.1, y1 - span * 0.24), (x1 - span * 0.1, y1 - span * 0.24), (x1 - span * 0.18, cy + span * 0.04)], fill=fg, width=lw)
        draw.arc([cx - span * 0.12, y1 - span * 0.28, cx + span * 0.12, y1 - span * 0.06], start=0, end=180, fill=fg, width=lw)

    elif name == "trend_up":
        pts = [(x0 + span * 0.06, y1 - span * 0.22), (cx - span * 0.08, cy + span * 0.06), (cx + span * 0.1, cy + span * 0.18), (x1 - span * 0.08, y0 + span * 0.20)]
        draw.line(pts, fill=fg, width=lw, joint="curve")
        draw.line([(x1 - span * 0.26, y0 + span * 0.18), (x1 - span * 0.06, y0 + span * 0.18), (x1 - span * 0.06, y0 + span * 0.38)], fill=fg, width=lw)

    elif name == "wallet":
        draw.rounded_rectangle([x0 + span * 0.06, y0 + span * 0.18, x1 - span * 0.06, y1 - span * 0.14], radius=int(span * 0.14), fill=fg)
        draw.rounded_rectangle([cx + span * 0.08, cy - span * 0.08, x1 - span * 0.02, cy + span * 0.16], radius=int(span * 0.08), fill=_hex_to_rgba("#FEE2E2", 255))

    elif name == "cart":
        draw.line([(x0 + span * 0.06, y0 + span * 0.16), (x0 + span * 0.22, y0 + span * 0.16), (x0 + span * 0.34, cy + span * 0.16), (x1 - span * 0.12, cy + span * 0.16), (x1 - span * 0.06, y0 + span * 0.30), (x0 + span * 0.25, y0 + span * 0.30)], fill=fg, width=lw)
        draw.ellipse([x0 + span * 0.34, y1 - span * 0.22, x0 + span * 0.48, y1 - span * 0.08], fill=fg)
        draw.ellipse([x1 - span * 0.28, y1 - span * 0.22, x1 - span * 0.14, y1 - span * 0.08], fill=fg)

    elif name == "pie":
        draw.pieslice([x0 + span * 0.06, y0 + span * 0.06, x1 - span * 0.06, y1 - span * 0.06], start=35, end=330, fill=fg)

    elif name == "bolt":
        pts = [(cx + span * 0.05, y0 + span * 0.05), (x0 + span * 0.22, cy + span * 0.04), (cx + span * 0.02, cy + span * 0.04), (cx - span * 0.06, y1 - span * 0.05), (x1 - span * 0.20, cy - span * 0.04), (cx - span * 0.02, cy - span * 0.04)]
        draw.polygon(pts, fill=fg)

    elif name == "clock":
        draw.ellipse([x0 + span * 0.06, y0 + span * 0.06, x1 - span * 0.06, y1 - span * 0.06], outline=fg, width=lw)
        draw.line([(cx, cy), (cx, y0 + span * 0.24)], fill=fg, width=lw)
        draw.line([(cx, cy), (cx + span * 0.22, cy + span * 0.1)], fill=fg, width=lw)

    elif name == "calendar":
        draw.rounded_rectangle([x0 + span * 0.08, y0 + span * 0.16, x1 - span * 0.08, y1 - span * 0.08], radius=int(span * 0.12), outline=fg, width=lw)
        draw.line([(x0 + span * 0.08, y0 + span * 0.36), (x1 - span * 0.08, y0 + span * 0.36)], fill=fg, width=max(2, lw - 1))
        draw.line([(x0 + span * 0.3, y0 + span * 0.08), (x0 + span * 0.3, y0 + span * 0.24)], fill=fg, width=lw)
        draw.line([(x1 - span * 0.3, y0 + span * 0.08), (x1 - span * 0.3, y0 + span * 0.24)], fill=fg, width=lw)

    elif name == "trophy":
        draw.rounded_rectangle([x0 + span * 0.22, y0 + span * 0.10, x1 - span * 0.22, cy + span * 0.16], radius=int(span * 0.18), fill=fg)
        draw.arc([x0 + span * 0.06, y0 + span * 0.16, x0 + span * 0.28, cy + span * 0.06], start=90, end=270, fill=fg, width=lw)
        draw.arc([x1 - span * 0.28, y0 + span * 0.16, x1 - span * 0.06, cy + span * 0.06], start=270, end=90, fill=fg, width=lw)
        draw.line([(cx, cy + span * 0.14), (cx, y1 - span * 0.16)], fill=fg, width=lw)
        draw.line([(cx - span * 0.22, y1 - span * 0.14), (cx + span * 0.22, y1 - span * 0.14)], fill=fg, width=lw)

    return img.resize((size, size), Image.Resampling.LANCZOS)


def render_vector_icon(
    name: str,
    size: int = 20,
    color: str = "#FFFFFF",
    bg_circle: Optional[str] = None,
) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(_render_vector_icon_pil(name, size, color, bg_circle))


@lru_cache(maxsize=8)
def _render_banner_illustration_pil(width: int = 210, height: int = 110) -> Image.Image:
    """Render the Invoice + Calculator + Potted Plant banner illustration at 3x resolution."""
    scale = 3
    w, h = width * scale, height * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Soft ground shadow
    draw.ellipse([int(w * 0.12), int(h * 0.80), int(w * 0.94), int(h * 0.95)], fill=(120, 112, 215, 70))

    # Invoice paper (slightly tilted effect via rotated layer)
    paper = Image.new("RGBA", (int(w * 0.44), int(h * 0.86)), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(paper)
    pw, ph = paper.size
    pdraw.rounded_rectangle([4, 4, pw - 5, ph - 5], radius=18, fill=(255, 255, 255, 250), outline=(218, 222, 245, 255), width=3)
    pdraw.text((int(pw * 0.14), int(ph * 0.11)), "INVOICE", fill=(30, 38, 82, 255))
    for i, frac in enumerate([0.33, 0.45, 0.57, 0.69]):
        line_w = 0.74 if i % 2 == 0 else 0.56
        pdraw.rounded_rectangle(
            [int(pw * 0.14), int(ph * frac), int(pw * (0.14 + line_w)), int(ph * frac) + 10],
            radius=5,
            fill=(198, 204, 236, 255),
        )
    rot_paper = paper.rotate(9, resample=Image.Resampling.BICUBIC, expand=True)
    img.paste(rot_paper, (int(w * 0.16), int(h * 0.04)), rot_paper)

    # Purple Calculator
    calc = Image.new("RGBA", (int(w * 0.25), int(h * 0.52)), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(calc)
    cw, ch = calc.size
    cdraw.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=16, fill=(76, 67, 198, 255))
    cdraw.rounded_rectangle([12, 12, cw - 13, int(ch * 0.30)], radius=8, fill=(224, 229, 255, 255))
    bx0, by0 = 14, int(ch * 0.38)
    bw = (cw - 28 - 12) // 3
    bh = (ch - by0 - 16 - 12) // 3
    for row in range(3):
        for col in range(3):
            x = bx0 + col * (bw + 6)
            y = by0 + row * (bh + 6)
            bcol = (130, 124, 242, 255) if (row == 2 and col == 2) else (167, 163, 250, 235)
            cdraw.rounded_rectangle([x, y, x + bw, y + bh], radius=5, fill=bcol)
    rot_calc = calc.rotate(-7, resample=Image.Resampling.BICUBIC, expand=True)
    img.paste(rot_calc, (int(w * 0.48), int(h * 0.32)), rot_calc)

    # Potted plant
    pot_x0, pot_y0 = int(w * 0.74), int(h * 0.62)
    pot_x1, pot_y1 = int(w * 0.89), int(h * 0.86)
    draw.polygon([(pot_x0, pot_y0), (pot_x1, pot_y0), (pot_x1 - 12, pot_y1), (pot_x0 + 12, pot_y1)], fill=(235, 238, 252, 255))
    draw.rounded_rectangle([pot_x0 - 4, pot_y0 - 6, pot_x1 + 4, pot_y0 + 10], radius=6, fill=(215, 220, 245, 255))
    stem_x = (pot_x0 + pot_x1) // 2
    draw.line([(stem_x, pot_y0), (stem_x, int(h * 0.24))], fill=(34, 150, 68, 255), width=6)
    draw.pieslice([stem_x - 58, int(h * 0.26), stem_x + 4, int(h * 0.56)], start=175, end=345, fill=(34, 177, 76, 255))
    draw.pieslice([stem_x - 4, int(h * 0.22), stem_x + 62, int(h * 0.52)], start=195, end=365, fill=(52, 211, 102, 255))
    draw.pieslice([stem_x - 24, int(h * 0.14), stem_x + 28, int(h * 0.44)], start=210, end=330, fill=(22, 163, 74, 255))

    return img.resize((width, height), Image.Resampling.LANCZOS)


def render_banner_illustration(width: int = 210, height: int = 110) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(_render_banner_illustration_pil(width, height))


@lru_cache(maxsize=4)
def _render_growth_chart_graphic_pil(width: int = 92, height: int = 64) -> Image.Image:
    """Render translucent ascending bars + upward curved arrow for the growth promo card."""
    scale = 3
    w, h = width * scale, height * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bar_w = int(w * 0.13)
    gap = int(w * 0.06)
    heights = [0.24, 0.38, 0.54, 0.72]
    x = int(w * 0.12)
    for frac in heights:
        y0 = int(h * (1.0 - frac))
        draw.rounded_rectangle([x, y0, x + bar_w, h - 4], radius=6, fill=(255, 255, 255, 78))
        x += bar_w + gap

    # Curved upward arrow
    pts = [
        (int(w * 0.14), int(h * 0.64)),
        (int(w * 0.42), int(h * 0.48)),
        (int(w * 0.68), int(h * 0.28)),
        (int(w * 0.88), int(h * 0.10)),
    ]
    draw.line(pts, fill=(255, 255, 255, 220), width=7, joint="curve")
    draw.line([(int(w * 0.74), int(h * 0.11)), (int(w * 0.89), int(h * 0.09)), (int(w * 0.87), int(h * 0.24))], fill=(255, 255, 255, 220), width=7)

    return img.resize((width, height), Image.Resampling.LANCZOS)


def render_growth_chart_graphic(width: int = 92, height: int = 64) -> ImageTk.PhotoImage:
    return ImageTk.PhotoImage(_render_growth_chart_graphic_pil(width, height))


class RoundedCard(tk.Canvas):
    """
    Reusable responsive card container with anti-aliased rounded corners,
    optional gradient, subtle drop shadow, and pastel corner wave accent.
    Children should be placed inside `self.body`.
    """

    def __init__(
        self,
        master: tk.Misc,
        parent_bg: str,
        fill: str = "#FFFFFF",
        gradient_end: Optional[str] = None,
        border_color: Optional[str] = None,
        shadow_color: Optional[str] = None,
        corner_wave_color: Optional[str] = None,
        radius: int = 14,
        pad_x: int = 14,
        pad_y: int = 12,
        **kwargs,
    ):
        super().__init__(
            master,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.parent_bg = parent_bg
        self.fill = fill
        self.gradient_end = gradient_end
        self.border_color = border_color
        self.shadow_color = shadow_color
        self.corner_wave_color = corner_wave_color
        self.radius = radius
        self.pad_x = pad_x
        self.pad_y = pad_y

        self._bg_photo: Optional[ImageTk.PhotoImage] = None
        self._last_size: Tuple[int, int] = (0, 0)
        self._bg_item: Optional[int] = None

        body_bg = fill if not gradient_end else fill
        self.body = tk.Frame(self, bg=body_bg, bd=0, highlightthickness=0)
        self._body_window = self.create_window(
            pad_x,
            pad_y,
            anchor="nw",
            window=self.body,
        )
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event: tk.Event) -> None:
        w, h = event.width, event.height
        if w < 12 or h < 12:
            return
        if (w, h) == self._last_size:
            return
        self._last_size = (w, h)

        self._bg_photo = create_rounded_rect_image(
            width=w,
            height=h,
            radius=self.radius,
            fill=self.fill,
            border_color=self.border_color,
            border_width=1 if self.border_color else 0,
            bg_color=self.parent_bg,
            shadow_color=self.shadow_color,
            gradient_end=self.gradient_end,
            corner_wave_color=self.corner_wave_color,
        )
        if self._bg_item is None:
            self._bg_item = self.create_image(0, 0, image=self._bg_photo, anchor="nw")
        else:
            self.itemconfigure(self._bg_item, image=self._bg_photo)
        self.tag_lower(self._bg_item)

        inner_w = max(1, w - 2 * self.pad_x)
        inner_h = max(1, h - 2 * self.pad_y)
        self.coords(self._body_window, self.pad_x, self.pad_y)
        self.itemconfigure(self._body_window, width=inner_w, height=inner_h)
