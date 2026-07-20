import logging
import time
import asyncio
from typing import Dict, Any, Optional

from core.engine import RuleEngine
from enforcement.enforcement import UniGuruEnforcement
from reasoning.concept_resolver import ConceptResolver
from retrieval.retriever import (
    retrieve_knowledge_with_trace,
    NO_KNOWLEDGE_ANSWER,
)
from utils.rag_logger import (
    log_final_answer,
    log_incoming_request,
)

logger = logging.getLogger("uniguru.live")


class LiveUniGuruService:

    def __init__(self):
        self.engine = RuleEngine()
        self.enforcement = UniGuruEnforcement()
        self.concept_resolver = ConceptResolver()


    def _handle_small_talk(self, query: str):
        greetings = {
            "hi": "Hello 👋 How can I help you today?",
            "hello": "Hello 👋 How can I help you today?",
            "hey": "Hey 👋 What can I do for you?",
            
            "good morning": "Good morning 🌞 How can I help you?",
            "good afternoon": "Good afternoon 😊 How can I assist you?",
            "good evening": "Good evening 🌙 How can I help you?",

            "thanks": "You're welcome 😊",
            "thank you": "You're welcome 😊",

            "bye": "Goodbye 👋 Have a great day!"
        }

        text = query.lower().strip()

        return greetings.get(text)


    async def ask(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        allow_web_retrieval: bool = False,
    ) -> Dict[str, Any]:

        start_time = time.perf_counter()

        metadata = dict(context or {})
        metadata["session_id"] = session_id

        caller = metadata.get("caller")

        log_incoming_request(
            user_query,
            session_id=session_id,
            caller=caller
        )


        small_talk = self._handle_small_talk(user_query)

        if small_talk:
            return {
                "decision": "answer",
                "confidence": 1.0,
                "source": "small_talk",
                "answer": small_talk,
                "session_id": session_id,
                "reason": "Greeting handled directly",
                "verification_status": "VERIFIED",
                "routing": {
                    "route": "SMALL_TALK"
                }
            }


        content, retrieval_trace = await asyncio.to_thread(
            retrieve_knowledge_with_trace,
            user_query
        )

    
        # ===============================
        # STEP 1 : RETRIEVAL
        # ===============================

        try:

            retrieved_content, retrieval_trace = await asyncio.to_thread(
                retrieve_knowledge_with_trace,
                user_query
            )

        except Exception as e:

            logger.exception(
                "Retrieval failed"
            )

            retrieved_content = ""
            retrieval_trace = {
                "match_found": False,
                "error": str(e)
            }

            print("========== RETRIEVAL DEBUG ==========")
        print("QUERY:", user_query)
        print("CONTENT:", retrieved_content)
        print("TRACE:", retrieval_trace)
        print("====================================")



        # ===============================
        # STEP 2 : ENGINE REASONING
        # ===============================


        engine_metadata = {
            **metadata,
            "retrieval_trace": retrieval_trace,
            "prefetched_content": retrieved_content,
        }


        decision = await asyncio.to_thread(
            self.engine.evaluate,
            content=user_query,
            metadata=engine_metadata,
            apply_enforcement=False,
        )


        data = decision.setdefault(
            "data",
            {}
        )


        # ===============================
        # STEP 3 : MERGE RETRIEVAL ANSWER
        # ===============================


        if retrieved_content:

            data["response_content"] = retrieved_content

            data["retrieval_trace"] = retrieval_trace


            decision["decision"] = "answer"


            decision["verification_status"] = (
                retrieval_trace.get(
                    "verification_status"
                )
                or
                "VERIFIED"
            )


            decision["reason"] = (
                "Knowledge retrieved from "
                f"{retrieval_trace.get('method','unknown')}"
            )


        else:

            decision.setdefault(
                "verification_status",
                "UNVERIFIED"
            )


        # ===============================
        # STEP 4 : ENFORCEMENT
        # ===============================


        sealed = await asyncio.to_thread(
            self.enforcement.validate_and_bind,
            decision
        )


        latency = (
            time.perf_counter()
            -
            start_time
        ) * 1000


        sealed["total_latency_ms"] = round(
            latency,
            2
        )


        # ===============================
        # STEP 5 : FINAL RESPONSE
        # ===============================


        response = self._build_contract_response(
            sealed,
            session_id,
            retrieval_trace
        )


        log_final_answer(
            user_query,
            response.get("answer",""),
            response.get("verification_status"),
            response.get("confidence",0),
            response.get("source")
        )


        return response




    def _build_contract_response(
        self,
        sealed: Dict[str,Any],
        session_id: Optional[str],
        retrieval_trace: Optional[Dict[str,Any]]
    ):


        data = sealed.get(
            "data",
            {}
        )


        answer = (
            data.get("response_content")
            or
            sealed.get("answer")
            or
            ""
        )


        answer = str(answer).strip()



        if answer == NO_KNOWLEDGE_ANSWER:

            answer = ""



        decision_raw = str(
            sealed.get("decision","reject")
        ).lower()



        if decision_raw in [
            "answer",
            "allow",
            "forward",
            "fallback"
        ] and answer:

            decision = "answer"

        else:

            decision = "reject"



        trace = (
            retrieval_trace
            or
            data.get("retrieval_trace")
            or {}
        )


        confidence = float(
            trace.get(
                "confidence",
                0
            )
        )


        source = (
            trace.get("method")
            or
            trace.get("source")
            or
            "engine"
        )


        verification = (
            sealed.get(
                "verification_status"
            )
            or
            "UNVERIFIED"
        )


        if not answer:

            answer = (
                "Knowledge not found "
                "in verified ontology."
            )



        return {


            "decision": decision,


            "answer": answer,


            "confidence": round(
                confidence,
                2
            ),


            "source": source,


            "session_id": session_id,


            "reason": sealed.get(
                "reason"
            ),



            "verification_status": verification,



            "ontology_reference":
                sealed.get(
                    "ontology_reference"
                )
                or
                {
                    "concept_id":
                    "retrieval::unified",

                    "domain":
                    "knowledge"
                },



            "reasoning_trace": {


                "sources_consulted":
                    trace.get(
                        "sources_consulted"
                    )
                    or
                    [source],



                "retrieval_confidence":
                    confidence,



                "similarity_scores":
                    trace.get(
                        "similarity_scores"
                    )
                    or [],



                "verification_status":
                    verification,



                "pipeline_trace":
                    data.get(
                        "trace"
                    )
                    or []

            },



            "routing": {

                "route":
                    "ROUTE_ONTOLOGY",


                "retrieval_method":
                    source
            },



            "governance_flags":
                sealed.get(
                    "governance_flags"
                )
                or {},



            "enforcement_signature":
                sealed.get(
                    "enforcement_signature"
                ),



            "request_id":
                sealed.get(
                    "request_id"
                )
                or
                data.get(
                    "request_id"
                ),



            "total_latency_ms":
                sealed.get(
                    "total_latency_ms"
                )

        }




live_service = LiveUniGuruService()