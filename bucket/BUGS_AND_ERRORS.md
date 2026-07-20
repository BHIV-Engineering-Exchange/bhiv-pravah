# 🐛 Bugs and Errors Report

This document catalogs all known bugs, errors, and issues in the AI Integration Platform.

## 🧪 Test Failures

### Pytest Issues
All pytest tests are failing due to incorrect command-line arguments:
```
ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --json-report --json-report-file=...
```

### Agent Specification Validation Issues
Multiple agents are failing validation because the test script expects a `domain` field but the agent specs use `domains` (plural):
- `cashflow_analyzer`: Missing fields: ['domain']
- `financial_coordinator`: Missing fields: ['domain']
- `goal_recommender`: Missing fields: ['domain']
- `sanskrit_parser`: Missing fields: ['domain']
- `vedic_quiz_agent`: Missing fields: ['domain']

### Sample Input Validation Issues
- `sanskrit_parser_input.json`: Character encoding error - `'charmap' codec can't decode byte 0x8d`

## ⚠️ Configuration Issues

### Agent Specification Schema Inconsistency
There's an inconsistency in the agent specification schema:
- **Expected by tests**: `domain` (singular)
- **Actual in specs**: `domains` (plural)

Example from [agents/cashflow_analyzer/agent_spec.json](file:///c%3A/Users/Microsoft/Downloads/Agents_integration-main/agents/cashflow_analyzer/agent_spec.json):
```json
{
    "name": "cashflow_analyzer",
    "domains": ["finance"],  // Should be "domain": "finance"
    // ...
}
```

### Test Script Issues
The [tests/run_tests.py](file:///c%3A/Users/Microsoft/Downloads/Agents_integration-main/tests/run_tests.py) script has several problems:
1. Uses pytest arguments (`--json-report`) that may not be available
2. Expects incorrect field names in agent specifications
3. Has encoding issues when reading certain files

## 🌐 Network and API Issues

### Law Agent External Dependency
The [law_agent](file:///c%3A/Users/Microsoft/Downloads/Agents_integration-main/agents/law_agent/agent_spec.json) relies on an external API:
- **Base URL**: `https://legal-agent-api-3yqg.onrender.com`
- **Issue**: External dependency that may be unreliable or unavailable
- **Impact**: Law agent functionality depends on external service uptime

### Render API Timeout Issues
The law agent implementation has timeout handling but may still experience:
- Connection timeouts to external service
- Slow response times from Render API
- Fallback mechanism needed for offline scenarios

## 📁 File System Issues

### Missing Log Directory
The application expects a `logs` directory that may not exist:
```
FileNotFoundError: [Errno 2] No such file or directory: 'logs/basket_runs'
```

### Path Handling Issues
Some file operations may have issues with:
- Windows path separators
- Relative vs absolute path handling
- Directory creation permissions

## 🔌 Service Integration Issues

### Redis Connection Problems
- Redis connection failures cause fallback to in-memory storage
- No clear indication of Redis status in health checks
- Potential data loss when Redis is unavailable

### MongoDB Connection Issues
- MongoDB connection failures result in file-only logging
- No automatic reconnection mechanism
- Health check may not accurately reflect database status

## 🧠 Agent Implementation Issues

### Law Agent Complexity
The [law_agent.py](file:///c%3A/Users/Microsoft/Downloads/Agents_integration-main/agents/law_agent/law_agent.py) is overly complex with:
- Multiple agent types (Basic, Adaptive, Enhanced)
- Heavy dependency on external services
- Large codebase (866 lines) making maintenance difficult
- Mixed responsibilities (FastAPI server + basket integration)

### Error Handling Inconsistencies
Different agents handle errors differently:
- Some return `{"error": "message"}`
- Others log errors and raise exceptions
- No standardized error response format

## 🧺 Basket System Issues

### Parallel Execution Not Implemented
The basket manager advertises parallel execution but falls back to sequential:
```python
async def _execute_parallel(self, input_data: Dict) -> Dict:
    """Execute agents in parallel (future implementation)"""
    # For now, fall back to sequential execution
    logger.warning("Parallel execution not yet implemented, falling back to sequential")
    return await self._execute_sequential(input_data)
```

### Resource Cleanup Issues
- Basket-specific loggers may not be properly closed
- MongoDB connections in baskets may not be cleaned up correctly
- Redis connections are shared and not managed per-basket

## 🛠️ Development Environment Issues

### Dependency Management
- Missing or incorrect pytest plugins
- Potential version conflicts between dependencies
- No clear documentation on required development tools

### Cross-Platform Compatibility
- Path handling issues on Windows (as seen in test result paths)
- Potential line ending issues in text files
- PowerShell vs. Bash command differences

## 📊 Performance Issues

### Execution Time
- Agent execution times not optimized
- No caching mechanism for repeated operations
- Sequential execution only (parallel not implemented)

### Memory Usage
- Potential memory leaks in long-running processes
- No memory usage monitoring or limits
- Large agent implementations may consume excessive resources

## 🎯 Recommendations

### Immediate Fixes
1. Fix pytest command arguments in [run_tests.py](file:///c%3A/Users/Microsoft/Downloads/Agents_integration-main/tests/run_tests.py)
2. Update agent specification validation to use `domains` instead of `domain`
3. Fix character encoding issues in sample input files
4. Ensure log directories are created before use

### Medium-term Improvements
1. Implement true parallel execution for baskets
2. Add proper fallback mechanisms for external dependencies
3. Standardize error handling across all agents
4. Improve resource cleanup and connection management

### Long-term Enhancements
1. Simplify complex agents like the law agent
2. Add comprehensive monitoring and alerting
3. Implement proper caching mechanisms
4. Add performance benchmarks and optimization