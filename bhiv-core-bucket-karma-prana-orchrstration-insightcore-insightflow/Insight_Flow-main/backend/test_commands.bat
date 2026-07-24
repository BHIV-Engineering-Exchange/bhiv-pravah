@echo off
REM test_commands.bat - Windows batch file for running tests

echo === InsightFlow Test Commands ===
echo.

echo 1. Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html
echo.

echo 2. Run specific test categories
echo Running Phase 1 - Adapter tests...
pytest tests/adapters/ -v
echo.

echo Running Phase 1 - Validator tests...
pytest tests/validators/ -v
echo.

echo Running Phase 2 - Service tests...
pytest tests/services/ -v
echo.

echo Running Phase 2 - ML tests...
pytest tests/ml/ -v
echo.

echo Running Phase 3 - Integration tests...
pytest tests/integration/ -v
echo.

echo Running Phase 3 - Performance tests...
pytest tests/performance/ -v
echo.

echo 3. Run with detailed output
pytest tests/ -vv -s
echo.

echo 4. Show slowest tests
pytest tests/ -v --durations=10
echo.

echo === Test Commands Complete ===