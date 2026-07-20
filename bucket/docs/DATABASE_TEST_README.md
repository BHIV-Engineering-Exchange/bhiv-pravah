# Supabase Database Test Suite

A comprehensive QA automation framework for testing Supabase PostgreSQL database operations and API integration for the AI Integration Platform.

## 🚀 Features

- **Complete CRUD Testing**: INSERT, SELECT, UPDATE, DELETE operations
- **API Integration**: Simulated calls to Anmol's backend endpoints
- **Edge Case Coverage**: Constraint violations, empty results, timeouts
- **Performance Testing**: Batch operations and load simulation
- **AIM/PROGRESS Logging**: Day 3 activity tracking
- **Comprehensive Reporting**: JSON and JUnit XML reports
- **Retry Logic**: Automatic retry for transient failures
- **Git Automation**: Post-test commit suggestions

## 📦 Installation & Setup

```bash
# Install dependencies
npm install

# Ensure AI_integration/.env contains:
# SUPABASE_URL=your-project-url
# SUPABASE_ANON_KEY=your-anon-key
```

## 🛠️ Usage

### Run All Tests
```bash
npm test
```

### Run Database Tests Only
```bash
npm run test:db
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Generate Coverage Report
```bash
npm test -- --coverage
```

## 📋 Test Structure

### 1. Database CRUD Operations
- ✅ **INSERT**: Create specs, evaluations, iterations
- ✅ **SELECT**: Retrieve with JOINs and relations
- ✅ **UPDATE**: Modify ratings and feedback
- ✅ **DELETE**: Remove records with cascade testing

### 2. API Integration Tests
- ✅ **Spec Creation**: Via simulated POST /api/specs
- ✅ **Spec Retrieval**: Via simulated GET /api/specs
- ✅ **Evaluation Updates**: Via simulated PUT /api/evaluations
- ✅ **Iteration Creation**: Via simulated POST /api/iterations

### 3. Edge Cases & Error Scenarios
- ✅ **Invalid JSON**: Constraint violation testing
- ✅ **Rating Bounds**: 1-10 validation
- ✅ **Foreign Keys**: Referential integrity
- ✅ **Empty Results**: No data handling
- ✅ **Batch Operations**: Performance testing
- ✅ **Timeouts**: Async operation validation

### 4. Data Flow Integration
- ✅ **Complete Workflow**: Spec → Evaluation → Iteration
- ✅ **Relation Validation**: Foreign key constraints
- ✅ **Cascade Deletes**: Dependency cleanup

## 🔧 Test Configuration

### Jest Configuration (`jest.config.js`)
```javascript
module.exports = {
  testEnvironment: 'node',
  testTimeout: 30000,
  verbose: true,
  collectCoverageFrom: ['**/*.js'],
  reporters: ['default', ['jest-junit', { outputDirectory: 'test_results' }]],
  globalSetup: './test_setup.js',
  globalTeardown: './test_teardown.js'
};
```

### Test Data Structure
```javascript
const testData = {
  spec: {
    prompt: 'Test AI specification',
    json_spec: { type: 'test', components: ['db', 'api'] }
  },
  evaluation: {
    rating: 9,
    feedback: 'Excellent structure'
  },
  iteration: {
    iteration_number: 1,
    changes: { added: 'validation' },
    status: 'completed'
  }
};
```

## 📊 Test Results & Reporting

### Output Structure
```
test_results/
├── db_test_report_[timestamp].json    # Detailed JSON report
└── junit.xml                          # JUnit XML for CI/CD

coverage/
├── coverage-summary.txt
├── lcov-report/
└── html/index.html
```

### JSON Report Format
```json
{
  "summary": {
    "total": 15,
    "passed": 14,
    "failed": 1,
    "skipped": 0,
    "duration": 45230,
    "success_rate": "93.33%"
  },
  "tests": [
    {
      "test": "INSERT: Create new spec",
      "status": "passed",
      "timestamp": "2025-01-15T10:30:00.000Z",
      "specId": "uuid-here"
    }
  ],
  "generated_at": "2025-01-15T10:45:23.000Z"
}
```

### AIM/PROGRESS Logging
```json
{"timestamp":"2025-01-15T10:30:00.000Z","type":"AIM","day":3,"note":"Running comprehensive database tests..."}
{"timestamp":"2025-01-15T11:15:00.000Z","type":"PROGRESS","day":3,"note":{"done":["database_tests_passed","api_integration_validated"],"failed":[],"grateful":"Successfully validated all database operations and API integrations"}}
```

## 🔄 API Integration Simulation

### AnmolAPIStub Class
Simulates backend API calls for integration testing:

```javascript
class AnmolAPIStub {
  async createSpec(specData) {
    // Simulates POST /api/specs
    const result = await supabase.from('specs').insert(specData);
    return { success: !result.error, data: result.data, endpoint: 'POST /api/specs' };
  }

