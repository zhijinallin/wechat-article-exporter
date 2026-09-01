#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "store-assets"
ICONS = ROOT / "icons"
REFERENCE = ASSETS / "popup-reference.png"
FONT_REGULAR = Path("/System/Library/Fonts/STHeiti Light.ttc")
FONT_BOLD = Path("/System/Library/Fonts/STHeiti Medium.ttc")
GREEN = "#087f5b"
INK = "#172033"
MUTED = "#697386"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(str(path), size=size)


def rounded_icon(size: int) -> Image.Image:
    scale = 4
    canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    inset = max(1, int(size * 0.04)) * scale
    draw.rounded_rectangle(
        (inset, inset, size * scale - inset, size * scale - inset),
        radius=int(size * 0.24) * scale,
        fill=GREEN,
    )
    text_font = font(int(size * 0.58) * scale, bold=True)
    box = draw.textbbox((0, 0), "文", font=text_font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    x = (size * scale - width) / 2
    y = (size * scale - height) / 2 - box[1] - size * scale * 0.015
    draw.text((x, y), "文", font=text_font, fill="white")
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def create_icons() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 48, 128):
        rounded_icon(size).save(ICONS / f"icon-{size}.png")
    rounded_icon(128).save(ASSETS / "store-icon-128.png")


def add_shadow(base: Image.Image, box: tuple[int, int, int, int], radius: int = 26) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(box, radius=radius, fill=(23, 32, 51, 42))
    layer = layer.filter(ImageFilter.GaussianBlur(18))
    base.alpha_composite(layer)


def create_screenshot() -> None:
    reference = Image.open(REFERENCE).convert("RGB")
    popup = reference.crop(
        (
            12,
            8,
            max(13, reference.width - 12),
            max(9, reference.height - 14),
        )
    )
    popup.thumbnail((625, 660), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (1280, 800), "#eef5f2")
    draw = ImageDraw.Draw(canvas)

    logo = rounded_icon(80)
    canvas.alpha_composite(logo, (72, 72))
    draw.text((174, 81), "微信文章本地导出器", font=font(31, True), fill=INK)
    draw.text((174, 124), "文章只在本机处理", font=font(21), fill=GREEN)

    draw.text((72, 218), "一键保存", font=font(58, True), fill=INK)
    draw.text((72, 286), "微信公众号文章", font=font(58, True), fill=INK)
    draw.text((76, 382), "完整 HTML  ·  Markdown  ·  复制到剪贴板", font=font(23), fill=MUTED)

    features = ["尽量保留正文图片", "方便交给 AI 和知识库", "不上传文章内容"]
    y = 465
    for item in features:
        draw.ellipse((78, y + 7, 94, y + 23), fill=GREEN)
        draw.text((112, y), item, font=font(24), fill=INK)
        y += 62

    draw.text((76, 716), "非微信官方产品", font=font(17), fill=MUTED)

    frame_x = 616
    frame_y = 50
    frame_w = popup.width + 28
    frame_h = popup.height + 28
    add_shadow(canvas, (frame_x, frame_y, frame_x + frame_w, frame_y + frame_h))
    draw.rounded_rectangle(
        (frame_x, frame_y, frame_x + frame_w, frame_y + frame_h),
        radius=24,
        fill="white",
        outline="#dce5e1",
        width=2,
    )
    canvas.alpha_composite(popup.convert("RGBA"), (frame_x + 14, frame_y + 14))
    canvas.convert("RGB").save(ASSETS / "screenshot-1280x800.png", quality=95)


def create_promo() -> None:
    canvas = Image.new("RGBA", (440, 280), "#eef5f2")
    draw = ImageDraw.Draw(canvas)
    canvas.alpha_composite(rounded_icon(72), (32, 34))
    draw.text((124, 41), "微信文章", font=font(32, True), fill=INK)
    draw.text((124, 79), "本地导出器", font=font(32, True), fill=INK)
    draw.rounded_rectangle((32, 142, 408, 230), radius=18, fill="white")
    draw.text((56, 158), "完整 HTML  ·  Markdown", font=font(23, True), fill=GREEN)
    draw.text((56, 194), "只在本机处理，不上传文章", font=font(18), fill=MUTED)
    draw.text((32, 251), "非微信官方产品", font=font(13), fill=MUTED)
    canvas.convert("RGB").save(ASSETS / "promo-440x280.png", quality=95)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    create_icons()
    create_screenshot()
    create_promo()
    print("已生成扩展图标和 Chrome 商店图片。")


if __name__ == "__main__":
    main()
