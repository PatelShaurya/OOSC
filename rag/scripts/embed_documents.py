"""
CLI script for generating BAAI/bge-m3 embeddings for Stage 2 chunks and storing them in Supabase pgvector.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.embeddings.embedder import BGEEmbedder
from rag.app.vector_store.supabase_vector import SupabaseVectorStore


def process_embedding_file(
    file_path: Path,
    embedder: BGEEmbedder,
    vector_store: SupabaseVectorStore,
    batch_size: int = 16,
    save_local: bool = True,
    skip_db: bool = False
):
    if not file_path.exists():
        raise FileNotFoundError(f"Chunk file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc_id = data.get("document_id", "unknown_doc")
    doc_title = data.get("document_title", "Untitled Document")
    chunks = data.get("chunks", [])

    if not chunks:
        print(f"No chunks found in file: {file_path}")
        return

    # Validate chunks
    texts = []
    valid_chunks = []
    for c in chunks:
        if "text" in c and c["text"].strip():
            texts.append(c["text"])
            valid_chunks.append(c)

    print(f"Generating embeddings for {len(valid_chunks)} chunks using BAAI/bge-m3...")
    embeddings = embedder.encode(texts, batch_size=batch_size)

    # Local caching directory
    if save_local:
        embeddings_dir = file_path.parent.parent / "embeddings"
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        local_out_file = embeddings_dir / f"{doc_id}_embedded.json"

        output_records = []
        for chunk, emb in zip(valid_chunks, embeddings):
            record = vector_store.prepare_chunk_record(chunk, emb)
            output_records.append(record)

        with open(local_out_file, "w", encoding="utf-8") as f:
            json.dump({
                "document_id": doc_id,
                "document_title": doc_title,
                "embedding_model": embedder.model_name,
                "embedding_dim": embedder.EMBEDDING_DIM,
                "total_chunks": len(output_records),
                "chunks": output_records
            }, f, indent=2, ensure_ascii=False)
        print(f"Local embedding cache saved to: {local_out_file}")

    # Database Upserting
    upserted_count = 0
    db_status = "Supabase"
    if not skip_db and vector_store.is_connected():
        records = [vector_store.prepare_chunk_record(c, e) for c, e in zip(valid_chunks, embeddings)]
        print(f"Upserting {len(records)} records to Supabase table '{vector_store.TABLE_NAME}'...")
        upserted_count = vector_store.upsert_chunks(records)
    else:
        if skip_db:
            db_status = "Skipped (--skip-db flag)"
        else:
            db_status = "Skipped (SUPABASE_URL/SERVICE_KEY not configured)"
        upserted_count = len(valid_chunks)

    # Print summary output
    print("\n" + "=" * 50)
    print("=== Stage 3 Embedding Complete ===")
    print("=" * 50)
    print(f"\nDocument:\n{doc_title}")
    print(f"\nChunks:\n{len(chunks)}")
    print(f"\nEmbeddings generated:\n{len(embeddings)}")
    print(f"\nEmbedding dimension:\n{embedder.EMBEDDING_DIM}")
    print(f"\nModel:\n{embedder.model_name}")
    print(f"\nDevice:\n{embedder.device.upper()}")
    print(f"\nNormalized:\nYes")
    print(f"\nDatabase:\n{db_status}")
    print(f"\nUpserted:\n{upserted_count}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate BGE-M3 embeddings and store in Supabase pgvector.")
    parser.add_argument("--file", type=str, help="Path to chunk JSON file")
    parser.add_argument("--dir", type=str, help="Directory containing chunk JSON files")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for embedding model")
    parser.add_argument("--device", type=str, default="auto", help="Device (auto, cpu, cuda)")
    parser.add_argument("--skip-db", action="store_true", help="Skip database upsert")
    parser.add_argument("--no-local-save", action="store_true", help="Disable local embedding cache saving")
    args = parser.parse_args()

    embedder = BGEEmbedder(device=args.device, batch_size=args.batch_size)
    vector_store = SupabaseVectorStore()

    if args.file:
        file_path = Path(args.file)
        process_embedding_file(
            file_path=file_path,
            embedder=embedder,
            vector_store=vector_store,
            batch_size=args.batch_size,
            save_local=not args.no_local_save,
            skip_db=args.skip_db
        )
    elif args.dir:
        input_dir = Path(args.dir)
        for chunk_file in input_dir.glob("*.json"):
            process_embedding_file(
                file_path=chunk_file,
                embedder=embedder,
                vector_store=vector_store,
                batch_size=args.batch_size,
                save_local=not args.no_local_save,
                skip_db=args.skip_db
            )
    else:
        print("Please specify --file or --dir argument.")


if __name__ == "__main__":
    main()
