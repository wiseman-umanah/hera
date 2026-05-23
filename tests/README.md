# Testing Guide

This directory contains pytest tests for the HBAR Coffee Shop agent application.

## Setup

Install test dependencies:

```bash
uv sync --all-extras
# or
uv pip install -e ".[dev]"
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_config.py
```

Run specific test class:
```bash
pytest tests/test_tools.py::TestGetMenuTool
```

Run specific test:
```bash
pytest tests/test_tools.py::TestGetMenuTool::test_get_menu_returns_string
```

Run with verbose output:
```bash
pytest -v
```

Run tests and display print statements:
```bash
pytest -s
```

## Test Structure

- **test_config.py** - Tests for menu configuration and settings validation
  - Menu items, prices, categories
  - Environment variable loading and validation

- **test_tools.py** - Tests for agent tools
  - `get_menu()` - Menu display
  - `calculate_order()` - Order calculation and validation
  - `check_balance()` - Balance checking with Mirror Node
  - `make_transfer_tool()` - Payment tool factory

- **test_app.py** - Tests for FastAPI endpoints and WebSocket
  - Config endpoint (`/api/config`)
  - Balance endpoint (`/api/balance/{account_id}`)
  - Transaction ID extraction
  - Payment session management
  - WebSocket message handling

- **test_agent.py** - Tests for agent initialization
  - Agent factory function
  - Configuration with user context

## Coverage

The test suite covers:

- **Configuration (test_config.py)**
  - ✅ Menu structure and prices
  - ✅ Settings loading from environment
  - ✅ Validation error handling

- **Tools (test_tools.py)**
  - ✅ Menu tool output
  - ✅ Order calculation with various inputs
  - ✅ Balance checking (sufficient/insufficient)
  - ✅ API error handling
  - ✅ Transfer tool creation and error handling

- **API Endpoints (test_app.py)**
  - ✅ Config endpoint
  - ✅ Health checks
  - ✅ Balance queries
  - ✅ Payment session lifecycle
  - ✅ Message extraction and formatting

- **Agent (test_agent.py)**
  - ✅ Agent creation
  - ✅ User context initialization

## Mocking Strategy

Tests use `unittest.mock` to:
- Mock external API calls (httpx, Mirror Node)
- Mock Hedera SDK components
- Mock LLM calls
- Mock WebSocket connections

This allows tests to run quickly without external dependencies.

## CI/CD Integration

To add to your CI/CD pipeline:

```bash
pytest --cov=. --cov-report=xml
```

Or in a workflow file:

```yaml
- name: Run tests
  run: pytest -v --tb=short
```

## Adding New Tests

When adding new features:

1. Create a new test class following the naming pattern: `Test<FeatureName>`
2. Use descriptive test names: `test_<scenario>_<expected_behavior>`
3. Mock external dependencies (API calls, database, etc.)
4. Use fixtures from `conftest.py` for common setup

Example:

```python
def test_new_feature_handles_edge_case(self):
    """Test that new feature properly handles X edge case."""
    # Arrange
    input_data = {...}
    expected = {...}
    
    # Act
    result = new_feature(input_data)
    
    # Assert
    assert result == expected
```

## Debugging Tests

Run a single test with detailed output:
```bash
pytest tests/test_config.py::TestMenu::test_menu_items_exist -vvs
```

Use pdb breakpoints in tests:
```python
def test_something():
    import pdb; pdb.set_trace()
    # ... test code
```

Or use pytest's built-in debugger:
```bash
pytest --pdb tests/test_config.py::TestMenu::test_menu_items_exist
```
