const testMode = new URLSearchParams(window.location.search).get("mode");
const TEST_ARTICLE_URL =
  testMode === "invalid"
    ? "https://example.com/not-a-wechat-article"
    : testMode === "legacy"
      ? "https://mp.weixin.qq.com/s?__biz=local-smoke-test"
      : "https://mp.weixin.qq.com/s/local-smoke-test";

window.__wechatExporterTest = {
  blobs: [],
  clicks: [],
  copiedMarkdown: "",
};

const NativeBlob = window.Blob;

window.Blob = class TestBlob extends NativeBlob {
  constructor(parts, options) {
    super(parts, options);
    document.documentElement.dataset.lastBlobType = options?.type || "";
    document.documentElement.dataset.lastBlobText = parts
      .map((part) => (typeof part === "string" ? part : ""))
      .join("");
  }
};

URL.createObjectURL = (blob) => {
  window.__wechatExporterTest.blobs.push(blob);
  return `blob:test-${window.__wechatExporterTest.blobs.length}`;
};

URL.revokeObjectURL = () => {};

HTMLAnchorElement.prototype.click = function click() {
  window.__wechatExporterTest.clicks.push({
    download: this.download,
    href: this.href,
  });
  document.documentElement.dataset.lastDownload = this.download;
  document.documentElement.dataset.downloadCount = String(
    window.__wechatExporterTest.clicks.length,
  );
};

Object.defineProperty(navigator, "clipboard", {
  configurable: true,
  value: {
    async writeText(value) {
      window.__wechatExporterTest.copiedMarkdown = value;
      document.documentElement.dataset.copiedMarkdown = value;
    },
  },
});

window.fetch = async (input) => {
  const url = new URL(String(input));
  if (url.hostname !== "mmbiz.qpic.cn") {
    return new Response("", { status: 404 });
  }

  return new Response(
    '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><rect width="2" height="2" fill="#087f5b"/></svg>',
    {
      headers: {
        "content-type": "image/svg+xml",
      },
      status: 200,
    },
  );
};

window.chrome = {
  tabs: {
    async query() {
      return [{ id: 1, url: TEST_ARTICLE_URL }];
    },
  },
  scripting: {
    async executeScript({ func }) {
      return [{ result: func() }];
    },
  },
};
