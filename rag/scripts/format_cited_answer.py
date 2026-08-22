"""
CLI tool for end-to-end testing of Stage 5B Citation Mapping & Formatting.
Flow: User Query -> RerankedRetriever (4C) -> Generator (5A) -> CitationMapper (5B) -> CitationFormatter (5B)
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.citations.formatter import CitationFormatter
from rag.app.citations.mapper import CitationMapper
from rag.app.generation.generator import Generator
from rag.app.reranking.reranker import RerankedRetriever


def main():
    parser = argparse.ArgumentParser(description="Stage 5B Citation Mapping and Formatting CLI Tool.")
    parser.add_argument("--query", type=str, required=True, help="User natural-language question")
    parser.add_argument("--candidate-k", type=int, default=10, help="Candidate chunks retrieved (default: 10)")
    parser.add_argument("--top-k", type=int, default=5, help="Reranked context chunks passed to generator (default: 5)")
    parser.add_argument("--json", action="store_true", help="Print output as JSON")
    args = parser.parse_args()

    # 1. Two-stage retrieval (Stage 4C)
    retriever = RerankedRetriever()
    reranked_resp = retriever.retrieve(query=args.query, candidate_k=args.candidate_k, top_k=args.top_k)

    # 2. Grounded generation (Stage 5A)
    generator = Generator()
    gen_resp = generator.generate(question=args.query, retrieved_results=reranked_resp.results)

    # 3. Citation mapping (Stage 5B)
    mapper = CitationMapper()
    cited_resp = mapper.create_cited_response(
        generation_response=gen_resp,
        retrieval_results=reranked_resp.results
    )

    # 4. Formatting output
    if args.json:
        print(json.dumps(cited_resp.model_dump(), indent=2, ensure_ascii=False))
    else:
        formatter = CitationFormatter()
        print(f"\nQuestion: {args.query}\n")
        print(formatter.format_cited_answer(cited_resp))


if __name__ == "__main__":
    main()
