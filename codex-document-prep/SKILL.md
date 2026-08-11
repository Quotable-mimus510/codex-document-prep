---
name: codex-document-prep
description: Locally convert, clean, split, index, search, and selectively retrieve large PDF, Word, Excel, PowerPoint, EPUB, MOBI, HTML, Markdown, text, CSV, and related document collections for Codex while minimizing token and credit usage. Use when users mention saving quota/tokens/credits, preparing books or office files for Codex, building a local document knowledge base, converting files to Markdown, or searching large documents without loading them in full. Do not use for high-fidelity editing or visual review of the original document.
---

# Codex Document Prep

Prepare files locally, then expose only a small index and bounded search hits to the model. Never print a converted document in full during preparation.

## Workflow

1. Run the dependency check without installing anything:

   ```bash
   python3 <skill-dir>/scripts/check_dependencies.py
   ```

2. Choose an output directory outside the source directory. Run preparation with explicit file paths:

   ```bash
   python3 <skill-dir>/scripts/prepare_documents.py <input> --output-dir <prepared-dir>
   ```

   For multiple inputs, repeat positional paths. Directories are scanned recursively. The command writes normalized source Markdown, bounded chunks, `index.md`, and `manifest.json`. It prints only a compact JSON summary.

3. Inspect only `index.md` or the compact manifest summary. Do not open every chunk.

4. Search prepared chunks before reading content:

   ```bash
   python3 <skill-dir>/scripts/search_chunks.py <prepared-dir> "<query>" --top 5
   ```

5. Read only selected matches with a hard character limit:

   ```bash
   python3 <skill-dir>/scripts/read_chunks.py <prepared-dir> <relative-chunk-path> --max-chars 6000
   ```

6. Answer from the retrieved excerpts. If evidence is insufficient, retrieve another specific chunk instead of loading the whole corpus.

## Conversion routing

- Prefer `markitdown` for PDF, DOCX, XLSX/XLS, PPTX, EPUB, and common text formats.
- Fall back to `pandoc` for DOCX, XLSX, PPTX, EPUB, RTF, and HTML.
- Fall back to `pdftotext` for born-digital PDFs.
- Use the bundled standard-library readers for DOCX, XLSX, PPTX, EPUB, HTML, and text when external converters are unavailable.
- Require Calibre's `ebook-convert` for MOBI/AZW3, then parse the resulting EPUB locally.
- Treat very short PDF extraction as a probable scan. Do not silently invoke an online OCR or an LLM. Explain that local Docling/Marker OCR is optional and request approval before installing dependencies.

## Token safeguards

- Always write converter output to a file; never pipe full documents into the terminal or chat.
- Keep the default chunk size unless the user asks otherwise. Reduce `--chunk-chars` for highly targeted work.
- Never read `source.md` in full merely to summarize or search it.
- Keep search results bounded with `--top` and `--snippet-chars`.
- Do not install packages, download OCR models, call an API, or enable LLM-assisted OCR without user approval.
- Preserve originals and write only inside the chosen output directory.
- Report skipped files and missing dependencies by path, without dumping their contents.

## Typical requests

- "把这些 PDF 和 EPUB 整理成 Codex 能按章节检索的资料库。"
- "尽量节省额度，只查这些书里关于现金流折现的内容。"
- "Convert this Word/Excel folder to compact Markdown and retrieve only relevant passages."