  async getSpecs() {
    // Simulates GET /api/specs
    const result = await supabase.from('specs').select('...');
    return { success: !result.error, data: result.data, endpoint: 'GET /api/specs' };
  }
}
```

### Integration Test Flow
1. **Create Spec** via API stub
2. **Verify Creation** in database
3. **Add Evaluation** via API stub
4. **Add Iteration** via API stub
5. **Retrieve Complete Data** with JOINs
6. **Validate Relationships** and constraints

## 🚨 Error Handling & Recovery

### Retry Logic
- **Max Retries**: 2 additional attempts
- **Backoff Strategy**: 1s, 2s delays
- **Transient Errors**: Network timeouts, temporary locks
- **Permanent Errors**: Constraint violations, auth failures

### Test Failure Handling
- **Descriptive Messages**: Clear error descriptions
- **Stack Traces**: Full error context
- **Report Generation**: Always generates reports even on failure
- **Cleanup**: Automatic test data removal

### Assertions & Validation
```javascript
// Example assertion with descriptive message
expect(data.id).toBeDefined();
expect(data.prompt).toBe(testData.spec.prompt);
// On failure: "Expected data.id to be defined"
```

## 📈 Performance & Load Testing

### Batch Operations Test
```javascript
test('Batch insert performance', async () => {
  const batchSize = 5;
  const batchSpecs = Array.from({ length: batchSize }, (_, i) => ({
    prompt: `Batch spec ${i + 1}`,
    json_spec: { type: 'batch_test', index: i },
    user_id: TEST_USER_ID
  }));

  const startTime = Date.now();
  const { data, error } = await supabase
    .from('specs')
    .insert(batchSpecs)
    .select();

  const duration = Date.now() - startTime;
  expect(data).toHaveLength(batchSize);
  // Performance assertion: expect(duration).toBeLessThan(5000);
});
```

### Timeout Simulation
```javascript
test('Timeout simulation', async () => {
  const startTime = Date.now();

  const { data, error } = await supabase
    .from('specs')
    .select('*, evaluations (*), iterations (*)')
    .eq('user_id', TEST_USER_ID);

  const duration = Date.now() - startTime;
  expect(duration).toBeLessThan(10000); // 10 second timeout
});
```

## 🔧 Environment & Configuration

### Required Environment Variables
```env
# Supabase Connection
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Test Configuration
NODE_ENV=test
```

### Test User Isolation
- **Test User ID**: `test-user-${timestamp}`
- **Automatic Cleanup**: Test data removed after each test
- **Isolation**: Tests don't affect production data

## 📊 Sample Test Run Output

```
🚀 Setting up test environment...
✅ Test environment setup complete

PASS supabase_db_tests.js
Database CRUD Operations
  ✅ INSERT: Create new spec (1203ms)
  ✅ SELECT: Retrieve spec with joins (543ms)
  ✅ INSERT: Create evaluation (432ms)
  ✅ INSERT: Create iteration (321ms)
  ✅ UPDATE: Modify evaluation rating (298ms)
  ✅ DELETE: Remove evaluation (245ms)

API Integration Tests
  ✅ Anmol API: Create spec via endpoint (987ms)
  ✅ Anmol API: Retrieve specs via endpoint (654ms)
  ✅ Anmol API: Update evaluation via endpoint (543ms)
  ✅ Anmol API: Create iteration via endpoint (432ms)

Edge Cases & Error Scenarios
  ✅ Invalid JSON spec constraint (123ms)
  ✅ Rating constraint violation (98ms)
  ✅ Foreign key constraint violation (87ms)
  ✅ Empty results handling (76ms)
  ✅ Batch insert performance (1456ms)
  ✅ Timeout simulation (234ms)

