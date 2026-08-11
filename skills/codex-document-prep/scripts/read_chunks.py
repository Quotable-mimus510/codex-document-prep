#!/usr/bin/env python3
"""Read selected prepared chunks with a strict aggregate character cap."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared_dir", type=Path)
    parser.add_argument("chunks", nargs="+")
    parser.add_argument("--max-chars", type=int, default=6000)
    args = parser.parse_args()
    if not 500 <= args.max_chars <= 30000:
        parser.error("--max-chars must be between 500 and 30000")
    root = args.prepared_dir.expanduser().resolve()
    output: list[str] = []
    used = 0
    for value in args.chunks:
        candidate = (root / value).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            parser.error(f"chunk escapes prepared directory: {value}")
        if not candidate.is_file() or candidate.suffix.lower() != ".md" or "chunks" not in candidate.parts:
            parser.error(f"not a prepared Markdown chunk: {value}")
        text = candidate.read_text(encoding="utf-8", errors="replace")
        label = f"\n\n--- {candidate.relative_to(root).as_posix()} ---\n\n"
        if used + len(label) >= args.max_chars:
            break
        output.append(label)
        used += len(label)
        remaining = args.max_chars - used
        if len(text) > remaining:
            marker = "\n\n[truncated by --max-chars]"
            excerpt = text[:max(0, remaining - len(marker))]
            output.extend([excerpt, marker[:remaining - len(excerpt)]])
            used = args.max_chars
            break
        output.append(text)
        used += len(text)
    print("".join(output)[:args.max_chars], end="")


if __name__ == "__main__":
    main()
