"""
Semantic retriever component supporting BGE-M3 embeddings, Supabase pgvector cosine similarity search,
and optional metadata filtering (document_id, document_type, issuing_authority).
"""
import glob
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np

from rag.app.embeddings.embedder import BGEEmbedder
from rag.app.retrieval.models import RetrievalResult, RetrievalResponse
from rag.app.vector_store.supabase_vector import SupabaseVectorStore


class SemanticRetriever:
    """
    Executes semantic vector similarity search against Supabase pgvector table `document_chunks`.
    Supports optional database-side metadata filtering by `document_id`, `document_type`, and `issuing_authority`.
    Uses BGE-M3 (1024 dimensions, L2 normalized) for query embedding generation.
    """

    def __init__(
        self,
        embedder: Optional[BGEEmbedder] = None,
        vector_store: Optional[SupabaseVectorStore] = None
    ):
        self.embedder = embedder or BGEEmbedder()
        self.vector_store = vector_store or SupabaseVectorStore()

    def _local_search_fallback(
        self,
        query_embedding: List[float],
        top_k: int,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        issuing_authority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback search using local embedding JSON files if database connection is uninitialized.
        Applies optional metadata filtering and computes cosine similarity locally.
        """
        embeddings_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "embeddings"
        json_files = list(embeddings_dir.glob("*.json"))

        if not json_files:
            return []

        all_matches = []
        q_vec = np.array(query_embedding, dtype=np.float32)

        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chunks = data.get("chunks", [])
                for chunk in chunks:
                    # Apply optional metadata filters locally
                    if document_id and chunk.get("document_id") != document_id:
                        continue
                    if document_type and chunk.get("document_type") != document_type:
                        continue
                    if issuing_authority and chunk.get("issuing_authority") != issuing_authority:
                        continue

                    emb = chunk.get("embedding")
                    if not emb or len(emb) != 1024:
                        continue
                    d_vec = np.array(emb, dtype=np.float32)
                    sim = float(np.dot(q_vec, d_vec))
                    record = dict(chunk)
                    record["similarity_score"] = sim
                    all_matches.append(record)
            except Exception as e:
                print(f"Warning reading local embedding file {jf}: {e}")

        all_matches.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
        return all_matches[:top_k]

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        issuing_authority: Optional[str] = None
    ) -> RetrievalResponse:
        """
        Retrieves top-K most relevant legal document chunks with optional metadata filtering.

        Args:
            query: Natural language user question.
            top_k: Number of top relevant chunks to return (default: 5).
            document_id: Optional exact match filter for document ID.
            document_type: Optional exact match filter for document type (e.g. 'law', 'scheme').
            issuing_authority: Optional exact match filter for issuing authority (e.g. 'Government of India').

        Returns:
            RetrievalResponse object containing query string, top_k, and sorted RetrievalResult items.
        """
        top_k = max(1, top_k)
        clean_query = query.strip() if query else ""

        if not clean_query:
            return RetrievalResponse(query=query, top_k=top_k, results=[])

        # Generate L2-normalized 1024-dimensional query embedding
        query_embedding = self.embedder.encode_single(clean_query)

        raw_results: List[Dict[str, Any]] = []

        # Query Supabase database with RPC function supporting metadata filtering
        if self.vector_store.is_connected() and self.vector_store.client is not None:
            try:
                rpc_params = {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                    "filter_document_id": document_id,
                    "filter_document_type": document_type,
                    "filter_issuing_authority": issuing_authority
                }
                rpc_res = self.vector_store.client.rpc("match_document_chunks", rpc_params).execute()

                if hasattr(rpc_res, "data") and rpc_res.data is not None:
                    raw_results = rpc_res.data
                else:
                    raw_results = self._local_search_fallback(
                        query_embedding, top_k, document_id, document_type, issuing_authority
                    )
            except Exception as exc:
                print(f"Warning: Supabase RPC error ({exc}). Using local vector search fallback.")
                raw_results = self._local_search_fallback(
                    query_embedding, top_k, document_id, document_type, issuing_authority
                )
        else:
            raw_results = self._local_search_fallback(
                query_embedding, top_k, document_id, document_type, issuing_authority
            )

        # Construct RetrievalResult objects preserving all chunk metadata
        retrieval_results: List[RetrievalResult] = []

        for r in raw_results:
            text_content = r.get("content") or r.get("text") or ""
            score = float(r.get("similarity_score", 0.0))

            res_obj = RetrievalResult(
                chunk_id=r.get("chunk_id", "unknown_chunk"),
                document_id=r.get("document_id", "unknown_doc"),
                document_title=r.get("document_title"),
                document_type=r.get("document_type"),
                issuing_authority=r.get("issuing_authority"),
                source_url=r.get("source_url"),
                page_start=r.get("page_start"),
                page_end=r.get("page_end"),
                chapter=r.get("chapter"),
                section=r.get("section"),
                parent_section=r.get("parent_section"),
                subsection=r.get("subsection"),
                chunk_index=r.get("chunk_index"),
                text=text_content,
                similarity_score=round(score, 4)
            )
            retrieval_results.append(res_obj)

        retrieval_results.sort(key=lambda x: x.similarity_score, reverse=True)

        return RetrievalResponse(
            query=clean_query,
            top_k=top_k,
            results=retrieval_results
        )
