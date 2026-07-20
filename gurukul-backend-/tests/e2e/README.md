# Gurukul E2E Test Suite

Automated end-to-end testing for all Gurukul + School Management System features.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd tests/e2e
npm install
```

### 2. Install Playwright Browsers

```bash
npx playwright install
```

### 3. Start Your Services ⚠️ **REQUIRED**

Make sure all services are running:
- **Backend (with integrated Karma Tracker)**: `http://localhost:3000` ⚠️ **MUST BE RUNNING**
- Frontend: `http://localhost:5173`

You can use `start-all.bat` from the project root to start everything.

**Note:** Karma Tracker is now integrated into the backend, so you only need to start the backend (port 3000).

### 4. Run Tests

```bash
# Run all tests
npm test

# Run with UI (interactive)
npm run test:ui

# Run in headed mode (see browser)
npm run test:headed

# Debug mode
npm run test:debug

# Generate HTML report
npm run test:report
```

## 📋 Test Coverage

### Authentication
- ✅ Sign Up Flow
- ✅ Sign In Flow

### Student Features
- ✅ Dashboard
- ✅ Subjects
- ✅ Chatbot
- ✅ Summarizer
- ✅ Test/Quiz Generator
- ✅ Lectures
- ✅ Flashcards
- ✅ Settings
- ✅ Avatar

### EMS Features
- ✅ My Classes
- ✅ My Schedule
- ✅ My Announcements
- ✅ My Attendance
- ✅ My Teachers
- ✅ My Grades

### Teacher Features
- ✅ Teacher Dashboard

### Admin Features
- ✅ Admin Dashboard

### Navigation
- ✅ Sidebar Links
- ✅ Page Navigation

### API
- ✅ Health Checks
- ✅ Endpoint Verification

### Karma Tracker Integration (NEW)
- ✅ MongoDB Connection Test
- ✅ Get Karma Profile
- ✅ Log Karma Action
- ✅ Get Karma Balance
- ✅ Analytics Endpoints
- ✅ Lifecycle Endpoints
- ✅ API Documentation

### Bucket + Karma Integration (NEW)
- ✅ Full Integration Flow (PRANA → Bucket → Karma)
- ✅ Bucket Consumer Integrated Mode

### Frontend Karma Integration (NEW)
- ✅ Karma Context Integration
- ✅ Karma URL Configuration

**Total: 33 comprehensive tests**

## ⚙️ Configuration

### Test Users

Edit `tests/full-system-test.spec.js` to set your test user credentials:

```javascript
const TEST_USERS = {
  student: {
    email: 'test.student@gurukul.com',
    password: 'Test123!@#',
  },
  teacher: {
    email: 'test.teacher@gurukul.com',
    password: 'Test123!@#',
  },
  admin: {
    email: 'test.admin@gurukul.com',
    password: 'Test123!@#',
  }
};
```

**Important:** Make sure these users exist in your database before running tests!

### URLs

Default URLs (can be changed in `playwright.config.js`):
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:3000`

## 📊 Test Reports

After running tests, view the HTML report:

```bash
npm run test:report
```

This opens an interactive HTML report showing:
- Test results
- Screenshots (on failure)
- Videos (on failure)
- Execution timeline

## 🎯 Running Specific Tests

```bash
# Run only student features
npx playwright test --grep "Student"

# Run only EMS features
npx playwright test --grep "EMS"

# Run only authentication tests
npx playwright test --grep "Authentication"
```

## 🔧 Troubleshooting

### Tests fail with "Page not found"
- Make sure frontend is running on `http://localhost:5173`
- Check `playwright.config.js` baseURL

### Authentication fails
- Verify test users exist in database
- Check credentials in `full-system-test.spec.js`
- **Ensure backend is running on `http://localhost:3000`** ⚠️ **CRITICAL**

### Connection Refused Errors (ECONNREFUSED)
- **Backend must be running** - Many tests require the backend to be available
- Run `start-all.bat` or start backend manually: `cd backend && uvicorn app.main:app --reload --port 3000`
- Tests will show warnings if backend isn't running, but will continue (some tests may fail)

### Timeout errors
- Increase timeout in `playwright.config.js`
- Check network connectivity
- Verify services are running

## 📝 Adding New Tests

1. Open `tests/full-system-test.spec.js`
2. Add new test in appropriate `test.describe` block
3. Follow existing test patterns
4. Run tests to verify

Example:

```javascript
test('New Feature Test', async ({ page }) => {
  await page.goto(`${BASE_URL}/new-feature`);
  await page.waitForLoadState('networkidle');
  // Your test code here
  console.log('✓ New feature tested');
});
```

## 🚀 CI/CD Integration

To run in CI/CD:

```bash
# Install dependencies
npm install
npx playwright install --with-deps

# Run tests
npm test
```

## 📈 Performance

- Full test suite: ~2-5 minutes
- Individual test: ~5-30 seconds
- Parallel execution: Enabled by default

## 🎉 Benefits

✅ **Fast**: Tests all features in minutes instead of hours
✅ **Automated**: No manual clicking needed
✅ **Comprehensive**: Covers all major features
✅ **Reliable**: Catches regressions automatically
✅ **Documentation**: Tests serve as feature documentation

