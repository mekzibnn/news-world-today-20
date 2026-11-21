#!/usr/bin/env python3
"""news-image-20261120 entry program.

Copies the pre-built front-page image (entry.png, in this repository) to
/output/entry.png. Standard library only, no network, deterministic: the
same input bytes always produce the same output bytes.
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "entry.png"
DEST = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DEST)


if __name__ == "__main__":
    main()
