# Aware-Engine-v2-Spec

1. Project Overview
This repository contains the completed Correction Task for the Assignment-Aware Engine. The engine has been upgraded from a deterministic but incomplete state to achieve full scoring contract compliance.

2. Scoring Contract Implementation
The engine strictly implements the exact weighted scoring formula as defined in the technical specification:

Accuracy (40% Weighting): Separated from quality and completeness to resolve previous borderline logic.

Completeness (40% Weighting): Calculated by comparing assignment.deliverables against submission.artifacts_present.

Quality (20% Weighting): Evaluated as a distinct metric to ensure high-standard output.

3. Deterministic Engineering
"Maintain determinism at all costs" is the guiding principle of this build. Key features include:

Timeline Discipline Penalty: Automatic score deductions for late submissions based on deterministic date comparisons.

Strict Validation: Implementation of nested JSON schema validation to enforce the EMS Validation contract.

Pure Function Design: Logic is structured to prevent hidden states in JavaScript evaluators, ensuring identical inputs always yield identical outputs.

4. Verification & Hardening

Deliverables Matching: The engine automatically deducts completeness scores if mandatory artifacts are missing.

Production Readiness: All mock naming has been removed, and the engine has been moved to the production directory.

Determinism Proof: The system has passed the mandatory 5x determinism test, verifying that the scoring output is 100% reproducible.


5. Technical Requirements Met

Integration Ready: Structured for future integration with the deployment layer and AI reviewer.

Test Hardening: Golden tests have been updated and are verified as passing.
