"""
Standalone verification script to run live RTI drafting queries directly.
"""
import json
import asyncio
from dotenv import load_dotenv

load_dotenv("rag/.env")
load_dotenv(".env")

from app.integrations.rag_client import RAGClient

async def run_live_test():
    client = RAGClient(base_url="http://127.0.0.1:8000")
    
    print("=" * 80)
    print("RUNNING LIVE RTI DRAFTING AGENT VERIFICATION")
    print("=" * 80 + "\n")

    queries = [
        ("TEST 1: Road Repairs", "I want to know how much money my municipality spent on road repairs in my area.", None, None, "Municipal Corporation"),
        ("TEST 2: Govt Project", "I want copies of records showing expenditure on a government project.", None, None, "Public Works Department"),
        ("TEST 3: Streetlights Ward 5", "I want to know how many streetlights were installed in Ward 5.", "Sunita Verma", "House 42, Ward 5, Delhi", "Municipal Corporation of Delhi"),
        ("TEST 4: Appeal Question", "Can I appeal if my RTI request is rejected?", None, None, None),
        ("TEST 5: Negative Test", "Write an RTI application and tell me the exact PIO name and address.", None, None, None),
    ]

    for name, req, applicant_name, applicant_address, public_authority in queries:
        print(f"[{name}] Query: \"{req}\"")
        resp = await client.draft_rti_application(
            request_text=req,
            applicant_name=applicant_name,
            applicant_address=applicant_address,
            public_authority=public_authority
        )
        print("-" * 80)
        print("ANSWER / DRAFT:")
        print(resp.answer)
        if resp.limitations:
            print("\nLIMITATIONS:")
            print(resp.limitations)
        print("\nCITATIONS:")
        for c in resp.citations:
            doc_title = c.document_title or c.document_id
            print(f"  • [{c.source_id}] {doc_title} | Section: {c.section} | Pages: {c.page_start}-{c.page_end}")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_live_test())
