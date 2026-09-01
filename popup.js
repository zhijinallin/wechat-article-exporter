import { extractWechatArticle } from "./extractor.js";

const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const MAX_TOTAL_IMAGE_BYTES = 50 * 1024 * 1024;
const IMAGE_HOSTS = new Set(["mmbiz.qpic.cn", "mmbiz.qlogo.cn"]);

const statusElement = document.querySelector("#status");
const articleCard = document.querySelector("#article-card");
const articleTitle = document.querySelector("#article-title");
const articleMeta = document.querySelector("#article-meta");
const exportHtmlButton = document.querySelector("#export-html");
const downloadMarkdownButton = document.querySelector("#download-markdown");
const copyMarkdownButton = document.querySelector("#copy-markdown");

let articlePromise;
let cachedArticle;

function isWechatArticleUrl(url) {
  return (
    url.hostname === "mp.weixin.qq.com" &&
    (url.pathname === "/s" || url.pathname.startsWith("/s/"))
  );
}

function setStatus(message, tone = "") {
  statusElement.textContent = message;
  statusElement.className = `status${tone ? ` ${tone}` : ""}`;
}

function setButtonsEnabled(enabled) {
  exportHtmlButton.disabled = !enabled;
  downloadMarkdownButton.disabled = !enabled;
  copyMarkdownButton.disabled = !enabled;
}

function sanitizeFilename(value) {
  const cleaned = String(value || "微信文章")
    .normalize("NFKC")
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 90);
  return cleaned || "微信文章";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function downloadText(filename, mimeType, content) {
  const blob = new Blob([content], { type: mimeType });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 10_000);
}

async function getArticle() {
  if (cachedArticle) return cachedArticle;
  if (articlePromise) return articlePromise;

  articlePromise = (async () => {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });

    if (!tab?.id || !tab.url) {
      throw new Error("无法读取当前标签页。");
    }

    const url = new URL(tab.url);
    if (!isWechatArticleUrl(url)) {
      throw new Error(
        "当前页面不是微信公众号文章。请先打开 mp.weixin.qq.com/s 链接。",
      );
    }

    const [execution] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractWechatArticle,
    });

    const result = execution?.result;
    if (!result?.ok) {
      throw new Error(result?.error || "微信文章提取失败。");
    }

    cachedArticle = result.article;
    return cachedArticle;
  })();

  try {
    return await articlePromise;
  } finally {
    articlePromise = undefined;
  }
}

function bytesToBase64(bytes) {
  const chunks = [];
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    chunks.push(
      String.fromCharCode(...bytes.subarray(index, index + chunkSize)),
    );
  }
  return btoa(chunks.join(""));
}

async function fetchImageAsDataUrl(source, remainingBytes) {
  let url;
  try {
    url = new URL(source);
  } catch {
    return { status: "skipped", dataUrl: null, bytes: 0 };
  }

  if (!IMAGE_HOSTS.has(url.hostname)) {
    return { status: "skipped", dataUrl: null, bytes: 0 };
  }

  try {
    const response = await fetch(url.href, {
      cache: "force-cache",
      credentials: "omit",
      referrerPolicy: "no-referrer",
    });
    if (!response.ok) {
      return { status: "failed", dataUrl: null, bytes: 0 };
    }

    const blob = await response.blob();
    if (
      blob.size > MAX_IMAGE_BYTES ||
      blob.size > remainingBytes ||
      !blob.type.startsWith("image/")
    ) {
      return { status: "skipped", dataUrl: null, bytes: 0 };
    }

    const bytes = new Uint8Array(await blob.arrayBuffer());
    return {
      status: "embedded",
      dataUrl: `data:${blob.type};base64,${bytesToBase64(bytes)}`,
      bytes: blob.size,
    };
  } catch {
    return { status: "failed", dataUrl: null, bytes: 0 };
  }
}