Data Flow Integration
  ✅ Complete data flow: Spec → Evaluation → Iteration (1876ms)

Test Suites: 1 passed, 1 total
Tests: 15 passed, 15 total
Time: 12.34s

📊 Test report saved to: test_results/db_test_report_1736901234567.json
📈 Test Results: 15/15 passed (100.00%)
✅ User confirmation received. Storage setup is complete!

🔄 Git Commands for Results:
git add test_results/ coverage/
git commit -m "✅ Database QA tests passed - Day 3 completion"
git push origin main
```

## 🎯 Integration with CI/CD

### GitHub Actions Example
```yaml
name: Database Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run test:db
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
      - uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test_results/
```

### JUnit XML Integration
```xml
<testsuites>
  <testsuite name="Supabase Database Tests" tests="15" failures="0" time="12.34">
    <testcase name="INSERT: Create new spec" time="1.203"/>
    <testcase name="SELECT: Retrieve spec with joins" time="0.543"/>
    <!-- ... more test cases ... -->
  </testsuite>
</testsuites>
```

## 🚀 Advanced Usage

### Custom Test Data
```javascript
// Override test data for specific scenarios
const customTestData = {
  spec: {
    prompt: 'Custom test specification',
    json_spec: { type: 'custom', features: ['advanced'] }
  }
};
```

### Selective Test Running
```bash
# Run only CRUD tests
npm test -- --testNamePattern="CRUD"

# Run only API integration tests
npm test -- --testNamePattern="API Integration"

# Run only edge case tests
npm test -- --testNamePattern="Edge Cases"
```

### Debug Mode
```bash
# Enable verbose logging
DEBUG=test npm test

# Run single test with details
npm test -- --verbose --testNamePattern="specific test name"
```

## 📋 Best Practices

### Test Organization
1. **Descriptive Names**: Clear, specific test names
2. **Independent Tests**: No test dependencies
3. **Cleanup**: Always clean up test data
4. **Assertions**: Multiple assertions per test when logical

### Performance Guidelines
1. **Reasonable Timeouts**: 30 seconds for database operations
2. **Batch Sizes**: Test realistic batch operations
3. **Load Simulation**: Include performance expectations
4. **Resource Cleanup**: Proper teardown and cleanup

### Error Handling
1. **Descriptive Messages**: Clear failure explanations
2. **Retry Logic**: Handle transient failures
3. **Logging**: Comprehensive error logging
4. **Recovery**: Graceful failure handling

## 🔧 Troubleshooting

### Common Issues

**"Supabase connection failed"**
- ✅ Check SUPABASE_URL and SUPABASE_ANON_KEY
- ✅ Verify AI_integration/.env exists
- ✅ Check network connectivity

**"Test timeout"**
- ✅ Increase testTimeout in jest.config.js
- ✅ Check database performance
- ✅ Reduce batch sizes for slower connections

**"RLS policy violation"**
- ✅ Ensure test user has proper permissions
- ✅ Check RLS policies are applied
- ✅ Verify user_id is set correctly

**"Constraint violation"**
- ✅ Check test data matches schema requirements
- ✅ Verify foreign key relationships
- ✅ Ensure unique constraints aren't violated

### Debug Commands
```bash
# Check test environment
node test_setup.js

# Run with debug logging
DEBUG=* npm test

# Check test results
cat test_results/db_test_report_*.json | jq '.summary'
```

## 🎉 Success Criteria

After running tests successfully, verify:

- ✅ **All Tests Pass**: 15/15 tests completed
- ✅ **Report Generated**: JSON and JUnit reports created
- ✅ **Coverage Report**: Code coverage metrics available
- ✅ **AIM/PROGRESS Logged**: Day 3 activities recorded
- ✅ **Git Commands Provided**: Automated commit suggestions
- ✅ **API Integration Validated**: All endpoints tested
- ✅ **Constraints Verified**: Database integrity confirmed
- ✅ **Performance Acceptable**: All operations within timeouts

---

**Ready to validate your database operations? Run `npm run test:db` to begin the comprehensive QA testing!** 🚀

This test suite provides enterprise-grade QA automation for your Supabase database and API integrations, ensuring reliability and performance for the AI Integration Platform.