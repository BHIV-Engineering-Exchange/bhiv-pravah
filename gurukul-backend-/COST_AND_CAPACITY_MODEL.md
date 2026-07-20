# Gurukul Infrastructure Cost & Capacity Model
**Operational Budget and Server Sizing for 5,000-User Scale**

---

## 1. Capacity Sizing Computations

### CPU Core Demands
*   **Formula**: $\text{Total Cores} = \frac{\text{Concurrent Users} \times \text{Average Requests/User/Sec} \times \text{CPU Time/Request (s)}}{\text{Target Utilization}}$
*   **Values**:
    *   $\text{Concurrent Users} = 5,000$
    *   $\text{Average Requests/User/Sec} = 0.5$ (2,500 total RPS peak)
    *   $\text{CPU Time/Request} = 0.002\text{ seconds}$ (FastAPI execution)
    *   $\text{Target Utilization} = 0.70\text{ (70\%)}$
*   **Result**: $\text{Total Cores} = \frac{5,000 \times 0.5 \times 0.002}{0.70} = 7.14\text{ Cores}$ (Provisioned: 8 Cores minimum for API layer).

### Memory Demands
*   **Formula**: $\text{Total RAM} = (\text{Replicas} \times \text{Pod Footprint}) + \text{Database Overhead}$
*   **Values**:
    *   3 API replicas $\times$ 1.5Gi per pod = 4.5Gi
    *   2 EMS API replicas $\times$ 1.0Gi per pod = 2.0Gi
    *   PostgreSQL active shared buffers = 4.0Gi
    *   MongoDB indexing cache = 4.0Gi
    *   Redis persistence cache = 2.0Gi
*   **Result**: $\text{Total RAM} = 16.5\text{Gi}$ (Provisioned: 32Gi cluster total memory for safety bounds).

---

## 2. Infrastructure Cloud Pricing Forecast (AWS US-East)

Operational pricing assumes on-demand pricing models. Implementing **1-Year Reserved Instances** reduces compute fees by up to 35%.

### 1. Compute Layer (EKS EC2 Instances)
*   **Requirement**: 3 $\times$ `m6g.xlarge` instances (4 vCPUs, 16Gi RAM each).
*   **Pricing**: $0.154 per hour $\times$ 730 hours/month $\times$ 3 nodes.
*   **Monthly Cost**: **$337.26**

### 2. Managed Database (Amazon Aurora PostgreSQL Multi-AZ)
*   **Requirement**: `db.r6g.xlarge` (4 vCPUs, 32Gi RAM) + Replica.
*   **Pricing**: $0.48 per hour $\times$ 730 hours/month $\times$ 2.
*   **Monthly Cost**: **$700.80**

### 3. Managed Cache (Amazon ElastiCache Redis)
*   **Requirement**: `cache.m6g.large` (2 vCPUs, 6.38Gi RAM) with replication.
*   **Pricing**: $0.136 per hour $\times$ 730 hours/month $\times$ 2.
*   **Monthly Cost**: **$198.56**

### 4. Managed NoSQL (MongoDB Atlas Dedicated Tier)
*   **Requirement**: M30 tier (8Gi RAM, 40Gi storage).
*   **Pricing**: $0.27 per hour $\times$ 730 hours.
*   **Monthly Cost**: **$197.10**

### 5. Network Traffic, Storage & EKS Control Fees
*   **EKS Control Plane Fee**: $0.10/hour $\times$ 730 hours = $73.00
*   **gp3 EBS Persistent Storage**: 200Gi $\times$ $0.08/GB-month = $16.00
*   **Application Load Balancer (ALB)**: $22.26 baseline + LCU usage = $58.00
*   **Monthly Cost**: **$147.00**

---

## 3. Total Operational Budget Projection

| Expense Category | Monthly Cost (USD) | Annual Cost (USD) | Budget Share |
| :--- | :--- | :--- | :--- |
| **EKS EC2 Compute** | $337.26 | $4,047.12 | 21.3% |
| **Aurora Postgres DB** | $700.80 | $8,409.60 | 44.3% |
| **ElastiCache Redis** | $198.56 | $2,382.72 | 12.6% |
| **MongoDB Atlas** | $197.10 | $2,365.20 | 12.5% |
| **Network & Addons** | $147.00 | $1,764.00 | 9.3% |
| **TOTAL** | **$1,580.72** | **$18,968.64** | **100%** |
