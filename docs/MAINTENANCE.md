# 长期维护指南

这份文档用于避免以后再次出现“插件还在用，但找不到代码和安装位置”的情况。

## 唯一正式项目

正式 GitHub 仓库：

```text
https://github.com/zhijinallin/wechat-article-exporter
```

GitHub 仓库的 `main` 分支是长期维护的正式源代码。电脑上的安装目录只是工作副本，不应成为唯一备份。

## 重要内容分别在哪里

| 内容 | 位置 |
|---|---|
| 插件版本号和权限 | `manifest.json` |
| 插件界面 | `popup.html`、`popup.css` |
| 导出功能 | `popup.js`、`extractor.js` |
| 用户说明 | `docs/USER-GUIDE.md` |
| 朋友安装说明 | `docs/FRIEND-INSTALL.md` |
| 商店提交说明 | `docs/WEB-STORE-PUBLISH.md` |
| 每次更新内容 | `CHANGELOG.md` |
| 打包结果 | 本机 `dist/` 和 GitHub Releases |

## 发布新版的固定流程

### 1. 确认要发布的变化

先把这次解决的问题和用户能感知的变化写入 `CHANGELOG.md`。

### 2. 提高版本号

修改 `manifest.json` 中的版本号：

- 修复小问题：`0.1.0` → `0.1.1`；
- 增加明显功能：`0.1.1` → `0.2.0`；
- 出现不兼容的大变化：`0.x` → `1.0.0`。

Chrome 商店不接受比已发布版本更低或相同的版本号。

### 3. 运行自动检查

```bash
./scripts/package.sh
./scripts/verify.sh
```

只有出现“验证通过”后，才进入人工测试。

如果维护电脑已经安装 Python Playwright，可以再启动本地测试服务器，并运行浏览器冒烟测试：

```bash
python3 -m http.server 8766 --bind 127.0.0.1
python3 scripts/browser-smoke.py
```

这个测试不访问微信，只使用 `test/` 中的模拟文章。

### 4. 人工测试

至少选择三篇文章：

- 一篇以文字为主；
- 一篇图片较多；
- 一篇包含表格、引用或复杂排版。

分别检查 HTML 下载、Markdown 下载和 Markdown 复制。

### 5. 保存到 GitHub

```bash
git add .
git commit -m "release: v版本号"
git push origin main
git tag v版本号
git push origin v版本号
```

在 GitHub Releases 中创建对应版本，并上传 `dist/` 中两个 ZIP 和 `SHA256SUMS.txt`。

### 6. 更新 Chrome 商店

在原来的商店项目中上传新版 `chrome-web-store.zip`，不要新建第二个商店项目。

## GitHub 应该保存什么

应该提交：代码、文档、图标、商店素材、测试和脚本。

不要提交：

- `.pem`、`.key` 等私钥；
- Chrome 或 GitHub 登录凭证；
- 导出的真实文章；
- 本机 `dist/`、`output/` 临时产物；
- 包含个人信息的测试数据。

## 关于本地 CRX 私钥

如果以后确实生成 `.crx`，Chrome 会同时生成 `.pem` 私钥。私钥用于维持同一个扩展身份：

- 不发给朋友；
- 不提交 GitHub；
- 单独放在安全的密码库或加密备份中；
- 丢失后无法使用原来的本地签名继续更新。

Chrome 商店发布不需要上传这个 `.pem`。

## 出现故障时

1. 先记录不能导出的文章链接类型和错误提示，不要马上覆盖正式版本；
2. 在 GitHub 新建 Issue；
3. 从最后一个正常工作的 GitHub Release 重新安装，确认是否是新版造成；
4. 修复后提高版本号重新发布；
5. 不删除旧 Release，保留回滚依据。

## 每月最低维护动作

- 用一篇新文章测试三种导出方式；
- 检查 GitHub Issue；
- 检查 Chrome 商店是否有政策、审核或停用通知；
- 确认仓库、商店账号和两步验证仍可访问。
