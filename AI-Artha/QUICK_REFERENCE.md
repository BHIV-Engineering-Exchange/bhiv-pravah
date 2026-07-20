# ARTHA v0.1 - Quick Reference

## 🚀 Quick Start (5 mins)

```bash
# 1. Start services
docker-compose -f docker-compose.dev.yml up -d

# 2. Seed data
docker exec artha-backend-dev npm run seed

# 3. Access
# Frontend: http://localhost:5173
# Backend: http://localhost:5000
# Admin: admin@artha.local / Admin@123456
```

## 🔑 API Quick Commands

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
-H "Content-Type: application/json" \
-d '{"email":"admin@artha.local","password":"Admin@123456"}' \
| jq -r '.data.token')

# Verify ledger chain
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/ledger/verify-chain | jq

# Get GST summary (Feb 2025)
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/gst/summary?period=2025-02" | jq

# Generate GSTR-1
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/gst/filing-packet/gstr-1?period=2025-02" | jq

# Get P&L
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/reports/profit-loss?startDate=2025-01-01&endDate=2025-12-31" | jq
```

## 📊 Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Basic health |
| GET | `/health/detailed` | System status |
| POST | `/api/v1/auth/login` | Get JWT |
| GET | `/api/v1/ledger/verify-chain` | **Verify ledger integrity** |
| POST | `/api/v1/expenses/ocr` | **Process receipt** |
| GET | `/api/v1/gst/summary?period=YYYY-MM` | **GST summary** |
| GET | `/api/v1/reports/profit-loss?...` | P&L report |
| GET | `/api/v1/reports/balance-sheet?...` | Balance sheet |

## 🧪 Testing

```bash
cd backend

# All tests
npm run test:all

# Specific test suites
npm run test:ledger      # Hash-chain
npm run test:ocr         # OCR pipeline
npm run test:gst         # GST filing

# Full test script
./scripts/run-all-tests.sh
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | `docker logs artha-backend-dev` |
| No data in dashboard | `docker exec artha-backend-dev npm run seed` |
| API returns 401 | Get new token: `/auth/login` |
| Hash verify fails | `docker-compose restart` |
| OCR not working | Check: `GET /expenses/ocr/status` |

## 📝 New Features (Days 1-7)

### ✨ Day 1: Hash-Chain Ledger
- Every entry has cryptographic hash
- Verify entire chain: `GET /ledger/verify-chain`
- Detect tampering immediately

### ✨ Day 2: OCR Receipts
- Upload receipt image: `POST /expenses/ocr`
- Auto-extract: vendor, date, amount, tax
- Pre-fill expense form

### ✨ Day 3: GST Filing
- GSTR-1 packet: `GET /gst/filing-packet/gstr-1?period=2025-02`
- GSTR-3B packet: `GET /gst/filing-packet/gstr-3b?period=2025-02`
- Export CSV: `GET /gst/filing-packet/export?type=gstr-1&period=2025-02`

### ✨ Day 4: Pravah Deploy
- See: `docs/PRAVAH_DEPLOYMENT.md`
- Production-ready pipeline
- Health check configured

### ✨ Day 5-6: Testing & UI
- Full integration test suite
- Ledger integrity widget
- GST summary component
- OCR receipt scanner UI

## 📚 Documentation

| File | Purpose |
|------|---------|
| README.md | Project overview & API docs |
| DEPLOYMENT.md | Production deployment |
| docs/PRAVAH_DEPLOYMENT.md | Pravah-specific guide |
| docs/DEMO_SCENARIOS.md | Demo walkthrough |
| docs/RUNTIME_ARCHITECTURE.md | BHIV runtime architecture |
| docs/INTEGRATION_GUIDE.md | BHIV integration guide |
| docs/DEPLOYMENT_GUIDE.md | BHIV deployment guide |
| docs/OPERATIONS_GUIDE.md | BHIV operations guide |
| docs/INCIDENT_RECOVERY_GUIDE.md | Incident recovery procedures |
| docs/AUTHORITY_BOUNDARY_GUIDE.md | Authority boundaries |
| docs/CAPABILITY_REGISTRATION_GUIDE.md | Capability registration |
| QUICK_REFERENCE.md | This file |

## 🎯 Demo Flow (25 mins)

1. **Dashboard overview** (5)
2. **Hash-chain verification** (4)
3. **Invoice workflow** (5)
4. **OCR expense entry** (5)
5. **GST export** (3)
6. **Reports** (2)
7. **Q&A** (1)

## 💾 Backup & Restore

```bash
# Backup
docker exec artha-mongo-dev mongodump \
-u root -p password --out /backups/dump_$(date +%Y%m%d_%H%M%S)

# Restore
docker exec artha-mongo-dev mongorestore \
-u root -p password /backups/dump_YYYYMMDD_HHMMSS
```

## 🔐 Security Reminders

- JWT secrets in .env only
- Never commit secrets to repo
- Rotate JWT secrets quarterly
- Enable HTTPS in production
- Use Pravah Secrets Manager
- Enable rate limiting
- Audit all ledger changes

## 📞 Need Help?

- **Frontend issue?** Check browser console
- **API issue?** `docker logs artha-backend-dev`
- **Database issue?** `docker exec artha-mongo-dev mongosh --eval "db.adminCommand('ping')"`
- **See:** `DEPLOYMENT.md` → "Troubleshooting"

---

**Last Updated**: Dec 5, 2025 | **Status**: Production Ready ✅