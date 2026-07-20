from fastapi import APIRouter, HTTPException, Body
from services.validation_service import validation_service
from services.ontology_service import ontology_service
from services.rag_service import rag_service
from services.response_formatter import response_formatter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["Intelligence"])

from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field("", description="The user question or query.")
    question: str = Field("", description="Alternative key for the user question.")
    subject: Optional[str] = Field(None, description="Optional subject/topic selection from UI (e.g., Programming)")

@router.post("/ask")
async def ask_uniguru(request: QueryRequest):
    """
    Unified intelligence endpoint with deterministic priority and local LLM fallback.
    """
    try:
        # Support both 'query' and 'question' keys for better compatibility
        query = request.query or request.question
        logger.info(f"Received intelligence query: {query}")
        print(f"> Intelligence Request: {query}")

        clean_query = query.strip().strip("?!.,").lower()
        if clean_query in {"hello", "hi", "hey"}:
            suggested_question = "What is the core purpose of human life according to Swaminarayan teachings?"
            suggested_answer = (
                "According to Swaminarayan teachings, the core purpose of human life is to attain "
                "spiritual progress through dharma, bhakti, gnan, and vairagya, while living in satsang "
                "and drawing closer to Bhagwan."
            )
            return response_formatter.format_response(
                decision="answer",
                confidence=1.0,
                source="none",
                answer=(
                    "Hello! Kuch to kaho\n\n"
                    f"Suggested Swaminarayan question: {suggested_question}\n"
                    f"Answer: {suggested_answer}"
                ),
            )
        
        # 1. Run Validation
        validation = validation_service.validate_query(query)
        if not validation["is_valid"]:
            logger.warning(f"Query validation failed: {validation['error']}")
            return response_formatter.format_response(
                decision="reject",
                confidence=0.0,
                source="none",
                answer=validation["error"]
            )

        # 2. Intent-Based Deterministic Retrieval (Ontology / unified retriever)
        logger.info("Attempting deterministic ontology retrieval...")
        from retrieval.retriever import retrieve_knowledge_with_trace

        content, trace = retrieve_knowledge_with_trace(query, subject=request.subject)
        if content and trace.get("match_found") and float(trace.get("confidence") or 0) >= 0.30:
            logger.info("Unified retriever match with confidence %s", trace.get("confidence"))
            return response_formatter.format_response(
                decision="answer",
                confidence=float(trace.get("confidence") or 0.0),
                source=str(trace.get("method") or "ontology"),
                answer=content,
            )

        ontology_res = ontology_service.get_deterministic_answer(query)
        if ontology_res and ontology_res.get("confidence", 0) >= 0.85:
            logger.info(f"Ontology match found with confidence {ontology_res['confidence']}")
            return response_formatter.format_response(
                decision="answer",
                confidence=ontology_res["confidence"],
                source="ontology",
                answer=ontology_res["answer"]
            )

        # 3. Vector-Based Semantic Retrieval (RAG)
        logger.info("Attempting vector-based semantic retrieval...")
        rag_res = rag_service.search_vectorstore(query)
        if rag_res and rag_res.get("confidence", 0) >= 0.70:
            logger.info(f"Vectorstore match found with confidence {rag_res['confidence']}")
            return response_formatter.format_response(
                decision="answer",
                confidence=rag_res["confidence"],
                source="vectorstore",
                answer=rag_res["answer"]
            )

        # 4. Final Rejection (No Knowledge Found)
        logger.info("No knowledge found in ontology or vectorstore.")
        return response_formatter.format_response(
            decision="reject",
            confidence=0.0,
            source="none",
            answer="I'm sorry, I couldn't find any verified information regarding your query in my knowledge base."
        )
    except Exception as e:
        logger.error(f"Critical error in intelligence router: {str(e)}", exc_info=True)
        print(f"!!! Router Error: {str(e)}")
        return response_formatter.format_response(
            decision="reject",
            confidence=0.0,
            source="none",
            answer=f"An internal error occurred: {str(e)}"
        )
