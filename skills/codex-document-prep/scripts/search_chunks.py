#!/usr/bin/env python3
"""Search prepared chunks and print only bounded JSON snippets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def snippets(text: str, terms: list[str], limit: int, count: int = 2) -> list[str]:
    lowered = text.casefold()
    positions = sorted({position for term in terms if (position := lowered.find(term.casefold())) >= 0})
    output: list[str] = []
    for position in positions[:count]:
        start = max(0, position - limit // 2)
        end = min(len(text), start + limit)
        excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
        rendered = ("…" if start else "") + excerpt + ("…" if end < len(text) else "")
        if rendered not in output:
            output.append(rendered)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared_dir", type=Path)
    parser.add_argument("query")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--snippet-chars", type=int, default=320)
    args = parser.parse_args()
    if not 1 <= args.top <= 20:
        parser.error("--top must be between 1 and 20")
    if not 80 <= args.snippet_chars <= 1200:
        parser.error("--snippet-chars must be between 80 and 1200")
    root = args.prepared_dir.expanduser().resolve()
    terms = [term for term in re.split(r"\s+", args.query.strip()) if term]
    if not terms:
        parser.error("query must not be empty")
    matches: list[dict[str, object]] = []
    for path in root.glob("documents/*/chunks/*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.casefold()
        counts = [lowered.count(term.casefold()) for term in terms]
        if not any(counts):
            continue
        phrase = args.query.strip().casefold()
        score = sum(counts) + (5 if phrase and phrase in lowered else 0) + (3 if all(counts) else 0)
        heading = next((re.sub(r"^#{1,6}\s+", "", line).strip() for line in text.splitlines()
                        if re.match(r"^#{1,6}\s+", line)), "")
        matches.append({
            "path": path.relative_to(root).as_posix(), "heading": heading[:160],
            "score": score, "snippets": snippets(text, terms, args.snippet_chars),
        })
    matches.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    print(json.dumps({"query": args.query, "matches": matches[:args.top]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
