#!/usr/bin/env python3
from __future__ import annotations

import shutil
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


def extension_icon(size: int) -> Image.Image:
    """Preserve the icons already shipped inside the v0.1.0 extension ZIP."""
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


def rounded_icon(size: int) -> Image.Image:
    scale = 4
    canvas = Image.new("RGB", (size * scale, size * scale), GREEN)
    draw = ImageDraw.Draw(canvas)
    alpha = Image.new("L", canvas.size, 0)
    alpha_draw = ImageDraw.Draw(alpha)
    inset = max(1, int(size * 0.04)) * scale
    alpha_draw.rounded_rectangle(
        (inset, inset, size * scale - inset, size * scale - inset),
        radius=int(size * 0.24) * scale,
        fill=255,
    )
    text_font = font(int(size * 0.58) * scale, bold=True)
    box = draw.textbbox((0, 0), "文", font=text_font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    x = (size * scale - width) / 2
    y = (size * scale - height) / 2 - box[1] - size * scale * 0.015
    draw.text((x, y), "文", font=text_font, fill="white")
    resized = canvas.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    resized.putalpha(alpha.resize((size, size), Image.Resampling.LANCZOS))
    return resized


def create_icons() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 48, 128):
        extension_icon(size).save(ICONS / f"icon-{size}.png")

    store_icon = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    store_icon.alpha_composite(rounded_icon(96), (16, 16))
    store_icon.save(ASSETS / "store-icon-128.png")


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
    canvas = Image.new("RGBA", (440, 280), GREEN)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((315, -110, 505, 80), fill="#0ca678")
    draw.rounded_rectangle((26, 26, 114, 114), radius=20, fill="white")
    canvas.alpha_composite(rounded_icon(64), (38, 38))
    draw.text((134, 28), "微信文章", font=font(31, True), fill="white")
    draw.text((134, 67), "本地导出器", font=font(31, True), fill="white")
    draw.rounded_rectangle((26, 139, 414, 231), radius=19, fill="white")
    draw.text((50, 154), "完整 HTML  ·  Markdown", font=font(23, True), fill=GREEN)
    draw.text((50, 193), "只在本机处理，不上传文章", font=font(18), fill="#076a4c")
    draw.text((26, 253), "非微信官方产品", font=font(13), fill="#b7ebd5")
    canvas.convert("RGB").save(ASSETS / "promo-440x280.png", quality=95)


def create_marquee() -> None:
    canvas = Image.new("RGBA", (1400, 560), GREEN)
    draw = ImageDraw.Draw(canvas)

    draw.ellipse((1040, -270, 1580, 270), fill="#0ca678")
    draw.ellipse((1120, 320, 1500, 700), fill="#076a4c")
    draw.rounded_rectangle((74, 74, 286, 286), radius=44, fill="white")
    canvas.alpha_composite(rounded_icon(154), (103, 103))

    draw.text((350, 92), "微信文章本地导出器", font=font(58, True), fill="white")
    draw.text((350, 183), "一键保存完整 HTML 与 Markdown", font=font(38), fill="#dff7eb")

    draw.rounded_rectangle((350, 300, 1135, 430), radius=28, fill="#ffffff")
    draw.text((390, 325), "保留正文图片  ·  方便 AI 与知识库  ·  本机处理", font=font(30, True), fill=GREEN)
    draw.text((82, 490), "非微信官方产品", font=font(19), fill="#b7ebd5")

    canvas.convert("RGB").save(ASSETS / "marquee-1400x560.png", quality=95)


def create_upload_ready_folder() -> None:
    upload_ready = ASSETS / "upload-ready"
    upload_ready.mkdir(parents=True, exist_ok=True)
    mapping = {
        "store-icon-128.png": "01-store-icon-128x128.png",
        "screenshot-1280x800.png": "02-screenshot-1280x800.png",
        "promo-440x280.png": "03-small-promo-440x280.png",
        "marquee-1400x560.png": "04-marquee-1400x560-optional.png",
    }
    for source_name, target_name in mapping.items():
        shutil.copy2(ASSETS / source_name, upload_ready / target_name)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    create_icons()
    create_screenshot()
    create_promo()
    create_marquee()
    create_upload_ready_folder()
    print("已生成扩展图标、Chrome 商店图片和直接上传文件夹。")


if __name__ == "__main__":
    main()
