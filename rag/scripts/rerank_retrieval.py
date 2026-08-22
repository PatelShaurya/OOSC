"""
CLI tool for testing Stage 4C Two-Stage Retrieval (Semantic Candidate Search + Cross-Encoder Reranking).
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.reranking.reranker import RerankedRetriever


def format_cli_output(response):
    print("\n" + "=" * 60)
    print("Reranked Retrieval")
    print("=" * 60)
    print(f"Query: \"{response.query}\"")
    print(f"Candidate count: {response.candidate_k}")
    print(f"Final results: {response.top_k}")
    print("=" * 60 + "\n")

    if not response.results:
        print("No matching results found.\n")
        return

    for idx, item in enumerate(response.results, 1):
        pages_str = f"{item.page_start}-{item.page_end}" if item.page_start and item.page_end else "N/A"
        sec_str = item.section or "N/A"
        subsec_str = item.subsection or "N/A"
        doc_title = item.document_title or item.document_id
        rerank_str = f"{item.rerank_score:.4f}" if item.rerank_score is not None else "N/A"

        print("-" * 60)
        print(f"Rank {idx}")
        print(f"Semantic similarity: {item.similarity_score:.4f}")
        print(f"Reranker score: {rerank_str}")
        print(f"Document: {doc_title} (ID: {item.document_id})")
        print(f"Section: {sec_str} | Subsection: {subsec_str} | Pages: {pages_str}")
        print(f"Chunk ID: {item.chunk_id}")
        print("Text:")
        print(item.text.strip())
        print("-" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Stage 4C Two-Stage Semantic Retrieval & Cross-Encoder Reranking CLI.")
    parser.add_argument("--query", type=str, required=True, help="User natural-language query")
    parser.add_argument("--candidate-k", type=int, default=10, help="Number of candidate chunks to retrieve initially")
    parser.add_argument("--top-k", type=int, default=5, help="Number of final top reranked chunks to return")
    parser.add_argument("--document-id", type=str, default=None, help="Filter by document ID")
    parser.add_argument("--document-type", type=str, default=None, help="Filter by document type (e.g. law, scheme)")
    parser.add_argument("--issuing-authority", type=str, default=None, help="Filter by issuing authority")
    parser.add_argument("--json", action="store_true", help="Print response as JSON")
    args = parser.parse_args()

    pipeline = RerankedRetriever()
    response = pipeline.retrieve(
        query=args.query,
        candidate_k=args.candidate_k,
        top_k=args.top_k,
        document_id=args.document_id,
        document_type=args.document_type,
        issuing_authority=args.issuing_authority
    )

    if args.json:
        print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
    else:
        format_cli_output(response)


if __name__ == "__main__":
    main()
