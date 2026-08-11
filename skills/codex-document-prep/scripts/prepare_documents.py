#!/usr/bin/env python3
"""Convert documents locally into indexed, bounded Markdown chunks.

The script never writes document text to stdout. Stdout contains one compact JSON summary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional


SUPPORTED = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".epub",
    ".mobi", ".azw3", ".html", ".htm", ".md", ".markdown", ".txt",
    ".csv", ".tsv", ".json", ".xml", ".rtf",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def safe_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "big5", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


class MarkdownHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.list_depth = 0
        self.heading: Optional[int] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "svg", "noscript"}:
            self.skip_depth += 1
        elif self.skip_depth:
            return
        elif re.fullmatch(r"h[1-6]", tag):
            self.heading = int(tag[1])
            self.parts.append("\n\n" + "#" * self.heading + " ")
        elif tag in {"p", "div", "section", "article", "header", "footer"}:
            self.parts.append("\n\n")
        elif tag == "br":
            self.parts.append("\n")
        elif tag in {"ul", "ol"}:
            self.list_depth += 1
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n" + "  " * max(0, self.list_depth - 1) + "- ")
        elif tag == "tr":
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "svg", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        elif self.skip_depth:
            return
        elif tag in {"ul", "ol"}:
            self.list_depth = max(0, self.list_depth - 1)
            self.parts.append("\n")
        elif re.fullmatch(r"h[1-6]", tag):
            self.heading = None
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def markdown(self) -> str:
        return "".join(self.parts)


def html_to_markdown(value: str) -> str:
    parser = MarkdownHTMLParser()
    parser.feed(value)
    return parser.markdown()


def normalize_markdown(value: str) -> str:
    value = html.unescape(value).replace("\x00", "").replace("\u200b", "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    previous = None
    blank = 0
    for raw in value.splitlines():
        line = raw.rstrip()
        if not line.strip():
            blank += 1
            if blank <= 2:
                lines.append("")
            continue
        blank = 0
        compact = line.strip()
        if compact == previous and len(compact) < 180:
            continue
        lines.append(line)
        previous = compact
    return "\n".join(lines).strip() + "\n"


def run_converter(command: list[str], output: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=1800)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if completed.returncode != 0 or not output.is_file():
        message = (completed.stderr or f"exit code {completed.returncode}").strip()
        return False, message[-500:]
    return True, ""


def external_convert(path: Path, temp: Path) -> tuple[Optional[str], Optional[str], list[str]]:
    warnings: list[str] = []
    ext = path.suffix.lower()
    markitdown = shutil.which("markitdown")
    if markitdown:
        output = temp / "markitdown.md"
        ok, error = run_converter([markitdown, str(path), "-o", str(output)], output)
        if ok:
            return safe_text(output), "markitdown", warnings
        warnings.append(f"markitdown failed: {error}")

    pandoc_exts = {".docx", ".xlsx", ".pptx", ".epub", ".rtf", ".html", ".htm"}
    pandoc = shutil.which("pandoc")
    if pandoc and ext in pandoc_exts:
        output = temp / "pandoc.md"
        ok, error = run_converter([pandoc, str(path), "-t", "gfm", "-o", str(output)], output)
        if ok:
            return safe_text(output), "pandoc", warnings
        warnings.append(f"pandoc failed: {error}")

    if ext == ".pdf" and (pdftotext := shutil.which("pdftotext")):
        output = temp / "pdftotext.txt"
        ok, error = run_converter([pdftotext, "-layout", str(path), str(output)], output)
        if ok:
            text = safe_text(output)
            if len(text.strip()) < 200:
                warnings.append("very little PDF text was extracted; the file may be scanned and need local OCR")
            return text, "pdftotext", warnings
        warnings.append(f"pdftotext failed: {error}")
    return None, None, warnings


def paragraph_text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.iter() if local_name(node.tag) == "t").strip()


def native_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    body = next((node for node in root.iter() if local_name(node.tag) == "body"), root)
    output: list[str] = []
    for child in body:
        kind = local_name(child.tag)
        if kind == "p":
            text = paragraph_text(child)
            if not text:
                continue
            style = ""
            for node in child.iter():
                if local_name(node.tag) == "pStyle":
                    style = next((v for k, v in node.attrib.items() if local_name(k) == "val"), "")
                    break
            match = re.search(r"heading\s*([1-6])", style, re.I)
            output.append(("#" * int(match.group(1)) + " " if match else "") + text)
        elif kind == "tbl":
            rows: list[list[str]] = []
            for row in (node for node in child if local_name(node.tag) == "tr"):
                rows.append([paragraph_text(cell) for cell in row if local_name(cell.tag) == "tc"])
            if rows:
                width = max(map(len, rows))
                rows = [row + [""] * (width - len(row)) for row in rows]
                output.append("| " + " | ".join(rows[0]) + " |")
                output.append("| " + " | ".join(["---"] * width) + " |")
                output.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n\n".join(output)


def xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(node.text or "" for node in item.iter() if local_name(node.tag) == "t")
            for item in root if local_name(item.tag) == "si"]


def column_index(reference: str) -> int:
    letters = re.match(r"[A-Za-z]+", reference)
    value = 0
    for char in (letters.group(0).upper() if letters else "A"):
        value = value * 26 + ord(char) - 64
    return max(0, value - 1)


def native_xlsx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        shared = xlsx_shared_strings(archive)
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            next((v for k, v in rel.attrib.items() if local_name(k) == "Id"), ""):
            next((v for k, v in rel.attrib.items() if local_name(k) == "Target"), "")
            for rel in relationships
        }
        sections: list[str] = []
        for sheet in (node for node in workbook.iter() if local_name(node.tag) == "sheet"):
            name = next((v for k, v in sheet.attrib.items() if local_name(k) == "name"), "Sheet")
            rel_id = next((v for k, v in sheet.attrib.items() if local_name(k) == "id"), "")
            target = rel_map.get(rel_id, "")
            sheet_path = str(PurePosixPath("xl") / target) if not target.startswith("xl/") else target
            sheet_path = str(PurePosixPath(sheet_path))
            root = ET.fromstring(archive.read(sheet_path))
            rows: list[list[str]] = []
            for row in (node for node in root.iter() if local_name(node.tag) == "row"):
                values: list[str] = []
                for cell in (node for node in row if local_name(node.tag) == "c"):
                    ref = next((v for k, v in cell.attrib.items() if local_name(k) == "r"), "A1")
                    idx = column_index(ref)
                    while len(values) <= idx:
                        values.append("")
                    cell_type = next((v for k, v in cell.attrib.items() if local_name(k) == "t"), "")
                    raw = next((node.text or "" for node in cell.iter() if local_name(node.tag) == "v"), "")
                    inline = "".join(node.text or "" for node in cell.iter() if local_name(node.tag) == "t")
                    formula = next((node.text or "" for node in cell.iter() if local_name(node.tag) == "f"), "")
                    if cell_type == "s" and raw.isdigit() and int(raw) < len(shared):
                        value = shared[int(raw)]
                    elif cell_type == "inlineStr":
                        value = inline
                    else:
                        value = raw or inline
                    if formula:
                        value = f"={formula}" + (f" [{value}]" if value else "")
                    values[idx] = value.replace("\t", " ").replace("\n", " ")
                rows.append(values)
            sections.append(f"# Sheet: {name}\n\n```tsv\n" + "\n".join("\t".join(row) for row in rows) + "\n```")
        return "\n\n".join(sections)


def native_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        slides = sorted((name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
                        key=lambda name: int(re.search(r"\d+", Path(name).stem).group()))
        sections: list[str] = []
        for number, slide in enumerate(slides, 1):
            root = ET.fromstring(archive.read(slide))
            texts = [node.text or "" for node in root.iter() if local_name(node.tag) == "t"]
            sections.append(f"# Slide {number}\n\n" + "\n\n".join(filter(None, texts)))
        return "\n\n".join(sections)


def native_epub(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        opf_path = next((next((v for k, v in node.attrib.items() if local_name(k) == "full-path"), "")
                         for node in container.iter() if local_name(node.tag) == "rootfile"), "")
        if not opf_path:
            raise ValueError("EPUB container has no rootfile")
        opf = ET.fromstring(archive.read(opf_path))
        base = PurePosixPath(opf_path).parent
        manifest: dict[str, str] = {}
        for node in opf.iter():
            if local_name(node.tag) == "item":
                item_id = next((v for k, v in node.attrib.items() if local_name(k) == "id"), "")
                href = next((v for k, v in node.attrib.items() if local_name(k) == "href"), "")
                manifest[item_id] = str(base / href)
        spine = [next((v for k, v in node.attrib.items() if local_name(k) == "idref"), "")
                 for node in opf.iter() if local_name(node.tag) == "itemref"]
        sections: list[str] = []
        for item_id in spine:
            member = manifest.get(item_id)
            if member and member in archive.namelist():
                sections.append(html_to_markdown(archive.read(member).decode("utf-8", errors="replace")))
        return "\n\n".join(sections)


def native_convert(path: Path, temp: Path) -> tuple[str, str, list[str]]:
    ext = path.suffix.lower()
    warnings: list[str] = []
    if ext in {".md", ".markdown", ".txt", ".csv", ".tsv", ".json", ".xml"}:
        return safe_text(path), "text", warnings
    if ext in {".html", ".htm"}:
        return html_to_markdown(safe_text(path)), "html-stdlib", warnings
    if ext == ".docx":
        return native_docx(path), "docx-stdlib", warnings
    if ext == ".xlsx":
        return native_xlsx(path), "xlsx-stdlib", warnings
    if ext == ".pptx":
        return native_pptx(path), "pptx-stdlib", warnings
    if ext == ".epub":
        return native_epub(path), "epub-stdlib", warnings
    if ext in {".mobi", ".azw3"}:
        ebook = shutil.which("ebook-convert")
        mac = Path("/Applications/calibre.app/Contents/MacOS/ebook-convert")
        if not ebook and mac.is_file():
            ebook = str(mac)
        if not ebook:
            raise RuntimeError("MOBI/AZW3 requires Calibre's ebook-convert")
        epub = temp / "converted.epub"
        ok, error = run_converter([ebook, str(path), str(epub)], epub)
        if not ok:
            raise RuntimeError(f"ebook-convert failed: {error}")
        return native_epub(epub), "ebook-convert+epub-stdlib", warnings
    raise RuntimeError(f"no available local converter for {ext}; install markitdown or a format-specific local tool")


def convert(path: Path) -> tuple[str, str, list[str]]:
    with tempfile.TemporaryDirectory(prefix="codex-doc-") as directory:
        temp = Path(directory)
        text, backend, warnings = external_convert(path, temp)
        if text is not None and backend is not None:
            return normalize_markdown(text), backend, warnings
        native_text, native_backend, native_warnings = native_convert(path, temp)
        return normalize_markdown(native_text), native_backend, warnings + native_warnings


def chunk_markdown(text: str, limit: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + limit)
        if end < len(text):
            search_start = start + limit // 2
            boundaries: list[int] = []
            for marker in ("\n\n", "\n#", "。", ". ", "! ", "? "):
                position = text.rfind(marker, search_start, end)
                if position >= search_start:
                    boundaries.append(position + len(marker))
            if boundaries:
                end = max(boundaries)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks or [""]


def heading_for(chunk: str) -> str:
    for line in chunk.splitlines():
        if re.match(r"^#{1,6}\s+", line):
            return re.sub(r"^#{1,6}\s+", "", line).strip()[:160]
    first = next((line.strip() for line in chunk.splitlines() if line.strip()), "Untitled")
    return first[:160]


def slug_for(path: Path) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("-.") or "document"
    digest = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:8]
    return f"{base[:60]}-{digest}"


def collect_inputs(values: list[str], output_dir: Path) -> list[Path]:
    files: list[Path] = []
    output_resolved = output_dir.resolve()
    for value in values:
        path = Path(value).expanduser().resolve()
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED:
                    try:
                        candidate.resolve().relative_to(output_resolved)
                        continue
                    except ValueError:
                        files.append(candidate.resolve())
        else:
            raise FileNotFoundError(value)
    return sorted(set(files))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Files or directories to prepare")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--chunk-chars", type=int, default=5000)
    parser.add_argument("--overlap-chars", type=int, default=300)
    parser.add_argument("--force", action="store_true", help="Replace an existing per-document output directory")
    args = parser.parse_args()
    if args.chunk_chars < 1000:
        parser.error("--chunk-chars must be at least 1000")
    if not 0 <= args.overlap_chars < args.chunk_chars // 2:
        parser.error("--overlap-chars must be non-negative and less than half the chunk size")
    return args


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir.expanduser().resolve()
    documents_dir = output_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for source in collect_inputs(args.inputs, output_dir):
        if source.suffix.lower() not in SUPPORTED:
            continue
        slug = slug_for(source)
        doc_dir = documents_dir / slug
        if doc_dir.exists() and not args.force:
            errors.append({"source": str(source), "error": "output exists; use --force to replace it"})
            continue
        if doc_dir.exists():
            shutil.rmtree(doc_dir)
        chunks_dir = doc_dir / "chunks"
        chunks_dir.mkdir(parents=True)
        try:
            text, backend, warnings = convert(source)
            chunks = chunk_markdown(text, args.chunk_chars, args.overlap_chars)
            (doc_dir / "source.md").write_text(text, encoding="utf-8")
            chunk_entries: list[dict[str, object]] = []
            for index, chunk in enumerate(chunks, 1):
                relative = Path("documents") / slug / "chunks" / f"{index:04d}.md"
                header = f"<!-- source: {source.name}; chunk: {index}/{len(chunks)} -->\n\n"
                (output_dir / relative).write_text(header + chunk + "\n", encoding="utf-8")
                chunk_entries.append({"path": relative.as_posix(), "heading": heading_for(chunk), "chars": len(chunk)})
            entries.append({
                "source": str(source), "name": source.name, "backend": backend,
                "chars": len(text), "warnings": warnings, "chunks": chunk_entries,
            })
        except Exception as exc:  # keep processing other inputs
            errors.append({"source": str(source), "error": str(exc)[:500]})

    manifest = {
        "version": 1,
        "chunk_chars": args.chunk_chars,
        "overlap_chars": args.overlap_chars,
        "documents": entries,
        "errors": errors,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    index_lines = ["# Prepared document index", "", f"Documents: {len(entries)}; errors: {len(errors)}", ""]
    for entry in entries:
        index_lines.append(f"## {entry['name']}")
        index_lines.append(f"- Backend: `{entry['backend']}`; characters: {entry['chars']}")
        for chunk in entry["chunks"]:  # type: ignore[index]
            index_lines.append(f"- [{chunk['path']}]({chunk['path']}): {chunk['heading']} ({chunk['chars']} chars)")
        index_lines.append("")
    if errors:
        index_lines.extend(["## Skipped files", ""])
        index_lines.extend(f"- `{item['source']}`: {item['error']}" for item in errors)
    (output_dir / "index.md").write_text("\n".join(index_lines).strip() + "\n", encoding="utf-8")
    summary = {
        "output_dir": str(output_dir), "documents": len(entries),
        "chunks": sum(len(entry["chunks"]) for entry in entries), "errors": len(errors),
        "index": str(output_dir / "index.md"), "manifest": str(output_dir / "manifest.json"),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
