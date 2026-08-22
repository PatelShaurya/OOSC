"""
Supabase pgvector client integration for chunk and embedding upserts.
"""
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class SupabaseVectorStore:
    """
    Manages vector database operations for document chunks with 1024-dimensional BGE-M3 embeddings.
    """

    TABLE_NAME = "document_chunks"

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.url = supabase_url or os.getenv("SUPABASE_URL")
        self.key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            print("Warning: SUPABASE_URL or SUPABASE_SERVICE_KEY missing. Database client uninitialized.")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(self.url, self.key)

    def is_connected(self) -> bool:
        return self.client is not None

    def prepare_chunk_record(self, chunk: Dict[str, Any], embedding: List[float]) -> Dict[str, Any]:
        """Formats chunk dict + embedding list into database table schema record."""
        return {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "content": chunk["text"],
            "embedding": embedding,
            "document_title": chunk.get("document_title"),
            "document_type": chunk.get("document_type"),
            "issuing_authority": chunk.get("issuing_authority"),
            "source_url": chunk.get("source_url"),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "chapter": chunk.get("chapter"),
            "section": chunk.get("section"),
            "parent_section": chunk.get("parent_section"),
            "subsection": chunk.get("subsection"),
            "chunk_index": chunk.get("chunk_index"),
        }

    def upsert_chunks(self, records: List[Dict[str, Any]], batch_size: int = 50) -> int:
        """
        Upserts chunk records with embeddings to Supabase using (document_id, chunk_id) conflict handling.
        Returns the total number of records successfully upserted.
        """
        if not self.client:
            raise RuntimeError("Supabase client is not initialized. Check your SUPABASE_URL and SUPABASE_SERVICE_KEY.")

        if not records:
            return 0

        upserted_count = 0
        for i in range(0, len(records), batch_size):
            batch = records[i: i + batch_size]
            response = self.client.table(self.TABLE_NAME).upsert(
                batch,
                on_conflict="document_id,chunk_id"
            ).execute()

            if hasattr(response, "data") and response.data:
                upserted_count += len(response.data)
            else:
                upserted_count += len(batch)

        return upserted_count
