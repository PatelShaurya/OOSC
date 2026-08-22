import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag.app.reranking.reranker import RerankedRetriever

def run_tests():
    retriever = RerankedRetriever()

    print("\n" + "="*80)
    print("PART 1: PM KISAN RETRIEVAL RELEVANCE TEST")
    print("="*80 + "\n")

    pm_kisan_queries = [
        "Who is eligible for PM Kisan scheme?",
        "What benefits does PM Kisan provide?",
        "How can an eligible farmer apply?",
        "What documents are required?",
        "Who is not eligible for the scheme?"
    ]

    for i, q in enumerate(pm_kisan_queries, 1):
        res = retriever.retrieve(query=q, candidate_k=10, top_k=5)
        print(f"[{i}] QUERY: \"{q}\"")
        print(f"    Top Chunks Retrieved: {len(res.results)}")
        for rank, r in enumerate(res.results, 1):
            clean_snippet = " ".join(r.text.split())[:130]
            print(f"    Rank {rank} | Chunk: {r.chunk_id} | Rerank Score: {r.rerank_score:.4f} (Sim: {r.similarity_score:.4f})")
            print(f"      Doc: {r.document_title} (ID: {r.document_id})")
            print(f"      Sec: {r.section} | Pages: {r.page_start}-{r.page_end}")
            print(f"      Snippet: {clean_snippet}...\n")
        print("-" * 80 + "\n")

    print("\n" + "="*80)
    print("PART 2: CROSS-DOCUMENT SEPARATION TEST")
    print("="*80 + "\n")

    cross_doc_queries = [
        ("What rights does a consumer have?", "Consumer Protection Act"),
        ("Who is eligible for PM Kisan?", "PM Kissan FAQ"),
        ("What can a consumer do about a defective product?", "Consumer Protection Act")
    ]

    for i, (q, expected) in enumerate(cross_doc_queries, 1):
        res = retriever.retrieve(query=q, candidate_k=10, top_k=5)
        top_doc = res.results[0] if res.results else None
        top_title = top_doc.document_title if top_doc else "None"
        top_doc_id = top_doc.document_id if top_doc else "None"
        
        is_match = (expected.lower() in top_title.lower()) or (expected.lower().replace(" ", "_") in top_doc_id.lower())
        status_str = "YES [PASSED]" if is_match else "NO [FAILED]"
        
        print(f"[{i}] QUERY: \"{q}\"")
        print(f"    Expected Document : {expected}")
        print(f"    Top Retrieved Doc : {top_title} (ID: {top_doc_id})")
        if top_doc:
            print(f"    Rerank Score      : {top_doc.rerank_score:.4f}")
        print(f"    Match Verified    : {status_str}")
        print(f"    Top 3 Docs        : {[r.document_title for r in res.results[:3]]}")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    run_tests()
