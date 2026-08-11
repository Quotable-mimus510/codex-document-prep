#!/usr/bin/env python3
"""Dependency-free smoke test for native conversion, chunking, search, and caps."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "codex-document-prep" / "scripts"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], check=True, text=True, capture_output=True)


def make_fixtures(root: Path) -> None:
    (root / "sample.md").write_text(
        "# 现金流分析\n\n" + "现金流折现模型需要根据风险选择折现率。" * 500,
        encoding="utf-8",
    )
    (root / "sample.html").write_text(
        "<html><body><h1>Local-first</h1><p>Only retrieve relevant excerpts.</p></body></html>",
        encoding="utf-8",
    )
    with zipfile.ZipFile(root / "sample.docx", "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="w"><w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/>'
            '</w:pPr><w:r><w:t>年度报告</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>经营现金流稳定。</w:t></w:r></w:p></w:body></w:document>',
        )
    with zipfile.ZipFile(root / "sample.xlsx", "w") as archive:
        archive.writestr("xl/workbook.xml", '<workbook xmlns:r="rel"><sheets><sheet name="预算" r:id="rId1"/></sheets></workbook>')
        archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        archive.writestr("xl/sharedStrings.xml", '<sst><si><t>项目</t></si><si><t>收入</t></si></sst>')
        archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row></sheetData></worksheet>')
    with zipfile.ZipFile(root / "sample.epub", "w") as archive:
        archive.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>')
        archive.writestr("OEBPS/content.opf", '<package><manifest><item id="c1" href="chapter.xhtml"/></manifest><spine><itemref idref="c1"/></spine></package>')
        archive.writestr("OEBPS/chapter.xhtml", '<html><body><h1>第一章</h1><p>电子书折现率章节。</p></body></html>')


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-document-prep-test-") as directory:
        root = Path(directory)
        inputs = root / "inputs"
        output = root / "prepared"
        inputs.mkdir()
        make_fixtures(inputs)

        prepared = run(
            str(SCRIPTS / "prepare_documents.py"), str(inputs),
            "--output-dir", str(output), "--chunk-chars", "1000", "--overlap-chars", "80",
        )
        summary = json.loads(prepared.stdout)
        assert summary["documents"] == 5
        assert summary["errors"] == 0

        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        assert all(chunk["chars"] <= 1000 for doc in manifest["documents"] for chunk in doc["chunks"])

        searched = run(str(SCRIPTS / "search_chunks.py"), str(output), "现金流 折现率", "--top", "3")
        matches = json.loads(searched.stdout)["matches"]
        assert matches and matches[0]["score"] > 0

        read = run(
            str(SCRIPTS / "read_chunks.py"), str(output), matches[0]["path"], "--max-chars", "500",
        )
        assert 0 < len(read.stdout) <= 500

    print("smoke test passed")


if __name__ == "__main__":
    main()
