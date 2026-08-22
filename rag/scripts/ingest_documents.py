"""
CLI script to execute document ingestion on a PDF file.
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path when running script directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rag.app.ingestion.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest PDF document into clean structured JSON.")
    parser.add_argument("--file", required=True, help="Path to input PDF file")
    parser.add_argument("--document-id", required=True, help="Unique document ID")
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument("--source-url", default=None, help="Source URL (optional)")
    parser.add_argument("--document-type", default=None, help="Document type (optional, e.g. law, rule)")
    parser.add_argument("--issuing-authority", default=None, help="Issuing authority (optional)")
    parser.add_argument(
        "--output-dir", default=None, help="Directory to save processed JSON (default: rag/data/processed)"
    )

    args = parser.parse_args()

    pipeline = IngestionPipeline(output_dir=args.output_dir)
    try:
        doc = pipeline.process_document(
            pdf_path=args.file,
            document_id=args.document_id,
            title=args.title,
            source_url=args.source_url,
            document_type=args.document_type,
            issuing_authority=args.issuing_authority,
            save=True,
        )
        print(f"Successfully processed '{doc.metadata.title}' ({len(doc.pages)} pages).")
        output_path = pipeline.output_dir / f"{args.document_id}.json"
        print(f"Saved to: {output_path}")
    except Exception as e:
        print(f"Error during document ingestion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
