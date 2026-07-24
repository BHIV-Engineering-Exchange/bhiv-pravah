# Ecosystem Participant Registry

**Phase 1 — Ecosystem Discovery**
This registry identifies the actual runtime participants in the TANTRA ecosystem, specifically mapping the boundaries around KESHAV.

## 1. SETU / Input
* **Role**: Signal Generation
* **Upstream Systems**: None (Ecosystem Entry)
* **Downstream Systems**: KESHAV (Intelligence)
* **Runtime Ownership**: Ecosystem Integrator
* **Authority Ownership**: Ecosystem Authority
* **Dependency Ownership**: Ecosystem
* **Execution Ownership**: Ecosystem
* **Declarations**:
  * Authority NOT Owned (by KESHAV)
  * Authority Ceiling

## 2. KESHAV
* **Role**: Intelligence Layer
* **Upstream Systems**: SETU / Input (Signal)
* **Downstream Systems**: RAJYA (Decision), InsightFlow (Observability)
* **Runtime Ownership**: Rajaryan Verma
* **Authority Ownership**: Rajaryan Verma
* **Dependency Ownership**: Rajaryan Verma
* **Execution Ownership**: Rajaryan Verma
* **Declarations**:
  * Authority Owned (by KESHAV Owner)

## 3. RAJYA
* **Role**: Decision Validation
* **Upstream Systems**: KESHAV (Intelligence)
* **Downstream Systems**: Sarathi (Enforcement)
* **Runtime Ownership**: RAJYA Owner
* **Authority Ownership**: RAJYA Owner
* **Dependency Ownership**: RAJYA Owner
* **Execution Ownership**: RAJYA Owner
* **Declarations**:
  * Authority NOT Owned (by KESHAV)
  * Authority Ceiling

## 4. Sarathi
* **Role**: Contract Enforcement
* **Upstream Systems**: RAJYA (Decision)
* **Downstream Systems**: Core (Execution)
* **Runtime Ownership**: Sarathi Owner
* **Authority Ownership**: Sarathi Owner
* **Dependency Ownership**: Sarathi Owner
* **Execution Ownership**: Sarathi Owner
* **Declarations**:
  * Authority NOT Owned (by KESHAV)
  * Authority Ceiling

## 5. Core
* **Role**: Action Execution
* **Upstream Systems**: Sarathi (Enforcement)
* **Downstream Systems**: Bucket (Truth)
* **Runtime Ownership**: Core Owner
* **Authority Ownership**: Core Owner
* **Dependency Ownership**: Core Owner
* **Execution Ownership**: Core Owner
* **Declarations**:
  * Authority NOT Owned (by KESHAV)
  * Authority Ceiling

## 6. Bucket
* **Role**: Persistence and Truth Store
* **Upstream Systems**: Core (Execution)
* **Downstream Systems**: None
* **Runtime Ownership**: Bucket Owner
* **Authority Ownership**: Bucket Owner
* **Dependency Ownership**: Bucket Owner
* **Execution Ownership**: Bucket Owner
* **Declarations**:
  * Authority NOT Owned (by KESHAV)
  * Authority Ceiling

## 7. InsightFlow
* **Role**: Observability and Telemetry
* **Upstream Systems**: KESHAV (Intelligence)
* **Downstream Systems**: None
* **Runtime Ownership**: InsightFlow Owner
* **Authority Ownership**: InsightFlow Owner
* **Dependency Ownership**: InsightFlow Owner
* **Execution Ownership**: InsightFlow Owner
* **Declarations**:
  * Authority NOT Owned (by KESHAV)
  * Authority Ceiling
