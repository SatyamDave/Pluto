# 🧪 Pluto AI Phone Assistant - Testing Guide

This document provides comprehensive instructions for setting up and running tests for Pluto, the AI phone assistant.

## 🚀 Quick Start

### 1. Install Testing Dependencies
```bash
# Install all testing tools
pip install -r requirements-test.txt

# Or use the test runner
python run_tests.py --install
```

### 2. Run All Tests
```bash
# Run with coverage report
python run_tests.py

# Or use pytest directly
pytest -s --cov=. --cov-report=html
```

### 3. View Results
```bash
# Open coverage report in browser
open htmlcov/index.html
```

## 📋 Test Categories

### Core Telephony Tests
- **Inbound SMS**: Webhook handling and AI response generation
- **Inbound Voice**: Call answering and TTS integration
- **Outbound SMS**: Message sending functionality
- **Outbound Calls**: Call placement and script execution

### Memory & Context Tests
- **Memory Storage**: Saving user interactions to database
- **Embedding Generation**: OpenAI integration for semantic search
- **Context Recall**: Retrieving relevant past information
- **Memory Management**: Forgetting and importance scoring

### Habit Engine Tests
- **Pattern Detection**: Identifying recurring user behaviors
- **Habit Suggestions**: Proactive recommendations
- **Confidence Scoring**: Filtering weak patterns

### Style Engine Tests
- **Tone Analysis**: Learning user communication style
- **Style Adaptation**: Matching user's personality
- **Signature Phrases**: Using learned expressions

### Proactive Agent Tests
- **Morning Digest**: Scheduled proactive messaging
- **Urgent Alerts**: Email and calendar conflict detection
- **Wake-up Calls**: Persistent reminder execution
- **Background Monitoring**: Continuous proactive checking

### Email & Calendar Tests
- **Gmail Integration**: API authentication and email fetching
- **Email Classification**: Importance and urgency detection
- **Calendar Conflicts**: Schedule conflict identification
- **Event Management**: Adding and modifying calendar events

### Confirmation Layer Tests
- **Permission Checking**: Asking before external actions
- **User Confirmation**: Respecting explicit permissions
- **Contact Preferences**: Managing auto-send settings

## 🛠️ Testing Tools

### Core Framework
- **pytest**: Main testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities

### Coverage & Quality
- **coverage.py**: Code coverage analysis
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting

### Mocking & Isolation
- **unittest.mock**: Standard library mocking
- **responses**: HTTP request mocking
- **freezegun**: Time mocking

## 📁 Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual modules
│   ├── test_memory_manager.py
│   ├── test_habit_engine.py
│   ├── test_style_engine.py
│   └── test_proactive_agent.py
├── integration/             # Integration tests
│   ├── test_telephony_integration.py
│   ├── test_memory_integration.py
│   └── test_ai_integration.py
└── e2e/                    # End-to-end tests
    ├── test_user_workflows.py
    └── test_proactive_cycles.py
```

## 🔧 Test Configuration

### Environment Variables
```bash
# Testing environment
export PLUTO_ENV=test
export PLUTO_DB_URL=postgresql://test:test@localhost:5432/pluto_test
export PLUTO_REDIS_URL=redis://localhost:6379/1
export PLUTO_OPENAI_API_KEY=test_key
export PLUTO_TWILIO_ACCOUNT_SID=test_sid
export PLUTO_TWILIO_AUTH_TOKEN=test_token
```

### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    external: Tests requiring external services
```

## 🎯 Running Specific Tests

### By Category
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# All tests with coverage
python run_tests.py
```

### By Module
```bash
# Test specific module
pytest tests/unit/test_memory_manager.py -v

# Test specific function
pytest tests/unit/test_memory_manager.py::test_store_memory -v

# Test with specific marker
pytest -m "unit and not slow" -v
```

### By Pattern
```bash
# Test files matching pattern
pytest tests/unit/test_*_manager.py -v

# Test functions matching pattern
pytest -k "memory" -v

# Exclude slow tests
pytest -m "not slow" -v
```

## 📊 Coverage Reports

### Generate Reports
```bash
# HTML report (default)
pytest --cov=. --cov-report=html

# Terminal report
pytest --cov=. --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml

# Multiple formats
pytest --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml
```

### Coverage Configuration
```ini
# .coveragerc
[run]
source = .
omit = 
    */tests/*
    */venv/*
    */env/*
    setup.py
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

## 🧹 Test Maintenance

### Clean Up
```bash
# Remove test artifacts
python run_tests.py --clean

# Or manually
rm -rf .coverage htmlcov/ .pytest_cache/ __pycache__/
```

### Update Dependencies
```bash
# Update testing packages
pip install -r requirements-test.txt --upgrade

# Check for security issues
safety check -r requirements-test.txt
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Run all quality checks
pre-commit run --all-files
```

## 🚨 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the right directory
cd /path/to/pluto-ai-terminal

# Install in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check Redis connection
redis-cli ping

# Verify environment variables
echo $PLUTO_DB_URL
echo $PLUTO_REDIS_URL
```

#### Coverage Issues
```bash
# Clear coverage data
coverage erase

# Run tests with fresh coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Check coverage configuration
coverage debug config
```

### Debug Mode
```bash
# Run with debug output
pytest -s -v --tb=long

# Run single test with debug
pytest tests/unit/test_memory_manager.py::test_store_memory -s -v --tb=long

# Use Python debugger
pytest --pdb
```

## 📈 Performance Testing

### Benchmark Tests
```bash
# Install benchmark plugin
pip install pytest-benchmark

# Run benchmarks
pytest --benchmark-only

# Compare with previous runs
pytest --benchmark-compare
```

### Load Testing
```bash
# Test with multiple concurrent users
pytest tests/load/ -n auto

# Test specific concurrency levels
pytest tests/load/ -n 4
```

## 🔒 Security Testing

### Dependency Scanning
```bash
# Check for known vulnerabilities
safety check -r requirements.txt
safety check -r requirements-test.txt

# Update vulnerable packages
safety check -r requirements.txt --full-report
```

### Code Security
```bash
# Run security linter
bandit -r .

# Check for secrets in code
detect-secrets scan
```

## 📚 Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Guide](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

### Examples
- [Test Examples](examples/testing/)
- [Mock Examples](examples/mocking/)
- [Integration Test Examples](examples/integration/)

### Support
- [GitHub Issues](https://github.com/your-repo/pluto-ai-terminal/issues)
- [Testing Channel](https://discord.gg/your-channel)
- [Documentation Wiki](https://github.com/your-repo/pluto-ai-terminal/wiki)

---

**Happy Testing! 🎉**

Remember: Good tests are the foundation of reliable software. Write tests that are:
- **Fast**: Tests should run quickly
- **Independent**: Tests shouldn't depend on each other
- **Repeatable**: Tests should give the same results every time
- **Self-validating**: Tests should have a clear pass/fail result
- **Timely**: Write tests before or alongside the code they test
