# ARTHA Test Suite Documentation

## Overview

Comprehensive test suite for ARTHA v0.1-demo covering unit tests, integration tests, and end-to-end workflows.

## Test Structure

```
tests/
├── integration.test.js          # NEW: E2E integration tests (50+ tests)
├── ledger-chain.test.js         # Hash-chain verification tests
├── ocr.test.js                  # OCR receipt processing tests
├── gst-filing.test.js           # GST filing packet tests
├── invoice.test.js              # Invoice workflow tests
├── expense.routes.test.js       # Expense CRUD tests
├── redis-cache.test.js          # Cache operations tests
├── performance.test.js          # Performance monitoring tests
├── health-monitoring.test.js    # Health check tests
├── final-integration.test.js    # Final integration tests
└── ... (30+ test files)
```

## Quick Start

### 1. Setup Environment

```bash
# Copy test environment file
cp .env.example .env.test

# Configure test database
echo "MONGODB_TEST_URI=mongodb://localhost:27017/artha_test" >> .env.test
echo "JWT_SECRET=test_jwt_secret_minimum_32_characters_long" >> .env.test
echo "HMAC_SECRET=test_hmac_secret_minimum_32_characters_long" >> .env.test
echo "NODE_ENV=test" >> .env.test
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Verify Setup

```bash
npm run verify:integration-tests
```

### 4. Run Tests

```bash
# Run integration tests only
npm run test:integration

# Run all tests
npm run test:all

# Run specific test file
npm run test:ledger
npm run test:ocr
npm run test:gst

# Run with coverage
npm test -- --coverage
```

## Test Categories

### 🔐 Authentication Tests
- User registration
- Login/logout
- JWT token generation
- Token refresh
- Access control

**Files**: `auth.test.js`, `auth.controller.test.js`

### 📒 Ledger & Hash-Chain Tests
- Journal entry creation
- Double-entry validation
- Hash-chain integrity
- Chain verification
- Tamper detection

**Files**: `ledger-chain.test.js`, `ledger.test.js`, `ledger.service.test.js`

### 🧾 Invoice Tests
- Invoice CRUD operations
- AR entry creation
- Payment recording
- Status transitions
- Statistics

**Files**: `invoice.test.js`, `invoice.model.test.js`

### 💰 Expense Tests
- Expense submission
- Approval workflow
- Receipt uploads
- Ledger recording
- OCR integration

**Files**: `expense.routes.test.js`, `ocr.test.js`

### 📊 GST Filing Tests
- GSTR-1 packet generation
- GSTR-3B packet generation
- Tax calculations
- CSV export
- Period validation

**Files**: `gst-filing.test.js`

### 🏥 Health & Monitoring Tests
- Health endpoints
- Performance metrics
- Database optimization
- Redis caching
- System status

**Files**: `health-monitoring.test.js`, `performance.test.js`, `redis-cache.test.js`

### 🔗 Integration Tests (NEW)
- Complete workflows
- Service integration
- API contract testing
- Backward compatibility
- Error handling

**Files**: `integration.test.js`

## Running Specific Test Suites

### Integration Tests (Recommended)
```bash
npm run test:integration
```

**Coverage**: 10 test suites, 50+ tests
- Authentication flow
- Ledger & hash-chain
- Invoice workflow
- Expense workflow
- GST filing
- Health checks
- Authorization
- Legacy routes
- Error handling

### Hash-Chain Tests
```bash
npm run test:ledger
```

**Coverage**: Hash computation, chain linkage, tamper detection

### OCR Tests
```bash
npm run test:ocr
```

**Coverage**: Text extraction, field parsing, confidence scoring

### GST Tests
```bash
npm run test:gst
```

**Coverage**: GSTR-1, GSTR-3B, tax calculations

### Performance Tests
```bash
npm run test:performance
```

**Coverage**: Request timing, memory monitoring, slow queries

### Cache Tests
```bash
npm run test:cache
```

**Coverage**: Redis operations, cache invalidation, TTL

### All Tests
```bash
npm run test:all
```

**Coverage**: Complete test suite with coverage report

## Test Patterns

### Standard Test Structure
```javascript
describe('Feature Name', () => {
  beforeAll(async () => {
    // Setup: Create test data
  });

  afterAll(async () => {
    // Cleanup: Remove test data
  });

  test('should do something', async () => {
    // Arrange
    const input = { ... };

    // Act
    const result = await someFunction(input);

    // Assert
    expect(result).toBe(expected);
  });
});
```

### API Test Pattern
```javascript
test('should create resource', async () => {
  const response = await request(app)
    .post('/api/v1/resource')
    .set('Authorization', `Bearer ${token}`)
    .send(data);

  expect(response.status).toBe(201);
  expect(response.body.success).toBe(true);
  expect(response.body.data).toHaveProperty('id');
});
```

### Service Test Pattern
```javascript
test('should process data correctly', async () => {
  const input = { ... };
  const result = await service.method(input);

  expect(result).toMatchObject({
    field1: expectedValue1,
    field2: expectedValue2,
  });
});
```

## Custom Matchers

### toBeOneOf
```javascript
expect(response.status).toBeOneOf([200, 201, 400]);
```

Allows flexible status code checking for endpoints with multiple valid responses.

## Coverage Reports

### Generate Coverage
```bash
npm test -- --coverage
```

### View HTML Report
```bash
# After running tests with coverage
open coverage/lcov-report/index.html
```

### Coverage Targets
- **Statements**: >80%
- **Branches**: >75%
- **Functions**: >80%
- **Lines**: >80%

## Debugging Tests

### Run Single Test
```bash
npm test -- tests/integration.test.js --testNamePattern="should create invoice"
```

### Watch Mode
```bash
npm run test:watch
```

### Verbose Output
```bash
npm test -- --verbose
```

### Debug Mode
```bash
node --inspect-brk node_modules/.bin/jest tests/integration.test.js
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm run test:all
```

### Docker Testing
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Troubleshooting

### Database Connection Errors
```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Start MongoDB
mongod --dbpath /data/db
```

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Test Timeout
```javascript
// Increase timeout for slow tests
test('slow operation', async () => {
  // ...
}, 30000); // 30 seconds
```

### Memory Issues
```bash
# Increase Node memory
NODE_OPTIONS=--max_old_space_size=4096 npm test
```

## Best Practices

### ✅ DO
- Write isolated tests (no dependencies between tests)
- Clean up test data in `afterAll()`
- Use descriptive test names
- Test both success and error cases
- Mock external services
- Use factories for test data

### ❌ DON'T
- Share state between tests
- Use production database
- Hard-code test data
- Skip cleanup
- Test implementation details
- Ignore failing tests

## Maintenance

### Adding New Tests
1. Create test file in `tests/` directory
2. Follow existing patterns
3. Add test script to `package.json`
4. Update this README
5. Run `npm run verify:integration-tests`

### Updating Tests
1. Maintain backward compatibility
2. Update related tests
3. Run full test suite
4. Update documentation

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Supertest Documentation](https://github.com/visionmedia/supertest)
- [MongoDB Memory Server](https://github.com/nodkz/mongodb-memory-server)

## Support

For issues or questions:
1. Check this README
2. Review test output
3. Check logs in `backend/logs/`
4. Review DEEP_ANALYSIS.md
5. Open GitHub issue

---

**Last Updated**: 2025-02-05  
**Test Coverage**: 50+ integration tests, 30+ test files  
**Status**: ✅ All tests passing
