#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:8766", help="本地测试服务器地址"
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    output_dir = ROOT / "output" / "playwright"
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        page.goto(f"{base_url}/test/harness.html", wait_until="networkidle")
        page.locator("#status").filter(has_text="已识别正文").wait_for()
        require(not page.locator("#export-html").is_disabled(), "HTML 按钮没有启用")

        page.locator("#export-html").click()
        page.locator("#status").filter(has_text="HTML 已生成").wait_for()
        html_name = page.locator("html").get_attribute("data-last-download") or ""
        html_text = page.locator("html").get_attribute("data-last-blob-text") or ""
        require(html_name.endswith(".html"), "HTML 下载文件名不正确")
        require("data:image/svg+xml;base64," in html_text, "测试图片没有嵌入 HTML")
        require("正文未上传到任何服务" in html_text, "HTML 缺少本地处理说明")

        page.locator("#download-markdown").click()
        page.locator("#status").filter(has_text="Markdown 已下载").wait_for()
        markdown_name = page.locator("html").get_attribute("data-last-download") or ""
        markdown_text = page.locator("html").get_attribute("data-last-blob-text") or ""
        require(markdown_name.endswith(".md"), "Markdown 下载文件名不正确")
        require("# 微信文章导出器端到端测试" in markdown_text, "Markdown 缺少标题")
        require("**规划、执行、检查、修订**" in markdown_text, "Markdown 粗体转换失败")

        page.locator("#copy-markdown").click()
        page.locator("#status").filter(has_text="已复制到剪贴板").wait_for()
        copied = page.locator("html").get_attribute("data-copied-markdown") or ""
        require(copied == markdown_text, "复制内容和下载内容不一致")

        page.screenshot(path=output_dir / "local-smoke.png", full_page=True)

        invalid = browser.new_page()
        invalid.goto(f"{base_url}/test/harness.html?mode=invalid", wait_until="networkidle")
        invalid.locator("#status").filter(has_text="当前页面不是微信公众号文章").wait_for()
        require(invalid.locator("#export-html").is_disabled(), "错误页面仍允许导出")

        legacy = browser.new_page()
        legacy.goto(f"{base_url}/test/harness.html?mode=legacy", wait_until="networkidle")
        legacy.locator("#status").filter(has_text="已识别正文").wait_for()

        browser.close()

    print("浏览器冒烟测试通过：HTML、Markdown、复制、错误页面和旧式微信链接均符合预期。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
