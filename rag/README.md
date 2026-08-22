# CivicAI RAG Service - Stage 1: Document Ingestion

Stage 1 converts official PDF documents into clean, structured JSON files preserving page-level information for legal and civic citations.

## Features
- **PDF Text Extraction**: Uses PyMuPDF (`fitz`) to extract text page-by-page.
- **Text Cleaning**: Normalizes whitespace and line breaks without altering legal text meaning.
- **Pydantic Validation**: Enforces structured schemas for document metadata and page content.
- **JSON Export**: Output formatted as `rag/data/processed/<document_id>.json`.

## Requirements & Setup

Ensure Python 3.11+ is installed.

```bash
pip install -r rag/requirements.txt
```

## Folder Structure

```
rag/
├── app/
│   └── ingestion/
│       ├── __init__.py
│       ├── loader.py
│       ├── cleaner.py
│       ├── models.py
│       └── pipeline.py
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   └── ingest_documents.py
├── tests/
│   └── test_ingestion.py
├── requirements.txt
└── README.md
```

## Usage

Run document ingestion via CLI:

```bash
python rag/scripts/ingest_documents.py \
  --file rag/data/raw/sample_doc.pdf \
  --document-id doc_001 \
  --title "Consumer Protection Act 2019" \
  --document-type "law" \
  --issuing-authority "Government of India" \
  --source-url "https://example.gov.in/act.pdf"
```

The output JSON will be saved to `rag/data/processed/doc_001.json`.

## Running Tests

Run pytest from the repository root:

```bash
pytest rag/tests
```
