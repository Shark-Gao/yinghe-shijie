from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(r"G:\workspace\yinghe-shijie")
COVERS_DIR = ROOT / "covers"
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")


@dataclass(frozen=True)
class CoverSpec:
    slug: str
    topic: str
    source_image: Path
    title_lines: Sequence[str]
    subtitle: str
    accent: tuple[int, int, int]


SPECS = [
    CoverSpec(
        slug="computer-cache-memory-storage",
        topic="computer-memory-hierarchy",
        source_image=Path(
            r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f4eb0-f361-7ce1-a1c3-b58731c4cd1f\call_EaCFNSY8Xr27YpISV5qM6Ufb.png"
        ),
        title_lines=("缓存 内存", "硬盘谁最慢"),
        subtitle="一眼看懂算力分层",
        accent=(255, 188, 66),
    ),
    CoverSpec(
        slug="how-a-world-war-two-submarine-works",
        topic="ww2-submarine-cutaway",
        source_image=Path(
            r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f4eb0-f361-7ce1-a1c3-b58731c4cd1f\call_ces4fIhrn0Y18ovUA6Mhk0Ei.png"
        ),
        title_lines=("二战潜艇", "靠什么潜航"),
        subtitle="剖面看懂深海杀器",
        accent=(88, 220, 220),
    ),
    CoverSpec(
        slug="how-inland-waterways-work",
        topic="inland-waterway-logistics",
        source_image=Path(
            r"C:\Users\sharkgao.SHARKGAO-PC2\.codex\generated_images\019f4eb0-f361-7ce1-a1c3-b58731c4cd1f\call_xUrk9yNdK1zZnAgwZlMrtKVa.png"
        ),
        title_lines=("内河航运", "为什么便宜"),
        subtitle="低成本运输的底层网络",
        accent=(73, 171, 255),
    ),
]


def fit_crop(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = image.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = max(0, min((src_w - new_w) // 3, src_w - new_w))
        box = (left, 0, left + new_w, src_h)
    else:
        new_h = int(src_w / target_ratio)
        top = max(0, (src_h - new_h) // 2)
        box = (0, top, src_w, top + new_h)
    return image.crop(box).resize(size, Image.Resampling.LANCZOS)


def draw_cover(base: Image.Image, size: tuple[int, int], title_lines: Sequence[str], subtitle: str, accent: tuple[int, int, int]) -> Image.Image:
    image = fit_crop(base, size).convert("RGBA")
    w, h = image.size

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    panel = Image.new("RGBA", image.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)

    panel_left = int(w * 0.5)
    panel_draw.rounded_rectangle(
        [(panel_left, int(h * 0.05)), (w - int(w * 0.03), h - int(h * 0.05))],
        radius=int(min(w, h) * 0.03),
        fill=(4, 10, 20, 188),
    )
    panel = panel.filter(ImageFilter.GaussianBlur(radius=2))
    overlay.alpha_composite(panel)

    draw = ImageDraw.Draw(overlay)
    title_font = ImageFont.truetype(str(FONT_BOLD), size=int(h * 0.1))
    subtitle_font = ImageFont.truetype(str(FONT_BOLD), size=int(h * 0.05))
    ghost_font = ImageFont.truetype(str(FONT_BOLD), size=int(h * 0.16))

    ghost_text = "HARDCORE"
    ghost_pos = (panel_left + int(w * 0.02), int(h * 0.06))
    draw.text(ghost_pos, ghost_text, font=ghost_font, fill=(255, 255, 255, 28))

    x = panel_left + int(w * 0.035)
    y = int(h * 0.25)
    stroke = max(3, int(h * 0.006))
    for line in title_lines:
        draw.text(
            (x, y),
            line,
            font=title_font,
            fill=(255, 244, 222, 255),
            stroke_width=stroke,
            stroke_fill=(0, 0, 0, 230),
        )
        y += title_font.size + int(h * 0.012)

    accent_y = y + int(h * 0.01)
    draw.rounded_rectangle(
        [(x, accent_y), (x + int(w * 0.19), accent_y + int(h * 0.012))],
        radius=int(h * 0.006),
        fill=accent + (255,),
    )

    sub_y = accent_y + int(h * 0.06)
    draw.text(
        (x, sub_y),
        subtitle,
        font=subtitle_font,
        fill=(255, 255, 255, 255),
        stroke_width=max(2, stroke - 1),
        stroke_fill=(0, 0, 0, 220),
    )

    return Image.alpha_composite(image, overlay).convert("RGB")


def save_outputs(spec: CoverSpec) -> None:
    out_dir = COVERS_DIR / spec.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    base = Image.open(spec.source_image)
    base_out = out_dir / f"base-{spec.topic}.png"
    base.save(base_out)

    outputs = {
        out_dir / f"{spec.slug}-cover-4x3.png": (1146, 860),
        out_dir / f"{spec.slug}-cover-16x9.png": (1920, 1080),
    }
    for path, size in outputs.items():
        final = draw_cover(base, size, spec.title_lines, spec.subtitle, spec.accent)
        final.save(path, quality=95)


def main() -> None:
    for spec in SPECS:
        save_outputs(spec)


if __name__ == "__main__":
    main()
