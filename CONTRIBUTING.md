# Contributing

Thank you for improving Codex Document Prep. Small, focused pull requests are easiest to review.

## Good contributions

- Reproducible fixes for document conversion or chunking
- Support for additional local converters or file variants
- Retrieval improvements that keep output bounded
- Cross-platform fixes for macOS, Linux, or Windows
- Tests using small synthetic fixtures that contain no private documents
- Documentation corrections and clearer examples

## Development setup

The baseline test suite uses only Python's standard library.

```bash
python3 -m py_compile skills/codex-document-prep/scripts/*.py
python3 tests/test_smoke.py
```

Optional converters such as MarkItDown, Pandoc, Poppler, and Calibre are not required for the baseline suite. State which optional tools and versions you used when a change depends on them.

## Pull requests

1. Open an issue first for large behavioral changes.
2. Keep changes local-first and preserve the bounded-output safeguards.
3. Add or update tests for behavior changes.
4. Do not commit copyrighted books, confidential documents, credentials, or generated preparation directories.
5. Explain the user impact, validation performed, and any new dependency.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
