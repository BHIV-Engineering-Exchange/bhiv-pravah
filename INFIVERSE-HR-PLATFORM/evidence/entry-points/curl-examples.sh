#!/bin/bash
# BHIV HR Platform - Authentication Entry Point Examples

# 1. API Key (Admin/System Scope)
curl -X GET -H "Authorization: Bearer prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o" http://localhost:8000/health/detailed

# 2. Client JWT (Tenant Scope - TECH001)
curl -X GET -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJURUNIMDAxIiwiZW1haWwiOiJ0ZWNoMDAxQHRlc3QuY29tIiwicm9sZSI6ImNsaWVudCJ9.dMbImh6FoyaNH6u2w0C-FTVwQbCkJCfz7o50GtW4iVk" http://localhost:8000/v1/client/stats

# 3. Candidate JWT (Self-Service Scope - test_cand_001)
curl -X GET -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjYW5kaWRhdGVfaWQiOiJ0ZXN0X2NhbmRfMDAxIiwiZW1haWwiOiJjYW5kQHRlc3QuY29tIiwicm9sZSI6ImNhbmRpZGF0ZSJ9.X8vRN6MqG0tybaUa6Cw0Xn0jS3_FFBhn2sPELJCNFHE" http://localhost:8000/v1/candidate/stats/test_cand_001
