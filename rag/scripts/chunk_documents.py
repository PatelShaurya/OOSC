"""
CLI tool for chunking Stage 1 processed document JSON into Stage 2 structured chunks.
Prints detailed metrics about chunking performance, page spans, and section metadata.
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.chunking.chunker import StructureAwareChunker
from rag.app.chunking.config import DEFAULT_CHUNKING_CONFIG


def process_file(file_path: Path, output_dir: Path) -> Path:
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunker = StructureAwareChunker(config=DEFAULT_CHUNKING_CONFIG)
    output_model = chunker.chunk_document(data)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{output_model.document_id}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_model.model_dump(), f, indent=2, ensure_ascii=False)

    return out_file


def print_chunk_stats(out_file: Path):
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_pages = data.get("total_pages", 0)
    chunks = data.get("chunks", [])
    total_chunks = len(chunks)

    if not chunks:
        print("No chunks generated.")
        return

    word_counts = [len(c["text"].split()) for c in chunks]
    multi_page_chunks = [c for c in chunks if c["page_start"] != c["page_end"]]

    min_size = min(word_counts)
    max_size = max(word_counts)
    avg_size = sum(word_counts) / total_chunks

    print("\n" + "=" * 50)
    print("=== Stage 2 Legal Chunking Statistics ===")
    print("=" * 50)
    print(f"Document ID       : {data.get('document_id')}")
    print(f"Document Title    : {data.get('document_title')}")
    print(f"Total Pages       : {total_pages}")
    print(f"Total Chunks      : {total_chunks}")
    print(f"Multi-page Chunks : {len(multi_page_chunks)} (chunks spanning multiple PDF pages)")
    print(f"Min Chunk Size    : {min_size} words")
    print(f"Max Chunk Size    : {max_size} words")
    print(f"Avg Chunk Size    : {avg_size:.1f} words")
    print(f"Output File Path  : {out_file}")
    print("=" * 50)

    print("\n--- Examples of Chunks Spanning Multiple Pages ---")
    for c in multi_page_chunks[:3]:
        print(f"\n• Chunk ID: {c['chunk_id']}")
        print(f"  Pages   : {c['page_start']} -> {c['page_end']}")
        print(f"  Chapter : {c.get('chapter')}")
        print(f"  Section : {c.get('section')}")
        print(f"  Parent  : {c.get('parent_section')}")
        print(f"  Sub     : {c.get('subsection')}")
        print(f"  Snippet : {c['text'][:140]}...")

    print("\n--- Examples Showing Section / Subsection Metadata ---")
    for c in chunks:
        if c.get("section") and c.get("subsection"):
            print(f"\n• Chunk ID: {c['chunk_id']}")
            print(f"  Pages   : {c['page_start']} -> {c['page_end']}")
            print(f"  Chapter : {c.get('chapter')}")
            print(f"  Section : {c.get('section')}")
            print(f"  Parent  : {c.get('parent_section')}")
            print(f"  Sub     : {c.get('subsection')}")
            print(f"  Snippet : {c['text'][:140]}...")
            break
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Chunk processed legal JSON documents for CivicAI RAG.")
    parser.add_argument("--file", type=str, help="Single file path to process")
    parser.add_argument("--dir", type=str, help="Directory containing JSON files to process")
    parser.add_argument("--outdir", type=str, default="rag/data/processed/chunks", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.outdir)

    if args.file:
        file_path = Path(args.file)
        out_file = process_file(file_path, out_dir)
        print_chunk_stats(out_file)
    elif args.dir:
        input_dir = Path(args.dir)
        for json_file in input_dir.glob("*.json"):
            out_file = process_file(json_file, out_dir)
            print_chunk_stats(out_file)
    else:
        print("Please specify --file or --dir")


if __name__ == "__main__":
    main()
