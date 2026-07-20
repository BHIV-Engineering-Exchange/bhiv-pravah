"""
Proof Log Generator — Isha Task Deliverable
Runs 20+ queries through the deterministic Kosha pipeline.
Produces schema-bound signal outputs and per-trace proof logs.
Includes semantic mismatch queries that must return NO VERIFIED KNOWLEDGE.
"""
import sys
import os
import json
import logging
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING)

from kosha.deterministic_pipeline import run_deterministic_pipeline

PROOF_QUERIES = [
    "What is the Bhagavad Gita?",
    "What does the Bhagavad Gita teach about Karma Yoga?",
    "Tell me about Vishnu in the Narada Purana",
    "What is the Padma Purana?",
    "How are rivers like Ganga described in Puranic texts?",
    "What guidance do ancient texts provide about kingship and Rajadharma?",
    "Explain the Upanishadic concept of Brahman",
    "What does the Mahabharata say about dharma?",
    "Explain temple construction in the Agni Purana",
    "What is the role of ecology and water conservation in dharma systems?",
    "Return Upanishads for Bhagavad Gita teachings",
    "Give an Ahimsa answer from the Narada Purana",
    "Explain quantum entanglement from the Bhagavad Gita",
    "Who won the cricket match yesterday?",
    "What is the current stock price of Apple?",
    "What is the significance of the number 108 in Hinduism?",
    "Tell me about the story of Prahlada in the Bhagavata Purana",
    "How is meditation (Dhyana) described in the Upanishads?",
    "What does the Rigveda say about Agni?",
    "Explain the concept of Moksha in the philosophical schools",
    "Give me the recipe for the perfect pizza",
    "How do I fix a leaking faucet?",
    "What are the main teachings of the Shiva Purana?",
    "What are the ethical duties of a householder (Grihastha)?",
    "Is time travel possible according to ancient Indian texts?",
    "What is the role of the Guru in spiritual traditions?",
    "Describe the architectural layout of a traditional Mandir",
    "What are the health benefits of fasting according to Ayurveda?",
    "How does the concept of Maya work in Advaita Vedanta?",
    "Can you recommend a good movie to watch?",
    "What are the key elements of Pancharatra Agama?",
    "Explain the symbolism of Lord Ganesha's form",
]


def run_proof_log():
    results = []
    no_knowledge_count = 0
    knowledge_found_count = 0

    print("=" * 70)
    print("UNIGURU DETERMINISTIC KOSHA PIPELINE — PROOF LOG")
    print(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    for i, query in enumerate(PROOF_QUERIES):
        result = run_deterministic_pipeline(query)

        status = result["verification_status"]
        confidence = result["confidence_breakdown"]["overall"]
        signals_found = len(result["matched_signals"])
        signals_rejected = len(result["rejected_signals"])
        answer = result["answer"]
        reasoning = result["reasoning_path"]

        if status == "NO_VERIFIED_KNOWLEDGE":
            no_knowledge_count += 1
        else:
            knowledge_found_count += 1

        entry = {
            "query_number": i + 1,
            "trace_id": result["trace_id"],
            "query": query,
            "verification_status": status,
            "confidence_breakdown": result["confidence_breakdown"],
            "matched_signals": result["matched_signals"],
            "rejected_signals": result["rejected_signals"],
            "knowledge_ids_used": result["knowledge_ids_used"],
            "domain_resolution": result["domain_resolution"],
            "synthesis_mode": result["synthesis_mode"],
            "answer_preview": answer[:120] + "..." if len(answer) > 120 else answer,
            "reasoning_path": reasoning,
        }
        results.append(entry)

        # Print to console
        print(f"\n[{i+1:02d}] {query}")
        print(f"     Status    : {status}")
        print(f"     Trace     : {result['trace_id']}")
        print(f"     Confidence: {confidence:.4f}")
        print(f"     Signals   : {signals_found} found, {signals_rejected} rejected")
        safe_preview = entry["answer_preview"].encode("ascii", errors="replace").decode("ascii")
        print(f"     Answer    : {safe_preview}")
        print(f"     Path      : {' -> '.join(reasoning)}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print(f"  Total queries       : {len(PROOF_QUERIES)}")
    print(f"  Knowledge found     : {knowledge_found_count}")
    print(f"  NO VERIFIED KNOWLEDGE: {no_knowledge_count}")
    print("=" * 70)

    # Save proof log
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "review_packets", "proof_logs", "proof_log_summary.json"
    )
    output_path = os.path.normpath(output_path)

    proof_log = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "signal_first_ontology_kosha_v3",
        "total_queries": len(PROOF_QUERIES),
        "knowledge_found": knowledge_found_count,
        "no_verified_knowledge": no_knowledge_count,
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(proof_log, f, indent=2, ensure_ascii=False)

    print(f"\nProof log saved to: {output_path}")
    return proof_log


if __name__ == "__main__":
    run_proof_log()
