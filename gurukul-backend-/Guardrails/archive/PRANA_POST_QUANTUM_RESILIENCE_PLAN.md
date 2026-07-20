# PRANA Post-Quantum Resilience Plan

**Status:** Future-Proofing Specification  
**Version:** 1.0.0  
**Objective:** Cryptographic agility and quantum-resistant integrity.

## 1. The Post-Quantum Threat
Future "Cryptographically Relevant Quantum Computers" (CRQC) will be capable of breaking current RSA and Elliptic Curve Cryptography (ECDSA/Ed25519) used for PRANA packet signing and bucket authentication. 

- **Risk:** Retroactive decryption of captured traffic; future forgery of PRANA signals.
- **Strategy:** PQC-Agility (Migration without logic rewrite).

## 2. Cryptographic Agility Layer
PRANA rejects monolithic crypto implementation. We design a **Signature Abstraction Interface**.

### 2.1 Interface Definition
The system interacts with a generic `Signer` and `Verifier` module that can wrap multiple algorithms.

```python
interface Signer:
    def sign(message: bytes, key_id: str) -> SignatureBundle
    def get_algorithm_metadata() -> Dict
```

### 2.2 Replaceable Crypto Modules
Algorithms are loaded as pluggable modules.
- **Current (Classical):** Ed25519 (Fast, short signatures).
- **Near-Term (Hybrid):** Ed25519 + CRYSTALS-Dilithium.
- **Long-Term (Pure PQC):** CRYSTALS-Dilithium / SPHINCS+.

## 3. NIST PQC Standards Analysis

| Algorithm              | Type             | PRANA Applicability | Rationale                                            |
| :--------------------- | :--------------- | :------------ | :--------------------------------------------------------- |
| **CRYSTALS-Kyber**     | KEM (Encryption) | **Secondary** | PRANA signals are non-sensitive; primary focus is signing. |
| **CRYSTALS-Dilithium** | Signature        | **Primary (High Perf)** | Highly efficient; standard choice for general-purpose signing. |
| **Falcon**        | Signature | **Primary (Short Sig)** | Lowest signature size; ideal for 2s signal window throughput. |
| **SPHINCS+** | Signature | **Primary (High Security)** | Stateless, hash-based; extremely robust but larger signatures. |

## 4. Hybrid Signature Model
To bridge the classical and quantum eras, PRANA will utilize **Hybrid Classical + PQC Signatures**.

- **Structure:** `Signature = Ed25519(data) || Dilithium(data)`
- **Verification:** Both signatures must be valid for the packet to be accepted.
- **Benefit:** If Dilithium is broken by a classical attack (weakness in new math) or Ed25519 is broken by a quantum attack, the other layer still provides security.

## 5. Migration Pathway (Zero History Re-write)
We do not re-sign history (which violates immutability). We use **Chain Anchoring**.

1. **Phase 1 (Agility Ready):** Deploy the Cryptographic Agility Layer with Ed25519 only.
2. **Phase 2 (Hybrid Emission):** Sensors start emitting Hybrid signatures; Bucket validates both.
3. **Phase 3 (PQC Anchor):** A "Genesis PQC Snapshot" is created. Every new packet's `prev_hash` includes the PQC-signed Merkle Root of the previous block.
4. **Phase 4 (PQC Pure):** Classical signatures are deprecated; system operates on PQC only.

## 6. Migration Constraints
- **No Boundary Violation:** PRANA does not gain "Intelligence" during migration.
- **Signature Abstraction:** The Policy and Enforcement layers only see "Is Authenticated: True/False", regardless of the underlying algorithm.
- **Backwards Compatibility:** Old classical-only packets remain valid if they exist before the specified PQC Anchor Date.

## 7. Justification
Post-quantum readiness is not "feature bloat"; it is an essential architectural requirement for a system designed to provide "Tamper-Evident Guarantees" over a long-term (10+ year) horizon. Without PQC, PRANA's structural integrity has an expiration date.
