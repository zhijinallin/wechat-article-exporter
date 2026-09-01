#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' "$PROJECT_ROOT/manifest.json")
DIST_DIR="$PROJECT_ROOT/dist"
STAGE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/wechat-article-exporter.XXXXXX")

cleanup() {
  rm -rf "$STAGE_DIR"
}
trap cleanup EXIT HUP INT TERM

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

RUNTIME_FILES="manifest.json popup.html popup.css popup.js extractor.js"

copy_runtime() {
  destination=$1
  mkdir -p "$destination/icons"
  for source_file in $RUNTIME_FILES; do
    cp "$PROJECT_ROOT/$source_file" "$destination/$source_file"
  done
  cp "$PROJECT_ROOT"/icons/*.png "$destination/icons/"
}

FRIEND_ROOT_NAME="wechat-article-exporter-v$VERSION"
FRIEND_PARENT="$STAGE_DIR/friends"
FRIEND_ROOT="$FRIEND_PARENT/$FRIEND_ROOT_NAME"
mkdir -p "$FRIEND_ROOT/docs" "$FRIEND_ROOT/store-assets"
copy_runtime "$FRIEND_ROOT"
cp "$PROJECT_ROOT/README.md" "$FRIEND_ROOT/README.md"
cp "$PROJECT_ROOT/PRIVACY.md" "$FRIEND_ROOT/PRIVACY.md"
cp "$PROJECT_ROOT/CHANGELOG.md" "$FRIEND_ROOT/CHANGELOG.md"
cp "$PROJECT_ROOT/docs/FRIEND-INSTALL.md" "$FRIEND_ROOT/README-INSTALL.md"
cp "$PROJECT_ROOT/docs/USER-GUIDE.md" "$FRIEND_ROOT/docs/USER-GUIDE.md"
cp "$PROJECT_ROOT/store-assets/screenshot-1280x800.png" "$FRIEND_ROOT/store-assets/screenshot-1280x800.png"

FRIEND_ZIP="$DIST_DIR/wechat-article-exporter-v$VERSION-friends-unpacked.zip"
(
  cd "$FRIEND_PARENT"
  zip -q -r "$FRIEND_ZIP" "$FRIEND_ROOT_NAME"
)

STORE_ROOT="$STAGE_DIR/store"
copy_runtime "$STORE_ROOT"
STORE_ZIP="$DIST_DIR/wechat-article-exporter-v$VERSION-chrome-web-store.zip"
(
  cd "$STORE_ROOT"
  zip -q -r "$STORE_ZIP" manifest.json popup.html popup.css popup.js extractor.js icons
)

python3 "$PROJECT_ROOT/scripts/write-checksums.py" "$DIST_DIR"

printf '%s\n' "已生成朋友手动安装版：$FRIEND_ZIP"
printf '%s\n' "已生成 Chrome 商店版：$STORE_ZIP"
printf '%s\n' "校验值：$DIST_DIR/SHA256SUMS.txt"
