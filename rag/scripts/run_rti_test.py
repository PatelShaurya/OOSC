"""
RTI Act Test Suite Runner for CivicAI RAG Pipeline.
Executes 5 target RTI questions through RAGPipeline and displays full grounded answers, limitations, and citations.
"""
import sys
import time
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv("rag/.env")

from rag.app.pipeline import RAGPipeline


def main():
    pipeline = RAGPipeline()

    questions = [
        ("Q1", "What is the right to information under the RTI Act?"),
        ("Q2", "How can I file an RTI application?"),
        ("Q3", "How long does a public authority have to respond to an RTI request?"),
        ("Q4", "What information can be exempted from disclosure under the RTI Act?"),
        ("Q5", "What can I do if my RTI request is rejected?")
    ]

    print("\n" + "=" * 80)
    print("RUNNING RTI ACT (2005) END-TO-END RAG PIPELINE EVALUATION")
    print("=" * 80 + "\n")

    for code, q in questions:
        print(f"[{code}] Query: \"{q}\"")
        res = pipeline.query(query=q, top_k=5, candidate_k=10, document_type="law")
        time.sleep(2.0)  # Pacing to avoid API rate limits

        print("-" * 80)
        print("ANSWER:")
        print(res.answer)
        if res.limitations:
            print("\nLIMITATIONS:")
            print(res.limitations)
        print("\nCITATIONS:")
        if res.citations:
            for c in res.citations:
                print(f"  • [{c.source_id}] {c.document_title} | {c.section} | Pages: {c.page_start}-{c.page_end}")
        else:
            print("  (No verified citations returned)")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
