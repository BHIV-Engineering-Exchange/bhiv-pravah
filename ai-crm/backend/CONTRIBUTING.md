# Contributing to AI Agent Logistics System

Thank you for your interest in contributing to the AI Agent Logistics System! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic understanding of FastAPI, Streamlit, and SQLAlchemy

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-agent-logistics.git
   cd ai-agent-logistics
   ```

2. **Set up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your development settings
   ```

4. **Run Tests**
   ```bash
   python run_tests.py
   ```

## 📋 How to Contribute

### Reporting Issues
- Use the GitHub issue tracker
- Include detailed description and reproduction steps
- Add relevant labels (bug, enhancement, question, etc.)

### Feature Requests
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Discuss the proposed implementation

### Code Contributions

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   python run_tests.py
   pytest --cov=. --cov-report=html
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add: descriptive commit message"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use the pull request template
   - Link related issues
   - Add a clear description of changes

## 📝 Coding Standards

### Python Style
- Follow PEP 8
- Use type hints where possible
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Code Structure
```python
# Good example
def process_restock_request(
    product_id: str, 
    quantity: int, 
    confidence_score: float
) -> RestockResult:
    """Process a restock request with validation."""
    if confidence_score < CONFIDENCE_THRESHOLD:
        return escalate_to_human_review(product_id, quantity)
    
    return create_restock_order(product_id, quantity)
```

### Documentation
- Add docstrings to all functions and classes
- Update README.md for significant changes
- Comment complex logic
- Keep API documentation current

### Testing
- Write unit tests for new functions
- Add integration tests for new features
- Maintain test coverage above 70%
- Use meaningful test names

```python
def test_restock_agent_creates_order_for_high_confidence():
    """Test that restock agent creates order when confidence > threshold."""
    # Arrange
    agent = RestockAgent()
    high_confidence_data = {...}
    
    # Act
    result = agent.process(high_confidence_data)
    
    # Assert
    assert result.status == "approved"
    assert result.order_created is True
```

## 🏗️ Project Structure

```
ai-agent_project/
├── agent.py                 # Main restock agent
├── procurement_agent.py     # Procurement automation
├── delivery_agent.py        # Delivery management
├── api_app.py              # FastAPI backend
├── dashboard_app.py        # Streamlit dashboard
├── database/
│   ├── models.py           # SQLAlchemy models
│   └── service.py          # Database services
├── tests/
│   ├── test_agent.py       # Agent tests
│   ├── test_api.py         # API tests
│   └── test_integration.py # Integration tests
└── docs/                   # Documentation
```

## 🧪 Testing Guidelines

### Test Categories
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **API Tests**: Test API endpoints
- **End-to-End Tests**: Test complete workflows

### Running Tests
```bash
# All tests
python run_tests.py

# Specific test file
pytest tests/test_agent.py -v

# With coverage
pytest --cov=. --cov-report=html

# Specific test
pytest tests/test_agent.py::test_restock_agent_processes_returns -v
```

## 📖 Documentation

### Code Documentation
- Use Google-style docstrings
- Include parameter types and return types
- Add usage examples for complex functions

### API Documentation
- Update OpenAPI schemas for new endpoints
- Include request/response examples
- Document error codes and messages

### User Documentation
- Update USER_MANUAL.md for user-facing changes
- Add screenshots for UI changes
- Keep README.md current

## 🔄 Development Workflow

### Branch Naming
- `feature/feature-name` - New features
- `bugfix/issue-description` - Bug fixes
- `hotfix/critical-fix` - Critical production fixes
- `docs/documentation-update` - Documentation only

### Commit Messages
Use conventional commits format:
```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting changes
- refactor: code refactoring
- test: adding tests
- chore: maintenance tasks
```

Examples:
```bash
git commit -m "feat(agent): add confidence scoring for restock decisions"
git commit -m "fix(api): resolve authentication token validation issue"
git commit -m "docs(readme): update installation instructions"
```

## 🚀 Release Process

### Version Numbering
Follow Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files
- [ ] Tagged release in Git

## 🤝 Community

### Getting Help
- 💬 Discussions: Use GitHub Discussions
- 🐛 Issues: Report bugs via GitHub Issues
- 📧 Email: For security issues only

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow GitHub's Community Guidelines

## 🏆 Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor discussions

## 📋 Checklist for Pull Requests

- [ ] Code follows project style guidelines
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Self-review completed
- [ ] Linked to related issues
- [ ] Screenshots added (if UI changes)

Thank you for contributing to making logistics automation better! 🚀