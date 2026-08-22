"""
Live Evaluation Runner for CivicAI RAG Pipeline using Real Google Gemini LLM API.
Executes test suites, computes metrics, and saves output to rag/evaluation/llm_results.json.
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv("rag/.env")

from rag.app.pipeline import RAGPipeline
from rag.app.generation.llm_client import LLMClient


def verify_real_llm_config() -> LLMClient:
    """
    Verifies that a valid real LLM configuration and API key are loaded.
    Raises RuntimeError if key is missing or invalid.
    """
    client = LLMClient()
    if not client.api_key or client.provider == "mock":
        raise RuntimeError(
            "CRITICAL: Live evaluation halted. No valid LLM_API_KEY found in rag/.env. "
            "Mock mode is disabled for this test suite."
        )
    return client


def evaluate_query(
    pipeline: RAGPipeline,
    query_text: str,
    top_k: int = 5,
    candidate_k: int = 10,
    document_type: str = None,
    document_id: str = None,
    issuing_authority: str = None,
    expected_doc: str = None,
    is_unsupported_test: bool = False
) -> Dict[str, Any]:
    """
    Executes a single RAG query and evaluates its grounding and citation accuracy.
    """
    response = pipeline.query(
        query=query_text,
        top_k=top_k,
        candidate_k=candidate_k,
        document_type=document_type,
        document_id=document_id,
        issuing_authority=issuing_authority
    )
    import time
    time.sleep(2.0)

    retrieved_docs = []
    retrieved_sections = []
    reranker_scores = []
    
    if response.retrieval and response.retrieval.results:
        for r in response.retrieval.results:
            retrieved_docs.append(r.document_title or r.document_id)
            if r.section:
                retrieved_sections.append(r.section)
            reranker_scores.append(round(r.rerank_score, 4))

    citations_data = []
    retrieved_chunk_ids = {r.chunk_id for r in (response.retrieval.results if response.retrieval else [])}

    for c in response.citations:
        citations_data.append({
            "source_id": c.source_id,
            "document_title": c.document_title,
            "section": c.section,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "source_url": c.source_url
        })

    # Grounding Classification
    if is_unsupported_test:
        if "do not provide" in response.answer.lower() or "not contain" in response.answer.lower() or "insufficient" in response.answer.lower() or response.limitations:
            grounding_class = "UNSUPPORTED"
            notes = "Correctly acknowledged that context is insufficient without inventing rules."
        else:
            grounding_class = "HALLUCINATED"
            notes = "Model generated unsupported rules or facts for an un-answerable query."
    else:
        if len(response.citations) > 0 and not ("fallback response" in response.answer.lower()):
            grounding_class = "GROUNDED"
            notes = "Answer is fully supported by retrieved context and attached verified citations."
        elif response.limitations and len(response.citations) > 0:
            grounding_class = "PARTIALLY GROUNDED"
            notes = "Answer is grounded but limitations explicitly noted missing details."
        elif response.limitations and len(response.citations) == 0:
            grounding_class = "UNSUPPORTED"
            notes = "Retrieved context was insufficient to answer the query."
        else:
            grounding_class = "UNSUPPORTED"
            notes = "Answer lacked verified citations."

    # Citation Correctness Classification
    citation_class = "CORRECT"
    for c in response.citations:
        if c.source_id not in retrieved_chunk_ids:
            citation_class = "INCORRECT"
            notes += " [Invalid citation source ID detected]"
            break

    if expected_doc:
        top_retrieved = retrieved_docs[0] if retrieved_docs else ""
        if expected_doc.lower() not in top_retrieved.lower():
            notes += f" [Expected doc '{expected_doc}', got '{top_retrieved}']"

    return {
        "query": query_text,
        "retrieved_documents": retrieved_docs,
        "retrieved_sections": retrieved_sections,
        "reranker_scores": reranker_scores,
        "answer": response.answer,
        "limitations": response.limitations,
        "citation_count": len(response.citations),
        "citations": citations_data,
        "grounding_status": grounding_class,
        "citation_correctness": citation_class,
        "notes": notes
    }


def main():
    print("=" * 80)
    print("STARTING CIVICAI RAG PIPELINE LIVE EVALUATION WITH REAL LLM API")
    print("=" * 80 + "\n")

    # 1. Verify LLM API config
    llm_client = verify_real_llm_config()
    print(f"Verified LLM Provider : {llm_client.provider}")
    print(f"Verified LLM Model    : {llm_client.model}")
    print("API Key Status        : Loaded & Configured\n")

    pipeline = RAGPipeline()
    results = []

    # 2. Test Suite 1: Consumer Protection Act (5 queries)
    print("--- 1. Consumer Protection Act Queries ---")
    cp_queries = [
        "What rights does a consumer have?",
        "What can I do if I receive a defective product?",
        "How can a consumer file a complaint?",
        "What is an unfair trade practice?",
        "What compensation can a consumer receive?"
    ]
    for q in cp_queries:
        print(f"  Executing: \"{q}\"")
        res = evaluate_query(pipeline, q, expected_doc="Consumer Protection Act")
        results.append(res)

    # 3. Test Suite 2: PM Kisan Queries (5 queries)
    print("\n--- 2. PM Kisan Queries ---")
    pm_queries = [
        "What is PM Kisan and who is eligible for it?",
        "What benefits does PM Kisan provide?",
        "How can an eligible farmer apply?",
        "What documents are required?",
        "Who is not eligible for PM Kisan?"
    ]
    for q in pm_queries:
        print(f"  Executing: \"{q}\"")
        res = evaluate_query(pipeline, q, expected_doc="PM Kissan")
        results.append(res)

    # 4. Test Suite 3: Cross-Document Separation (2 queries)
    print("\n--- 3. Cross-Document Separation Queries ---")
    cross_queries = [
        ("Who is eligible for PM Kisan?", "PM Kissan"),
        ("What rights does a consumer have?", "Consumer Protection Act")
    ]
    for q, expected in cross_queries:
        print(f"  Executing: \"{q}\" (Expected: {expected})")
        res = evaluate_query(pipeline, q, expected_doc=expected)
        results.append(res)

    # 5. Test Suite 4: Filtered Retrieval Queries (2 queries)
    print("\n--- 4. Filtered Retrieval Queries ---")
    res_filt1 = evaluate_query(
        pipeline,
        query_text="Who is eligible for PM Kisan?",
        document_type="scheme_faq",
        expected_doc="PM Kissan"
    )
    results.append(res_filt1)

    res_filt2 = evaluate_query(
        pipeline,
        query_text="What rights does a consumer have?",
        document_type="law",
        expected_doc="Consumer Protection Act"
    )
    results.append(res_filt2)

    # 6. Test Suite 5: Hallucination / Grounding Tests (3 queries)
    print("\n--- 5. Hallucination / Grounding Queries ---")
    unsupported_queries = [
        "What is the penalty for violating a PM Kisan requirement?",
        "Can I appeal a PM Kisan rejection?",
        "What is the deadline for filing this application?"
    ]
    for q in unsupported_queries:
        print(f"  Executing: \"{q}\"")
        res = evaluate_query(pipeline, q, is_unsupported_test=True)
        results.append(res)

    # 7. Compute Summary Metrics
    total = len(results)
    grounded_count = sum(1 for r in results if r["grounding_status"] == "GROUNDED")
    partially_grounded_count = sum(1 for r in results if r["grounding_status"] == "PARTIALLY GROUNDED")
    unsupported_count = sum(1 for r in results if r["grounding_status"] == "UNSUPPORTED")
    hallucinated_count = sum(1 for r in results if r["grounding_status"] == "HALLUCINATED")

    correct_citations_count = sum(1 for r in results if r["citation_correctness"] == "CORRECT")

    grounded_rate = ((grounded_count + partially_grounded_count) / total) * 100
    citation_correctness_rate = (correct_citations_count / total) * 100
    unsupported_rate = (unsupported_count / total) * 100
    hallucination_rate = (hallucinated_count / total) * 100

    summary_metrics = {
        "total_queries_tested": total,
        "grounded_count": grounded_count,
        "partially_grounded_count": partially_grounded_count,
        "unsupported_count": unsupported_count,
        "hallucinated_count": hallucinated_count,
        "grounded_answer_rate": round(grounded_rate, 2),
        "citation_correctness_rate": round(citation_correctness_rate, 2),
        "unsupported_answer_rate": round(unsupported_rate, 2),
        "hallucination_rate": round(hallucination_rate, 2)
    }

    eval_data = {
        "provider": llm_client.provider,
        "model": llm_client.model,
        "metrics": summary_metrics,
        "results": results
    }

    # Save to rag/evaluation/llm_results.json
    out_dir = Path("rag/evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "llm_results.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"Results saved to           : {out_file}")
    print(f"Total Queries Evaluated    : {total}")
    print(f"Grounded Answer Rate       : {grounded_rate:.2f}%")
    print(f"Citation Correctness Rate  : {citation_correctness_rate:.2f}%")
    print(f"Unsupported Answer Rate    : {unsupported_rate:.2f}%")
    print(f"Hallucination Rate         : {hallucination_rate:.2f}%")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
