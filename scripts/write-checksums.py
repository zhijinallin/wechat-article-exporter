#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：write-checksums.py DIST_DIR", file=sys.stderr)
        return 2

    dist_dir = Path(sys.argv[1]).resolve()
    zip_files = sorted(dist_dir.glob("*.zip"))
    if not zip_files:
        print("没有找到 ZIP 文件。", file=sys.stderr)
        return 1

    lines = [f"{sha256(path)}  {path.name}" for path in zip_files]
    (dist_dir / "SHA256SUMS.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