async function embedArticleImages(article) {
  const documentCopy = new DOMParser().parseFromString(
    `<main id="wx-export-root">${article.contentHtml}</main>`,
    "text/html",
  );
  const root = documentCopy.querySelector("#wx-export-root");
  let embedded = 0;
  let failed = 0;
  let skipped = 0;
  let totalBytes = 0;

  for (let index = 0; index < article.imageRefs.length; index += 1) {
    const imageRef = article.imageRefs[index];
    const image = root.querySelector(
      `[data-wx-export-id="${imageRef.id}"]`,
    );
    if (!image) continue;

    setStatus(
      `正在处理图片 ${index + 1}/${article.imageRefs.length}…`,
    );

    const result = await fetchImageAsDataUrl(
      imageRef.src,
      MAX_TOTAL_IMAGE_BYTES - totalBytes,
    );

    if (result.status === "embedded") {
      image.setAttribute("src", result.dataUrl);
      totalBytes += result.bytes;
      embedded += 1;
    } else if (result.status === "failed") {
      failed += 1;
    } else {
      skipped += 1;
    }

    image.removeAttribute("data-wx-export-id");
  }

  return {
    contentHtml: root.innerHTML,
    embedded,
    failed,
    skipped,
    totalBytes,
  };
}

function buildStandaloneHtml(article, imageResult) {
  const metadata = [
    article.author && `公众号：${article.author}`,
    article.publishTime && `发布时间：${article.publishTime}`,
    article.canonicalUrl && `原文：${article.canonicalUrl}`,
    `导出时间：${new Date(article.extractedAt).toLocaleString("zh-CN")}`,
  ].filter(Boolean);

  return `<!doctype html>
<html lang="${escapeHtml(article.language || "zh-CN")}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: https://mmbiz.qpic.cn https://mmbiz.qlogo.cn; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
  <title>${escapeHtml(article.title)}</title>
  <style>
    :root { color-scheme: light; font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; color: #20242d; background: #f3f5f7; }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px 18px 64px; }
    .document { width: min(860px, 100%); margin: 0 auto; padding: clamp(24px, 5vw, 56px); border: 1px solid #e1e5ea; border-radius: 18px; background: #fff; box-shadow: 0 18px 60px rgb(31 45 61 / 8%); }
    h1 { margin: 0 0 14px; color: #101828; font-size: clamp(26px, 4vw, 40px); line-height: 1.25; }
    .meta { display: grid; gap: 4px; margin-bottom: 36px; padding-bottom: 20px; border-bottom: 1px solid #e8ebef; color: #667085; font-size: 14px; overflow-wrap: anywhere; }
    .content { font-size: 17px; line-height: 1.85; overflow-wrap: anywhere; }
    .content img { display: block; max-width: 100% !important; height: auto !important; margin: 22px auto; }
    .content table { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; }
    .content td, .content th { padding: 8px 10px; border: 1px solid #d8dde5; }
    .content pre { overflow-x: auto; padding: 16px; border-radius: 10px; background: #f5f7fa; white-space: pre-wrap; }
    .content blockquote { margin-inline: 0; padding: 4px 18px; border-left: 4px solid #087f5b; color: #475467; }
    a { color: #087f5b; }
    .export-note { margin-top: 36px; padding-top: 16px; border-top: 1px solid #e8ebef; color: #98a2b3; font-size: 12px; }
  </style>
</head>
<body>
  <article class="document">
    <h1>${escapeHtml(article.title)}</h1>
    <div class="meta">${metadata
      .map((item) => `<span>${escapeHtml(item)}</span>`)
      .join("")}</div>
    <section class="content">${imageResult.contentHtml}</section>
    <p class="export-note">由“微信文章本地导出器”生成。图片内嵌 ${imageResult.embedded} 张；保留远程地址或跳过 ${imageResult.failed + imageResult.skipped} 张。正文未上传到任何服务。</p>
  </article>
</body>
</html>`;
}

