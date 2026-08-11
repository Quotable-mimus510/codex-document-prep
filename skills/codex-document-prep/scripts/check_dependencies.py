#!/usr/bin/env python3
"""Report local converter availability without installing or changing anything."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional


def locate(name: str) -> Optional[str]:
    found = shutil.which(name)
    if found:
        return found
    if name == "ebook-convert":
        mac = Path("/Applications/calibre.app/Contents/MacOS/ebook-convert")
        if mac.is_file():
            return str(mac)
    return None


def main() -> None:
    commands = {
        name: {"available": bool(path := locate(name)), "path": path}
        for name in ("markitdown", "pandoc", "pdftotext", "ebook-convert")
    }
    report = {
        "commands": commands,
        "bundled_readers": ["docx", "xlsx", "pptx", "epub", "html", "txt", "md", "csv", "tsv", "json", "xml"],
        "notes": {
            "pdf": "markitdown or pdftotext is required; scanned PDFs need optional local OCR",
            "mobi_azw3": "ebook-convert is required",
            "privacy": "no dependency is installed and no network request is made",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
