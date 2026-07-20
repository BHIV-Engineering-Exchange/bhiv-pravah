# 🧪 ARTHA Testing - Quick Reference Card

## 🚀 Quick Commands

### Run Tests
```bash
npm run test:quick          # Quick tests (~2 min)
npm run test:full           # Full suite (~10 min)
npm run test:integration    # Integration tests
npm run test:all            # All tests with coverage
```

### Verify Setup
```bash
npm run verify:integration-tests
```

### Specific Tests
```bash
npm run test:ledger         # Hash-chain tests
npm run test:ocr            # OCR tests
npm run test:gst            # GST filing tests
npm run test:invoice        # Invoice tests
npm run test:expense        # Expense tests
```

---

## 📊 Test Coverage

| Suite | Tests | Duration | Purpose |
|-------|-------|----------|---------|
| Integration | 50+ | ~3 min | E2E workflows |
| Hash-Chain | 15 | ~30 sec | Ledger integrity |
| OCR | 11 | ~20 sec | Receipt processing |
| GST | 10 | ~25 sec | Tax filing |
| Invoice | 8 | ~40 sec | Invoice workflows |
| Expense | 7 | ~35 sec | Expense workflows |

---

## 🎯 When to Use

### Pre-Commit
```bash
npm run test:quick
```
Fast validation before committing changes.

### Pre-Push
```bash
npm run test:full
```
Complete validation before pushing to remote.

### CI/CD
```bash
npm run test:full
```
Automated testing in pipeline.

### Development
```bash
npm run test:watch
```
Watch mode for active development.

---

## 🔧 Platform-Specific

### Unix/Linux/Mac
```bash
# Make executable (first time)
./scripts/make-executable.sh

# Run tests
./scripts/quick-test.sh
./scripts/run-all-tests.sh
```

### Windows
```bash
# Run tests
scripts\quick-test.bat
scripts\run-all-tests.bat
```

---

## 🐛 Troubleshooting

### MongoDB Connection
```bash
mongosh --eval "db.adminCommand('ping')"
```

### Port Conflict
```bash
# Unix
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
```

### Clear Cache
```bash
npm run test -- --clearCache
```

---

## 📝 Environment Setup

### Required Variables
```bash
MONGODB_TEST_URI=mongodb://localhost:27017/artha_test
JWT_SECRET=test_jwt_secret_minimum_32_characters_long
HMAC_SECRET=test_hmac_secret_minimum_32_characters_long
NODE_ENV=test
```

---

## ✅ Test Phases

1. **Code Quality** - Linting
2. **Unit Tests** - Core functionality
3. **Integration Tests** - E2E workflows
4. **System Tests** - Performance, health

---

## 🎨 Output Colors

- 🟢 **Green** - Test passed
- 🔴 **Red** - Test failed
- 🟡 **Yellow** - Test running
- 🔵 **Blue** - Phase header

---

## 📚 Documentation

- `INTEGRATION_TEST_SUITE_COMPLETE.md` - Test details
- `TEST_EXECUTION_SCRIPTS_COMPLETE.md` - Script usage
- `backend/tests/README.md` - Test guide
- `COMPLETE_TEST_SUITE_IMPLEMENTATION.md` - Summary

---

## 🔗 Quick Links

| Command | Purpose |
|---------|---------|
| `npm run test:quick` | Quick validation |
| `npm run test:full` | Complete test suite |
| `npm run test:integration` | E2E tests |
| `npm run verify:integration-tests` | Setup check |
| `npm run test:watch` | Watch mode |
| `npm test -- --coverage` | With coverage |

---

**Keep this card handy for quick reference!** 📌
