# Chrome 商店发布指南

目标：把插件发布为 **Unlisted（非公开）**。它不会出现在商店搜索结果中，但拿到链接的朋友可以正常安装，并自动接收更新。

这份指南分为“项目已自动准备的部分”和“账号所有者必须亲自完成的部分”。

## 发布前需要具备

- 一个 Chrome Web Store 开发者账号；
- 完成 Google 要求的一次性开发者注册付款；
- 开启 Google 账号两步验证；
- 一个任何人都能打开的隐私政策网址；
- 已通过项目校验的商店 ZIP。

官方入口：<https://chrome.google.com/webstore/devconsole/>

## 第一步：生成商店 ZIP

在项目目录运行：

```bash
./scripts/package.sh
./scripts/verify.sh
```

需要上传的文件是：

```text
dist/wechat-article-exporter-v0.1.0-chrome-web-store.zip
```

不要上传朋友版 ZIP，也不要上传 `.crx` 或 `.pem`。

## 第二步：新建商店项目

1. 登录 Chrome Web Store Developer Dashboard；
2. 点击“New item”或“新增项目”；
3. 上传 `chrome-web-store.zip`；
4. 如果系统提示版本已存在，需要提高 `manifest.json` 中的版本号后重新打包。

ZIP 打开后，`manifest.json` 必须直接位于最外层。本项目的打包脚本已经按这个规则生成。

## 第三步：填写商店信息

打开 [商店上架文案](STORE-LISTING.md)，逐项复制：

- 简短说明；
- 详细说明；
- 单一用途；
- 权限用途；
- 审核人员测试步骤。

上传 `store-assets/` 中的图标和截图。

## 第四步：填写隐私信息

需要如实说明：插件会处理“网站内容”，因为它读取用户当前打开的文章；这些内容只在本机处理，不会发送给开发者或第三方。

隐私政策文件位于 [PRIVACY.md](../PRIVACY.md)。提交时必须填写一个公众可以打开的网址。计划使用的地址是：

```text
https://github.com/zhijinallin/wechat-article-exporter/blob/main/PRIVACY.md
```

只有当 GitHub 仓库公开后，这个地址才能作为公开隐私政策网址。若仓库保持私有，需要另外发布一个公开的隐私政策页面。

## 第五步：选择发布范围

在 Distribution 页面选择：

```text
Visibility: Unlisted
```

不要误选 Public，除非项目所有者决定让所有人通过商店搜索发现插件。

Unlisted 仍会经过和 Public 相同的政策审核。

## 第六步：提交审核

1. 检查所有页面是否显示完成；
2. 点击“Submit for review”；
3. 保存商店项目 ID 和后台地址；
4. 审核期间不要创建内容相同的第二个项目；
5. 审核通过后，把非公开安装链接记录到 README 和 GitHub Release。

## 以后如何更新

1. 修改插件；
2. 提高 `manifest.json` 的版本号；
3. 更新 `CHANGELOG.md`；
4. 重新运行打包和验证脚本；
5. 在原来的商店项目中上传新的商店 ZIP；
6. 提交新版审核。

不要新建另一个商店项目，否则会产生新的扩展 ID，现有用户也收不到自动更新。

## 官方参考

- [准备扩展 ZIP](https://developer.chrome.com/docs/webstore/prepare)
- [选择 Public、Unlisted 或 Private](https://developer.chrome.com/docs/webstore/cws-dashboard-distribution)
- [本地处理也需要披露网站内容](https://developer.chrome.com/docs/webstore/program-policies/user-data-faq)
- [扩展发行方式](https://developer.chrome.com/docs/extensions/how-to/distribute)
