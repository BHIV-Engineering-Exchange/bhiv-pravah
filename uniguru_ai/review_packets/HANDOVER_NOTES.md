# Handover Notes

## Current Limitations

- Kosha source entries still contain OCR artifacts and thin fragments; the validator now rejects weak entries instead of stretching them into answers.
- Legacy FAISS/LLM helper code remains below the early deterministic return in `backend/service/api.py`; endpoint execution no longer reaches it, but cleanup is recommended.
- Stored Kosha domain labels are inconsistent; runtime ontology normalization compensates.

## Next Risks

- New ingestion flows must tag entries with canonical entities before activation.
- The ontology seed needs Vijay/Soham review before it becomes a formal TANTRA contract.
- Proof execution should be pinned in CI by Alay for environment-stable validation.

## Integration Dependencies

- Vijay: trace contract confirmation for TANTRA execution chain.
- Soham: canonical entity taxonomy and semantic mapping review.
- Alay: CI wiring for `python backend/run_proof_log.py` and `python backend/run_retrieval_benchmark.py`.