function convertHtmlToMarkdown(article) {
  const parsed = new DOMParser().parseFromString(
    `<main id="wx-markdown-root">${article.contentHtml}</main>`,
    "text/html",
  );
  const root = parsed.querySelector("#wx-markdown-root");

  const normalize = (value) =>
    String(value ?? "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t]+/g, " ");

  const renderChildren = (element) =>
    Array.from(element.childNodes)
      .map((child) => renderNode(child))
      .join("");

  const renderList = (element, ordered) =>
    Array.from(element.children)
      .filter((child) => child.tagName.toLowerCase() === "li")
      .map((item, index) => {
        const prefix = ordered ? `${index + 1}. ` : "- ";
        const body = renderChildren(item)
          .trim()
          .replace(/\n+/g, "\n  ");
        return `${prefix}${body}`;
      })
      .join("\n");

  const renderNode = (node) => {
    if (node.nodeType === Node.TEXT_NODE) return normalize(node.textContent);
    if (node.nodeType !== Node.ELEMENT_NODE) return "";

    const element = node;
    const tag = element.tagName.toLowerCase();
    const children = () => renderChildren(element);

    if (/^h[1-6]$/.test(tag)) {
      return `\n\n${"#".repeat(Number(tag[1]))} ${children().trim()}\n\n`;
    }

    switch (tag) {
      case "p":
      case "div":
      case "section":
      case "figure":
      case "figcaption":
        return `\n\n${children().trim()}\n\n`;
      case "br":
        return "\n";
      case "strong":
      case "b":
        return `**${children().trim()}**`;
      case "em":
      case "i":
        return `*${children().trim()}*`;
      case "del":
      case "s":
        return `~~${children().trim()}~~`;
      case "code":
        return `\`${normalize(element.textContent).trim().replace(/`/g, "\\`")}\``;
      case "pre":
        return `\n\n\`\`\`\n${element.textContent.trim()}\n\`\`\`\n\n`;
      case "blockquote":
        return `\n\n${children()
          .trim()
          .split("\n")
          .map((line) => `> ${line}`)
          .join("\n")}\n\n`;
      case "a": {
        const text = children().trim();
        const href = element.getAttribute("href") || "";
        return href ? `[${text || href}](${href})` : text;
      }
      case "img": {
        const alt = normalize(element.getAttribute("alt")).trim();
        const src = element.getAttribute("src") || "";
        return src ? `\n\n![${alt}](${src})\n\n` : "";
      }
      case "ul":
        return `\n\n${renderList(element, false)}\n\n`;
      case "ol":
        return `\n\n${renderList(element, true)}\n\n`;
      case "li":
        return children();
      case "hr":
        return "\n\n---\n\n";
      case "table":
        return `\n\n${element.outerHTML}\n\n`;
      default:
        return children();
    }
  };

  const header = [
    `# ${article.title}`,
    "",
    article.author ? `- 公众号：${article.author}` : "",
    article.publishTime ? `- 发布时间：${article.publishTime}` : "",
    article.canonicalUrl ? `- 原文：${article.canonicalUrl}` : "",
    `- 导出时间：${new Date(article.extractedAt).toLocaleString("zh-CN")}`,
    "",
    "---",
    "",
  ]
    .filter((line, index, lines) => line || lines[index - 1] !== "")
    .join("\n");

  return `${header}${renderChildren(root)}`
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .concat("\n");
}

async function initialize() {
  try {
    const article = await getArticle();
    articleTitle.textContent = article.title;
    articleMeta.textContent = [article.author, article.publishTime]
      .filter(Boolean)
      .join(" · ");
    articleCard.hidden = false;
    setButtonsEnabled(true);
    setStatus(
      `已识别正文：${article.contentText.length.toLocaleString("zh-CN")} 字符，${article.imageRefs.length} 张图片。`,
      "success",
    );
  } catch (error) {
    setButtonsEnabled(false);
    setStatus(error instanceof Error ? error.message : String(error), "error");
  }
}

exportHtmlButton.addEventListener("click", async () => {
  setButtonsEnabled(false);
  try {
    const article = await getArticle();
    const imageResult = await embedArticleImages(article);
    const html = buildStandaloneHtml(article, imageResult);
    downloadText(
      `${sanitizeFilename(article.title)}.html`,
      "text/html;charset=utf-8",
      html,
    );
    setStatus(
      `HTML 已生成：正文图片内嵌 ${imageResult.embedded}/${article.imageRefs.length} 张。`,
      "success",
    );
  } catch (error) {
    setStatus(error instanceof Error ? error.message : String(error), "error");
  } finally {
    setButtonsEnabled(true);
  }
});

downloadMarkdownButton.addEventListener("click", async () => {
  setButtonsEnabled(false);
  try {
    const article = await getArticle();
    const markdown = convertHtmlToMarkdown(article);
    downloadText(
      `${sanitizeFilename(article.title)}.md`,
      "text/markdown;charset=utf-8",
      markdown,
    );
    setStatus("Markdown 已下载。", "success");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : String(error), "error");
  } finally {
    setButtonsEnabled(true);
  }
});

copyMarkdownButton.addEventListener("click", async () => {
  setButtonsEnabled(false);
  try {
    const article = await getArticle();
    await navigator.clipboard.writeText(convertHtmlToMarkdown(article));
    setStatus("Markdown 已复制到剪贴板。", "success");
  } catch (error) {
    setStatus(
      error instanceof Error
        ? `复制失败：${error.message}`
        : `复制失败：${String(error)}`,
      "error",
    );
  } finally {
    setButtonsEnabled(true);
  }
});

void initialize();
