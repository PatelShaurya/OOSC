"""
Evaluation runner for Stage 4B semantic retrieval benchmark.
Measures Recall@1, Recall@3, Recall@5, and similarity metrics against benchmark test questions.
"""
import json
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.retrieval.retriever import SemanticRetriever


def is_section_match(retrieved_sec: str, expected_sec: str) -> bool:
    """
    Normalizes and checks if a retrieved section matches an expected section.
    E.g. 'Section 39' matches 'Section 39', 'Section 2(9)' matches 'Section 2'.
    """
    if not retrieved_sec:
        return False
    ret_clean = retrieved_sec.lower().strip()
    exp_clean = expected_sec.lower().strip()
    return exp_clean in ret_clean or ret_clean in exp_clean


def run_evaluation(questions_path: Path):
    if not questions_path.exists():
        print(f"Error: Evaluation file not found at {questions_path}")
        sys.exit(1)

    with open(questions_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    retriever = SemanticRetriever()
    total_q = len(test_cases)
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    top_1_sims = []
    top_5_sims = []
    successful_queries = 0
    failed_queries = 0

    per_q_results = []

    print("\nExecuting CivicAI Semantic Retrieval Evaluation Benchmark...\n")

    for tc in test_cases:
        qid = tc["id"]
        q_text = tc["question"]
        expected_secs = tc.get("expected_sections", [])

        try:
            res = retriever.retrieve(query=q_text, top_k=5)
            successful_queries += 1
        except Exception as exc:
            failed_queries += 1
            print(f"Error evaluating query {qid}: {exc}")
            continue

        top_results = res.results
        retrieved_secs = [r.section or r.parent_section or "N/A" for r in top_results]

        if top_results:
            top_1_sims.append(top_results[0].similarity_score)
            top_5_sims.extend([r.similarity_score for r in top_results])

        # Check recall at 1, 3, 5
        h1 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in retrieved_secs[:1])
        h3 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in retrieved_secs[:3])
        h5 = any(any(is_section_match(ret, exp) for exp in expected_secs) for ret in retrieved_secs[:5])

        if h1:
            hits_at_1 += 1
        if h3:
            hits_at_3 += 1
        if h5:
            hits_at_5 += 1

        per_q_results.append({
            "id": qid,
            "question": q_text,
            "expected": expected_secs,
            "retrieved": retrieved_secs,
            "pass_at_5": h5
        })

    # Summary calculations
    r1 = hits_at_1 / total_q if total_q > 0 else 0.0
    r3 = hits_at_3 / total_q if total_q > 0 else 0.0
    r5 = hits_at_5 / total_q if total_q > 0 else 0.0
    avg_top1_sim = sum(top_1_sims) / len(top_1_sims) if top_1_sims else 0.0
    avg_top5_sim = sum(top_5_sims) / len(top_5_sims) if top_5_sims else 0.0

    print("=" * 50)
    print("CivicAI Retrieval Evaluation Report")
    print("=" * 50)
    print(f"Questions evaluated: {total_q}")
    print(f"Successful queries: {successful_queries}")
    print(f"Failed queries:     {failed_queries}\n")

    print(f"Recall@1: {r1:.4f} ({hits_at_1}/{total_q})")
    print(f"Recall@3: {r3:.4f} ({hits_at_3}/{total_q})")
    print(f"Recall@5: {r5:.4f} ({hits_at_5}/{total_q})\n")

    print(f"Average Top-1 Similarity: {avg_top1_sim:.4f}")
    print(f"Average Top-5 Similarity: {avg_top5_sim:.4f}")
    print("=" * 50 + "\n")

    print("Per-Question Results:")
    print("-" * 50)
    for q_res in per_q_results:
        exp_str = ", ".join(q_res["expected"])
        status = "PASS" if q_res["pass_at_5"] else "FAIL"
        print(f"\n{q_res['id'].upper()}")
        print(f"Question: {q_res['question']}")
        print(f"Expected: {exp_str}")
        print("Top 5:")
        for idx, sec in enumerate(q_res["retrieved"], 1):
            is_match = any(is_section_match(sec, exp) for exp in q_res["expected"])
            check_str = " ✓" if is_match else ""
            print(f"  {idx}. {sec:<20}{check_str}")
        print(f"Recall@5 Status: {status}")
        print("-" * 50)


def main():
    q_file = Path(__file__).resolve().parent / "retrieval_questions.json"
    run_evaluation(q_file)


if __name__ == "__main__":
    main()
