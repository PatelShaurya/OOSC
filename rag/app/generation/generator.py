"""
Generator module combining ContextBuilder, Grounded Prompts, and LLMClient to produce grounded legal answers.
"""
import json
import re
from typing import List, Optional
from pydantic import ValidationError

from rag.app.generation.context_builder import ContextBuilder
from rag.app.generation.llm_client import LLMClient
from rag.app.generation.models import GenerationResponse
from rag.app.generation.prompts import GROUNDED_SYSTEM_PROMPT, build_user_prompt
from rag.app.retrieval.models import RetrievalResult


class Generator:
    """
    Standalone Grounded Answer Generation Service.
    Receives user question and top reranked context chunks, builds grounded prompts, calls LLM,
    and returns validated structured GenerationResponse objects.
    """

    def __init__(
        self,
        context_builder: Optional[ContextBuilder] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.llm_client = llm_client or LLMClient()

    def _extract_json_payload(self, raw_text: str) -> dict:
        """
        Extracts JSON object dictionary from LLM string output, stripping markdown code blocks if present.
        """
        clean_text = raw_text.strip()
        # Remove ```json ... ``` code fence if present
        if "```" in clean_text:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
            else:
                # Try finding first { and last }
                start_idx = clean_text.find("{")
                end_idx = clean_text.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    clean_text = clean_text[start_idx:end_idx + 1]

        return json.loads(clean_text)

    def generate(
        self,
        question: str,
        retrieved_results: List[RetrievalResult]
    ) -> GenerationResponse:
        """
        Generates a grounded plain-language answer strictly from supplied context chunks.

        Args:
            question: User's natural-language question.
            retrieved_results: List of top reranked RetrievalResult chunks from Stage 4C.

        Returns:
            Validated GenerationResponse object.
        """
        clean_question = question.strip() if question else ""

        if not clean_question or not retrieved_results:
            return GenerationResponse(
                answer="The available retrieved legal sources do not provide enough information to answer your question.",
                limitations="No relevant legal document chunks were provided in the context.",
                source_ids=[]
            )

        # 1. Build context blocks and get valid chunk IDs
        context_text, valid_chunk_ids = self.context_builder.build_context(retrieved_results)

        # 2. Construct grounded user prompt
        user_prompt = build_user_prompt(clean_question, context_text)

        try:
            # 3. Send prompt to LLM client
            raw_response = self.llm_client.generate(
                system_prompt=GROUNDED_SYSTEM_PROMPT,
                user_prompt=user_prompt
            )

            # 4. Extract and parse JSON
            parsed_data = self._extract_json_payload(raw_response)

            raw_answer = parsed_data.get("answer", "").strip()
            raw_limitations = parsed_data.get("limitations")
            raw_source_ids = parsed_data.get("source_ids", [])

            if not raw_answer:
                raw_answer = "The available legal sources do not specify sufficient details to answer this query."

            # 5. Strict Source ID Validation (reject/remove hallucinated chunk IDs)
            validated_source_ids = [
                sid for sid in raw_source_ids
                if isinstance(sid, str) and sid in valid_chunk_ids
            ]

            return GenerationResponse(
                answer=raw_answer,
                limitations=raw_limitations if isinstance(raw_limitations, str) else None,
                source_ids=validated_source_ids
            )

        except (json.JSONDecodeError, ValidationError, ValueError) as parse_err:
            print(f"Warning: Failed to parse LLM structured output ({parse_err}). Constructing fallback response.")
            return GenerationResponse(
                answer="Based on the retrieved sources, an answer could not be properly formatted.",
                limitations=f"Output Parsing Warning: {str(parse_err)}",
                source_ids=[]
            )
        except Exception as exc:
            print(f"Warning: LLM generation error ({exc}). Returning fallback error response.")
            return GenerationResponse(
                answer="An error occurred while contacting the language generation service.",
                limitations=f"LLM API Exception: {str(exc)}",
                source_ids=[]
            )
