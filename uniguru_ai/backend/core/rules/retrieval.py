import re
import os

from core.rules.base import BaseRule, RuleContext, RuleResult, RuleAction
from retrieval.retriever import retrieve_knowledge_with_trace
from verifier.source_verifier import SourceVerifier

KB_CONFIDENCE_THRESHOLD = float(__import__("os").getenv("UNIGURU_KB_CONFIDENCE_THRESHOLD", "0.30"))
UNVERIFIED_REFUSAL = "Knowledge not found in verified ontology."
MAX_KB_RESPONSE_CHARS = 2000


def _clean_kb_content(raw_content: str) -> str:
    text = str(raw_content or "").replace("\r", "")
    text = re.sub(r"^---[\s\S]*?---\n*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"\$(.*?)\$", r"\1", text)
    text = re.sub(r"`{1,3}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= MAX_KB_RESPONSE_CHARS:
        return text
    shortened = text[:MAX_KB_RESPONSE_CHARS].rsplit(" ", 1)[0].strip()
    return f"{shortened}\n\n[Content trimmed for readability.]"

class RetrievalRule(BaseRule):
    def evaluate(self, context: RuleContext) -> RuleResult:
        query = context.content
        prefetched = context.metadata.get("prefetched_content")
        prefetched_trace = context.metadata.get("retrieval_trace")

        if prefetched and isinstance(prefetched_trace, dict) and prefetched_trace.get("match_found"):
            content = prefetched
            trace = prefetched_trace
        else:
            content, trace = retrieve_knowledge_with_trace(query)

        confidence = float(trace.get("confidence", 0.0))
        match_found = trace.get("match_found", False)
        v_status = trace.get("verification_status", "FAILED")

        if match_found and confidence >= KB_CONFIDENCE_THRESHOLD:
            # Reasonable match found in KB (Keyword or Semantic)
            return RuleResult(
                action=RuleAction.ANSWER,
                reason=f"Verified knowledge found with {confidence:.2f} confidence.",
                severity=0.0,
                governance_flags=self.default_governance(),
                response_content=content or "",
                rule_name=self.name,
                extra_metadata={
                    "retrieval_trace": trace,
                    "verification_status": v_status,
                },
            )

        # No sufficient KB match
        return RuleResult(
            action=RuleAction.BLOCK,
            reason="Knowledge not found in verified ontology with sufficient confidence.",
            severity=0.5,
            governance_flags=self.default_governance(),
            response_content="Knowledge not found in verified ontology.",
            rule_name=self.name,
            extra_metadata={
                "retrieval_trace": trace,
                "verification_status": "FAILED",
            },
        )
