#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RUNTIME_FILES = {
    "manifest.json",
    "popup.html",
    "popup.css",
    "popup.js",
    "extractor.js",
    "icons/icon-16.png",
    "icons/icon-32.png",
    "icons/icon-48.png",
    "icons/icon-128.png",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"不是有效 PNG：{path.relative_to(ROOT)}")
    return struct.unpack(">II", data[16:24])


def png_color_type(path: Path) -> int:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 26:
        fail(f"不是有效 PNG：{path.relative_to(ROOT)}")
    return data[25]


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def verify_markdown_links() -> None:
    markdown_files = [
        ROOT / "README.md",
        ROOT / "PRIVACY.md",
        ROOT / "CHANGELOG.md",
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "store-assets").rglob("*.md")),
    ]
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")

    for path in markdown_files:
        if not path.is_file():
            fail(f"缺少文档：{path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            target = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_target = unquote(target.split("#", 1)[0])
            resolved = (path.parent / relative_target).resolve()
            if not resolved.exists():
                fail(
                    f"文档链接失效：{path.relative_to(ROOT)} -> {target}"
                )


def verify_source() -> str:
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("manifest_version") != 3:
        fail("manifest_version 必须为 3")
    version = str(manifest.get("version", ""))
    if not re.fullmatch(r"\d+(?:\.\d+){0,3}", version):
        fail("manifest.json 版本号格式不正确")
    if set(manifest.get("permissions", [])) != {"activeTab", "scripting"}:
        fail("权限与批准的最小权限集合不一致")
    if set(manifest.get("host_permissions", [])) != {
        "https://mmbiz.qpic.cn/*",
        "https://mmbiz.qlogo.cn/*",
    }:
        fail("图片域名权限发生了未审核的变化")

    for relative in RUNTIME_FILES:
        if not (ROOT / relative).is_file():
            fail(f"缺少运行文件：{relative}")

    for size in (16, 32, 48, 128):
        actual = png_size(ROOT / f"icons/icon-{size}.png")
        if actual != (size, size):
            fail(f"icon-{size}.png 尺寸错误：{actual}")

    # PNG color type 6 = RGBA; type 2 = 24-bit RGB without transparency.
    store_assets = {
        "store-assets/store-icon-128.png": ((128, 128), 6),
        "store-assets/screenshot-1280x800.png": ((1280, 800), 2),
        "store-assets/promo-440x280.png": ((440, 280), 2),
        "store-assets/marquee-1400x560.png": ((1400, 560), 2),
        "store-assets/upload-ready/01-store-icon-128x128.png": ((128, 128), 6),
        "store-assets/upload-ready/02-screenshot-1280x800.png": ((1280, 800), 2),
        "store-assets/upload-ready/03-small-promo-440x280.png": ((440, 280), 2),
        "store-assets/upload-ready/04-marquee-1400x560-optional.png": ((1400, 560), 2),
    }
    for relative, (expected_size, expected_color_type) in store_assets.items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"缺少商店素材：{relative}")
        actual = png_size(path)
        if actual != expected_size:
            fail(f"商店素材尺寸错误：{relative} = {actual}")
        actual_color_type = png_color_type(path)
        if actual_color_type != expected_color_type:
            fail(f"商店素材颜色格式错误：{relative} = PNG color type {actual_color_type}")

    forbidden = []
    for path in ROOT.rglob("*"):
        if any(
            part in {".git", "dist", "output", "private-evidence"}
            for part in path.parts
        ):
            continue
        if path.is_file() and path.suffix.lower() in {".pem", ".key"}:
            forbidden.append(str(path.relative_to(ROOT)))
    if forbidden:
        fail(f"项目中发现私钥文件：{', '.join(forbidden)}")

    verify_markdown_links()

    return version


def verify_archives(version: str) -> None:
    friend_zip = DIST / f"wechat-article-exporter-v{version}-friends-unpacked.zip"
    store_zip = DIST / f"wechat-article-exporter-v{version}-chrome-web-store.zip"

    if not friend_zip.is_file() or not store_zip.is_file():
        fail("缺少朋友版或 Chrome 商店版 ZIP")

    with zipfile.ZipFile(store_zip) as archive:
        names = {name.rstrip("/") for name in archive.namelist() if not name.endswith("/")}
        if "manifest.json" not in names:
            fail("商店 ZIP 的最外层没有 manifest.json")
        if not RUNTIME_FILES.issubset(names):
            fail("商店 ZIP 缺少运行文件")
        if any(name.startswith(("docs/", "test/", "scripts/", ".github/")) for name in names):
            fail("商店 ZIP 含有不应发布的开发文件")
        if any(name.endswith((".pem", ".key")) for name in names):
            fail("商店 ZIP 含有私钥")

    root_name = f"wechat-article-exporter-v{version}"
    with zipfile.ZipFile(friend_zip) as archive:
        names = {name.rstrip("/") for name in archive.namelist() if not name.endswith("/")}
        if f"{root_name}/manifest.json" not in names:
            fail("朋友版 ZIP 的插件目录不正确")
        if f"{root_name}/README-INSTALL.md" not in names:
            fail("朋友版 ZIP 缺少安装指南")
        if f"{root_name}/store-assets/screenshot-1280x800.png" not in names:
            fail("朋友版 ZIP 缺少真实插件截图")

    checksum_path = DIST / "SHA256SUMS.txt"
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    expected = {path.name: sha256(path) for path in (store_zip, friend_zip)}
    actual = {}
    for line in lines:
        digest, filename = line.split(maxsplit=1)
        actual[filename.strip()] = digest
    if actual != expected:
        fail("SHA256SUMS.txt 与发行 ZIP 不一致")


def main() -> int:
    try:
        version = verify_source()
        verify_archives(version)
    except (AssertionError, OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"验证失败：{error}", file=sys.stderr)
        return 1

    print(f"验证通过：v{version} 的源代码、两个发行包和校验值一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
