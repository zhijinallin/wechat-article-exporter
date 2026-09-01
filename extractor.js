/**
 * Runs inside the active page through chrome.scripting.executeScript.
 * Keep this function self-contained: Chrome serializes it before injection.
 */
export function extractWechatArticle() {
  const normalizeInlineText = (value) =>
    String(value ?? "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t\r\n]+/g, " ")
      .trim();

  const normalizeMultilineText = (value) =>
    String(value ?? "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n[ \t]+/g, "\n")
      .replace(/[ \t]{2,}/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .trim();

  const firstText = (selectors) => {
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      const text = normalizeInlineText(element?.textContent);
      if (text) return text;
    }
    return "";
  };

  const firstMeta = (selectors) => {
    for (const selector of selectors) {
      const value = normalizeInlineText(
        document.querySelector(selector)?.getAttribute("content"),
      );
      if (value) return value;
    }
    return "";
  };

  const normalizeUrl = (value, { allowDataImage = false } = {}) => {
    const raw = String(value ?? "").trim();
    if (!raw) return "";
    if (allowDataImage && /^data:image\//i.test(raw)) return raw;

    try {
      const url = new URL(raw, window.location.href);
      if (url.protocol === "http:") url.protocol = "https:";
      if (url.protocol !== "https:") return "";
      return url.href;
    } catch {
      return "";
    }
  };

  const title =
    firstMeta(['meta[property="og:title"]', 'meta[name="twitter:title"]']) ||
    firstText(["#activity-name", ".rich_media_title", "h1"]) ||
    normalizeInlineText(document.title);

  const author = firstText([
    "#js_name",
    ".rich_media_meta_nickname",
    ".wx_follow_nickname",
    "[data-role='profile-nickname']",
  ]);

  const publishTime =
    firstText(["#publish_time", ".rich_media_meta_text"]) ||
    firstMeta([
      'meta[property="article:published_time"]',
      'meta[name="article:published_time"]',
    ]);

  const description = firstMeta([
    'meta[property="og:description"]',
    'meta[name="description"]',
  ]);

  const content = document.querySelector(
    "#js_content, .rich_media_content, article",
  );

  if (!content) {
    return {
      ok: false,
      error:
        "未识别到微信公众号正文。请确认当前标签页是可正常阅读的 mp.weixin.qq.com/s/ 文章。",
    };
  }

  const clone = content.cloneNode(true);
  const sourceImages = Array.from(content.querySelectorAll("img"));
  const clonedImages = Array.from(clone.querySelectorAll("img"));

  clone
    .querySelectorAll(
      "script, style, link, meta, base, template, object, embed, canvas, form, input, textarea, select, button",
    )
    .forEach((element) => element.remove());

  clone
    .querySelectorAll("iframe, video, audio")
    .forEach((element) => {
      const source = normalizeUrl(
        element.getAttribute("data-src") ||
          element.getAttribute("src") ||
          element.querySelector("source")?.getAttribute("src"),
      );
      const placeholder = document.createElement("p");
      placeholder.textContent = source
        ? `［原文包含未导出的视频或音频：${source}］`
        : "［原文包含未导出的视频或音频］";
      element.replaceWith(placeholder);
    });

  clone
    .querySelectorAll(
      ".js_ad_link, .rich_media_tool, .rich_media_extra, [data-role='advertisement']",
    )
    .forEach((element) => element.remove());

  const imageRefs = [];

  clonedImages.forEach((clonedImage, index) => {
    if (!clone.contains(clonedImage)) return;

    const sourceImage = sourceImages[index];
    const source = normalizeUrl(
      sourceImage?.getAttribute("data-src") ||
        sourceImage?.currentSrc ||
        sourceImage?.getAttribute("src") ||
        clonedImage.getAttribute("data-src") ||
        clonedImage.getAttribute("src"),
      { allowDataImage: true },
    );

    clonedImage.removeAttribute("srcset");
    clonedImage.removeAttribute("data-src");
    clonedImage.removeAttribute("data-backsrc");
    clonedImage.removeAttribute("data-original");
    clonedImage.setAttribute("loading", "lazy");
    clonedImage.setAttribute(
      "alt",
      normalizeInlineText(
        sourceImage?.getAttribute("alt") || clonedImage.getAttribute("alt"),
      ),
    );

    if (!source) {
      clonedImage.removeAttribute("src");
      return;
    }

    clonedImage.setAttribute("src", source);
    if (/^data:image\//i.test(source)) return;

    const id = `wx-image-${index}`;
    clonedImage.setAttribute("data-wx-export-id", id);
    imageRefs.push({
      id,
      src: source,
      alt: clonedImage.getAttribute("alt") || "",
    });
  });

  clone.querySelectorAll("a").forEach((anchor) => {
    const href = normalizeUrl(anchor.getAttribute("href"));
    if (!href) {
      anchor.removeAttribute("href");
      anchor.removeAttribute("target");
      anchor.removeAttribute("rel");
      return;
    }
    anchor.setAttribute("href", href);
    anchor.setAttribute("target", "_blank");
    anchor.setAttribute("rel", "noopener noreferrer");
  });

  clone.querySelectorAll("*").forEach((element) => {
    for (const attribute of Array.from(element.attributes)) {
      const name = attribute.name.toLowerCase();
      if (
        name.startsWith("on") ||
        [
          "srcdoc",
          "nonce",
          "integrity",
          "crossorigin",
          "contenteditable",
          "formaction",
          "action",
          "xlink:href",
        ].includes(name)
      ) {
        element.removeAttribute(attribute.name);
        continue;
      }

      if (name.startsWith("data-") && name !== "data-wx-export-id") {
        element.removeAttribute(attribute.name);
        continue;
      }

      if (name === "style") {
        const safeStyle = attribute.value
          .replace(/url\s*\([^)]*\)/gi, "")
          .replace(/expression\s*\([^)]*\)/gi, "")
          .replace(/@import[^;]+;?/gi, "")
          .trim();
        if (safeStyle) element.setAttribute("style", safeStyle);
        else element.removeAttribute("style");
      }
    }
  });

  const contentText = normalizeMultilineText(content.innerText);
  if (contentText.length < 20 && imageRefs.length === 0) {
    return {
      ok: false,
      error:
        "页面存在正文容器，但没有可导出的正文。文章可能已失效、需要验证或尚未加载完成。",
    };
  }

  const canonicalUrl =
    normalizeUrl(
      document.querySelector('link[rel="canonical"]')?.getAttribute("href"),
    ) ||
    normalizeUrl(firstMeta(['meta[property="og:url"]'])) ||
    normalizeUrl(window.location.href);

  return {
    ok: true,
    article: {
      title: title || "未命名微信文章",
      author,
      publishTime,
      description,
      canonicalUrl,
      sourceHost: window.location.hostname,
      language: document.documentElement.lang || "zh-CN",
      extractedAt: new Date().toISOString(),
      contentHtml: clone.innerHTML,
      contentText,
      imageRefs,
    },
  };
}
