"""
CLI tool for end-to-end testing of Stage 5A Grounded Answer Generation.
Flow: User Query -> RerankedRetriever (Stage 4C) -> Generator (Stage 5A) -> Structured Grounded Answer
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.generation.generator import Generator
from rag.app.reranking.reranker import RerankedRetriever


def format_cli_output(query: str, reranked_response, generation_response):
    print("\n" + "=" * 60)
    print("Grounded Legal Answer Generation (Stage 5A)")
    print("=" * 60)
    print(f"Question:\n{query}\n")

    retrieved_secs = [
        f"{r.section or 'General Chunk'} ({r.document_title or r.document_id})"
        for r in reranked_response.results
    ]
    print("Retrieved Sections:")
    for sec in retrieved_secs:
        print(f"  - {sec}")
    print("\n" + "-" * 60)

    print("Generated Answer:")
    print(generation_response.answer.strip())
    print("\n" + "-" * 60)

    print("Source IDs Used:")
    if generation_response.source_ids:
        for sid in generation_response.source_ids:
            print(f"  - {sid}")
    else:
        print("  - None")

    print("\nLimitations / Missing Information:")
    if generation_response.limitations:
        print(f"  {generation_response.limitations}")
    else:
        print("  None (Answer fully supported by retrieved sources)")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Stage 5A Grounded Answer Generation CLI Tool.")
    parser.add_argument("--query", type=str, required=True, help="User natural-language question")
    parser.add_argument("--candidate-k", type=int, default=10, help="Candidate chunks retrieved (default: 10)")
    parser.add_argument("--top-k", type=int, default=5, help="Reranked context chunks passed to generator (default: 5)")
    parser.add_argument("--json", action="store_true", help="Print response as JSON")
    args = parser.parse_args()

    # 1. Two-stage retrieval
    retriever = RerankedRetriever()
    reranked_resp = retriever.retrieve(query=args.query, candidate_k=args.candidate_k, top_k=args.top_k)

    # 2. Grounded generation
    generator = Generator()
    gen_resp = generator.generate(question=args.query, retrieved_results=reranked_resp.results)

    if args.json:
        out_dict = {
            "query": args.query,
            "retrieved_sections": [r.section for r in reranked_resp.results],
            "generation": gen_resp.model_dump()
        }
        print(json.dumps(out_dict, indent=2, ensure_ascii=False))
    else:
        format_cli_output(args.query, reranked_resp, gen_resp)


if __name__ == "__main__":
    main()
