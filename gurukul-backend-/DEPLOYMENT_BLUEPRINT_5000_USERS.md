# Gurukul Production Deployment Blueprint
**5,000-User Infrastructure Architecture & Isolation Blueprint**

---

## 1. Multi-Zone EKS Infrastructure Topology

For production deployments, the architecture shifts from local containers into an AWS Elastic Kubernetes Service (EKS) multi-AZ topology.

```
                  [ AWS Route 53 (DNS Round-Robin) ]
                                  │
                       [ AWS Application ALB ]
                                  │
                 ┌────────────────┴────────────────┐
                 ▼ (AZ-a)                          ▼ (AZ-b)
         [ EKS Node Group 1 ]              [ EKS Node Group 2 ]
       ┌──────────────────────┐          ┌──────────────────────┐
       │ - gurukul-backend    │          │ - gurukul-backend    │
       │ - ems-backend        │          │ - ems-backend        │
       │ - gurukul-frontend   │          │ - gurukul-frontend   │
       │ - ems-frontend       │          │ - ems-frontend       │
       └──────────────────────┘          └──────────────────────┘
                 │                                 │
     ┌───────────┴─────────────────────────────────┴───────────┐
     ▼ (Isolated Subnets)                                      ▼
[ AWS RDS Aurora Postgres ]                             [ AWS ElastiCache Redis ]
(Multi-AZ Replication)                                  (Persistent AOF backups)
```

---

## 2. Environment Isolation Matrix
To maintain absolute stability and security bounds, Dev, Staging, and Production environments are structurally isolated:

*   **Development**: Local Developer laptop or single namespace in development cluster. Uses SQLite / Mongo DB mock services. Auto-deploys from `dev` branch.
*   **Staging**: Complete namespace mirror of production. Integrates real AWS databases (Aurora PostgreSQL & Mongo) with reduced pricing tiers (e.g., db.t4g instances). Auto-deploys from `main` branch upon CI tests passing.
*   **Production**: Dedicated VPC isolated inside production AWS account. No developer SSH allowed. Deploys via manual gates from immutable semantic tag releases (`v*.*.*`) using GitHub Actions pipelines.

---

## 3. Secret Management Approach
Using plaintext `.env` configurations in production is strictly prohibited as it exposes secrets via node inspection.
1.  **AWS Secrets Manager Integration**: All production secrets (DB credentials, encryption keys, mail credentials) are stored securely in AWS Secrets Manager.
2.  **External Secrets Operator (ESO)**: Kubernetes clusters run External Secrets Operator. It syncs secrets from Secrets Manager directly into native Kubernetes Secret objects (`gurukul-secrets`) dynamically in memory.
3.  **Role Bindings**: Pod service accounts utilize IAM Roles for Service Accounts (IRSA) to read secrets, completely bypassing hardcoded access keys.

---

## 4. Operational Backup & Recovery SOP

### PostgreSQL Backups
*   **Backup Method**: AWS Aurora automated daily snapshots with a **30-day retention window**. Plus, our designed CronJob backup mounts direct volume claims for manual migrations.
*   **Recovery Objective**: RPO (Recovery Point Objective) < 5 minutes (Aurora physical logs), RTO < 10 minutes.

### MongoDB Backups
*   **Backup Method**: MongoDB Atlas continuous backups with point-in-time recovery (PITR) enabled.

### Disaster Recovery Runbook
1.  Verify target VPC availability zones are fully active.
2.  Apply base secrets and CRDs to EKS namespaces.
3.  Provision persistent volume claims from target storage snapshots.
4.  Execute Helm chart apply: `helm upgrade --install gurukul-production ./charts/gurukul`.
5.  Validate database migration state using `/system/health` API hooks.
