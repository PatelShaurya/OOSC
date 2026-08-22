"""
Evaluation runner for Stage 4C Two-Stage Retrieval (Vector Search + Cross-Encoder Reranking).
Compares Recall@1, Recall@3, Recall@5, and ranking changes against the Stage 4B baseline.
"""
import json
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.reranking.reranker import RerankedRetriever
from rag.app.retrieval.retriever import SemanticRetriever
from rag.evaluation.evaluate_retrieval import is_section_match


def run_evaluation():
    q_file = Path(__file__).resolve().parent / "retrieval_questions.json"
    if not q_file.exists():
        print(f"Error: Evaluation file not found at {q_file}")
        sys.exit(1)

    with open(q_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    # Initialize Stage 4B retriever and Stage 4C pipeline
    semantic_retriever = SemanticRetriever()
    pipeline = RerankedRetriever(semantic_retriever=semantic_retriever)

    total_q = len(test_cases)
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0

    stage_4b_h1_count = 0
    improved_count = 0
    unchanged_count = 0
    worsened_count = 0

    cand_sims = []
    rerank_scores = []

    print("\nExecuting Stage 4C Two-Stage Retrieval Evaluation Benchmark (candidate_k=10, top_k=5)...\n")

    per_q_results = []

    for tc in test_cases:
        qid = tc["id"]
        q_text = tc["question"]
        expected_secs = tc.get("expected_sections", [])

        # Stage 4B Baseline (semantic search only)
        base_res = semantic_retriever.retrieve(query=q_text, top_k=5)
        base_retrieved = [r.section or r.parent_section or "N/A" for r in base_res.results]
        base_h1 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in base_retrieved[:1])
        if base_h1:
            stage_4b_h1_count += 1

        # Stage 4C Pipeline (candidate_k=10, top_k=5)
        stage_4c_res = pipeline.retrieve(query=q_text, candidate_k=10, top_k=5)
        reranked_results = stage_4c_res.results
        reranked_retrieved = [r.section or r.parent_section or "N/A" for r in reranked_results]

        if reranked_results:
            cand_sims.extend([r.similarity_score for r in reranked_results])
            rerank_scores.extend([r.rerank_score for r in reranked_results if r.rerank_score is not None])

        # Stage 4C Recall hits
        h1 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in reranked_retrieved[:1])
        h3 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in reranked_retrieved[:3])
        h5 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in reranked_retrieved[:5])

        if h1:
            hits_at_1 += 1
        if h3:
            hits_at_3 += 1
        if h5:
            hits_at_5 += 1

        # Compare Rank 1 movement
        if h1 and not base_h1:
            improved_count += 1
            movement = "IMPROVED (+1)"
        elif not h1 and base_h1:
            worsened_count += 1
            movement = "WORSENED (-1)"
        else:
            unchanged_count += 1
            movement = "UNCHANGED"

        per_q_results.append({
            "id": qid,
            "question": q_text,
            "expected": expected_secs,
            "stage_4b_top1": base_retrieved[0] if base_retrieved else "N/A",
            "stage_4c_top1": reranked_retrieved[0] if reranked_retrieved else "N/A",
            "movement": movement,
            "pass_at_5": h5
        })

    # Summary metrics
    r1 = hits_at_1 / total_q if total_q > 0 else 0.0
    r3 = hits_at_3 / total_q if total_q > 0 else 0.0
    r5 = hits_at_5 / total_q if total_q > 0 else 0.0
    base_r1 = stage_4b_h1_count / total_q if total_q > 0 else 0.0

    avg_cand_sim = sum(cand_sims) / len(cand_sims) if cand_sims else 0.0
    avg_rerank_score = sum(rerank_scores) / len(rerank_scores) if rerank_scores else 0.0

    print("=" * 60)
    print("Stage 4C Two-Stage Retrieval Evaluation Report")
    print("=" * 60)
    print(f"Questions evaluated: {total_q}\n")

    print("Comparison against Stage 4B Baseline:")
    print(f"  Stage 4B Baseline Recall@1: {base_r1:.4f}")
    print(f"  Stage 4C Reranked Recall@1: {r1:.4f}")
    print(f"  Stage 4C Reranked Recall@3: {r3:.4f}")
    print(f"  Stage 4C Reranked Recall@5: {r5:.4f}\n")

    print("Rank-1 Movement Analysis:")
    print(f"  Queries Improved: {improved_count}")
    print(f"  Queries Unchanged: {unchanged_count}")
    print(f"  Queries Worsened:  {worsened_count}\n")

    print(f"Average Candidate Semantic Similarity: {avg_cand_sim:.4f}")
    print(f"Average Top-5 Reranker Score:          {avg_rerank_score:.4f}")
    print("=" * 60 + "\n")

    print("Per-Question Baseline vs Reranked Comparison:")
    print("-" * 60)
    for q_res in per_q_results:
        exp_str = ", ".join(q_res["expected"])
        print(f"{q_res['id'].upper()}: {q_res['question']}")
        print(f"  Expected:       {exp_str}")
        print(f"  Stage 4B Rank1: {q_res['stage_4b_top1']}")
        print(f"  Stage 4C Rank1: {q_res['stage_4c_top1']}  [{q_res['movement']}]")
        print("-" * 60)


if __name__ == "__main__":
    run_evaluation()
