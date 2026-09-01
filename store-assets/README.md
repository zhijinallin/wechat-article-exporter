# Chrome 商店素材

- `store-icon-128.png`：商店图标；
- `screenshot-1280x800.png`：主要商店截图；
- `promo-440x280.png`：小型宣传图；
- `popup-reference.png`：在指定文章“表达者红利和价值索取”上运行插件后取得的真实截图，作为商店截图的界面来源；

如需重新生成图标和宣传图，在 macOS 项目目录运行：

```bash
python3 scripts/generate-assets.py
```

该脚本需要 Pillow，并使用 macOS 自带的华文字体。生成前必须先取得新的真实原始截图；生成后必须人工检查图片，不能只依赖尺寸校验。
