# UK Postcode API Development Guide for AI Agents

## Project Overview

This is a FastAPI backend application for UK postcode geocoding. It loads 1.7M UK postcodes into memory at startup and provides instant O(1) coordinate lookups via a simple REST API. The codebase follows strict conventions for code quality, testing patterns, and maintainability.

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Code Style Guidelines](#code-style-guidelines)
3. [Test Development Rules](#test-development-rules)
4. [Development Workflow](#development-workflow)
5. [Common Commands](#common-commands)

---

## Project Architecture

### Memory Management

**The PostcodeService is initialized ONCE at app startup and reused for all requests.**

```python
# app/main.py
postcode_service: PostcodeService | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global postcode_service
    # Load all postcodes at startup (~2 seconds, ~200MB memory)
    postcode_service = PostcodeService(settings.postcode_file_1, settings.postcode_file_2)
    yield
```

**Key Facts:**
- Memory usage: ~200MB for 1.7M postcodes (fits in Heroku 1X's 512MB)
- Startup time: ~2 seconds to load both msgpack files
- Lookup speed: O(1) dict lookup, <1ms per request
- Thread-safe: Single dict, read-only operations

### Performance Characteristics

- **Startup**: Loads 1.7M postcodes from msgpack files in ~2 seconds
- **Memory**: ~200MB constant (read-only, no leaks)
- **Lookup**: O(1) dictionary lookup, <1ms
- **Throughput**: Thousands of requests per second

---

## Code Style Guidelines

### General Requirements

- Use type hints throughout the codebase
- Follow PEP 8 style guidelines with 120 character line limit
- Write comprehensive tests for new functionality
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Handle errors gracefully with appropriate HTTP status codes
- Use dependency injection for services

### Import Rules

#### No Function-Level Imports

**Never use imports inside functions. All imports must be at the module level.**

**Avoid local/in-function imports unless there is a specific technical issue that requires it (e.g., circular imports).**

##### ✅ Correct - Module-level imports
```python
import logging
import os
from typing import Dict, Tuple

import msgpack

logger = logging.getLogger(__name__)

def load_postcodes(file_path: str) -> Dict[str, str]:
    with open(file_path, 'rb') as f:
        return msgpack.unpack(f, use_list=False)
```

##### ❌ Wrong - Function-level imports
```python
def load_postcodes(file_path: str) -> Dict[str, str]:
    import msgpack  # Wrong - import inside function
    with open(file_path, 'rb') as f:
        return msgpack.unpack(f, use_list=False)
```

### Documentation Rules

#### Use Docstrings, Not Comments

**Always use docstrings for function and class documentation. Only use comments for complex code that requires explanation.**

##### ✅ Good - Using docstrings with minimal comments
```python
def lookup(self, postcode: str) -> Tuple[float, float] | None:
    """Look up coordinates for a postcode.
    
    Args:
        postcode: The postcode to look up (e.g., "SW8 5EL" or "sw85el")
        
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    clean_pc = postcode.lower().replace(' ', '')
    if not clean_pc:
        return None
    
    encoded_coords = self.postcodes.get(clean_pc)
    if not encoded_coords:
        return None
    
    lat_str, lng_str = encoded_coords.split(' ')
    lat = round(float(lat_str) + 49.5, 3)
    lng = round(float(lng_str) - 8.5, 3)
    
    return lat, lng
```

##### ❌ Bad - Excessive comments
```python
def lookup(self, postcode: str) -> Tuple[float, float] | None:
    # Clean the postcode
    clean_pc = postcode.lower().replace(' ', '')  # Remove spaces and lowercase
    if not clean_pc:  # Check if empty
        return None
    
    # Look up in dict
    encoded_coords = self.postcodes.get(clean_pc)  # Get coords from dict
    # ... etc
```

### Line Length and Formatting

**Use a maximum line length of 120 characters. Do not unnecessarily break lines shorter than 120 characters.**

##### ✅ Good - Appropriate line breaking
```python
# Line under 120 chars - keep on one line
response = client.post('/api/', json=['SW8 5EL', 'W1J 7BU'], headers={'Authorization': 'Token testing'})

# Line over 120 chars - break appropriately
very_long_postcode_list = [
    'SW8 5EL', 'W1J 7BU', 'N7 7AJ', 'IG10 4QE', 'SW8 5JB', 
    'DD6 9DD', 'L3 9BE', 'KY99 4BS', 'LL47 6TJ', 'SS2 5JA'
]
```

---

## Test Development Rules

### 1. Test URL Generation Rules

**ALWAYS use `client.app.url_path_for()` in tests instead of hardcoded URLs.**

This ensures tests are resilient to route changes and makes the codebase more maintainable.

#### ✅ Good - Using url_path_for in tests
```python
def test_get_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get(client.app.url_path_for('health_check'))
    assert response.status_code == 200
```

#### ❌ Bad - Hardcoded URLs in tests
```python
def test_get_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get('/health')  # Hardcoded - will break if route changes
    assert response.status_code == 200
```

### 2. Test Coverage Requirements

**Maintain high test coverage for the entire application.**

```bash
# Run tests with coverage
make test-cov
```

#### Coverage Targets

- **Overall Coverage**: Aim for >90%
- **API Endpoints**: 100% coverage for all endpoints
- **Service Logic**: 100% coverage for PostcodeService

### 3. Test Code Style Rules

#### No Comments in Tests Except Docstrings

**Tests should have NO comments other than docstrings at the top of functions.**

##### ❌ Wrong - Unnecessary inline comments
```python
def test_post_correct_postcode(client, auth_headers):
    """Test POST with valid postcode returns coordinates."""
    r = client.post('/api/', json=['sw81hl'], headers=auth_headers)  # Make request
    assert r.status_code == 200  # Check status
    
    data = r.json()  # Get response data
    assert 'sw81hl' in data['results']  # Check postcode in results
```

##### ✅ Correct - Clean code without unnecessary comments
```python
def test_post_correct_postcode(client, auth_headers):
    """Test POST with valid postcode returns coordinates."""
    r = client.post('/api/', json=['sw81hl'], headers=auth_headers)
    assert r.status_code == 200
    
    data = r.json()
    assert 'sw81hl' in data['results']
    assert data['results']['sw81hl'] == [51.475, -0.121]
```

### 4. Test Data Structure Rules

**Always check the entire data structure in test responses, not just individual keys.**

When testing JSON responses, assert against the complete response structure to catch unexpected fields, missing fields, or structural changes. This makes tests more robust and catches regressions early.

##### ✅ Good - Checking complete structure
```python
def test_post_empty_postcode(client: TestClient, auth_headers: dict):
    """Test POST with empty postcode returns error."""
    r = client.post(client.app.url_path_for('lookup-postcodes'), json=[''], headers=auth_headers)
    assert r.status_code == 200
    
    data = r.json()
    assert data == {
        'results': {},
        'errors': {'': "No result for ''"}
    }
```

##### ❌ Bad - Checking only individual keys
```python
def test_post_empty_postcode(client: TestClient, auth_headers: dict):
    """Test POST with empty postcode returns error."""
    r = client.post(client.app.url_path_for('lookup-postcodes'), json=[''], headers=auth_headers)
    assert r.status_code == 200
    
    data = r.json()
    assert data['errors'][''] == "No result for ''"
    # Missing check for results being empty
    # Missing check for unexpected fields
```

##### ⚠️ Acceptable - Partial checks for large or dynamic responses
For responses with dynamic fields (like timestamps or IDs), you can check specific fields:
```python
def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    r = client.get(client.app.url_path_for('health-check'))
    assert r.status_code == 200
    
    data = r.json()
    assert data['status'] == 'healthy'
    assert 'postcodes_loaded' in data  # Dynamic value, just check it exists
```

### 5. Mocking Patterns

**Always use `@patch` as a decorator instead of inline `with patch()` blocks.**

##### ✅ Good - Using @patch decorator
```python
from unittest.mock import patch

@patch('app.services.postcode_lookup.msgpack.unpack')
def test_load_data_with_mock(mock_unpack):
    """Test data loading with mocked msgpack."""
    mock_unpack.return_value = {'test': '1.0 2.0'}
    
    service = PostcodeService('file1.mp', 'file2.mp')
    assert len(service.postcodes) > 0
```

---

## Development Workflow

1. **Before making changes**: Read existing code to understand patterns
2. **When adding features**: Follow existing patterns for consistency
3. **After making changes**: Run tests and linting
4. **Before committing**: Ensure all tests pass and code is formatted

### Error Handling

Use appropriate HTTP status codes and clear error messages:

```python
from fastapi import HTTPException, status

@router.post('/api/')
async def lookup_postcodes(postcodes: List[str]):
    if not isinstance(postcodes, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='The JSON you submit should be a simple list of postcodes'
        )
    
    results, errors = service.lookup_batch(postcodes)
    return {'results': results, 'errors': errors}
```

---

## Common Commands

### Development

```bash
# Install dependencies
make install-dev

# Run development server
make run-dev

# Update postcode data
make update-postcodes
```

### Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
uv run pytest tests/test_postcodes.py -v
```

### Linting and Formatting

```bash
# Check code style
make lint

# Auto-fix and format code
make format

# Check specific files
uv run ruff check app/ tests/
```

### Cleanup

```bash
# Remove cache files
make clean
```

---

## Important Notes for AI Agents

1. **Never modify PostcodeService initialization** - it's optimized for Heroku 1X (512MB RAM)
2. **Memory is fixed at ~200MB** - all postcodes loaded at startup, not per-request
3. **Run tests after changes** to ensure nothing breaks
4. **Use type hints** - they help with code completion and catch errors early
5. **Follow existing patterns** - look at similar code in the project for consistency
6. **Never create files unless absolutely necessary** for achieving your goal
7. **Always prefer editing an existing file** to creating a new one
8. **Never proactively create documentation files** unless explicitly requested

## Project Structure

```
uk-postcode-api/
├── app/
│   ├── api/              # FastAPI routes (postcodes.py)
│   ├── core/             # Configuration and logging
│   ├── services/         # PostcodeService (in-memory lookup)
│   ├── data/             # Msgpack files (postcodes_1.mp, postcodes_2.mp)
│   └── main.py           # FastAPI application entry point
├── tests/                # Pytest test files
│   ├── conftest.py       # Test fixtures
│   └── test_postcodes.py # API and service tests
├── scripts/              # Utility scripts
│   └── update_postcodes.py  # Download and process postcode data
├── .github/workflows/    # CI/CD automation
│   ├── ci.yml           # Test and lint on PRs
│   └── update-postcodes.yml  # Weekly data updates
├── Makefile             # Development commands
└── pyproject.toml       # Project dependencies and configuration
```

## Key Dependencies

- **FastAPI**: Web framework with automatic OpenAPI docs
- **Pydantic**: Data validation and settings management
- **msgpack**: Binary serialization format for postcode data
- **pytest**: Testing framework
- **ruff**: Fast Python linter and formatter
- **uvicorn**: ASGI server
- **gunicorn**: Production WSGI server (for Heroku)
- **logfire**: Observability and monitoring (optional)
- **sentry-sdk**: Error tracking (optional)

## Performance Considerations

### Memory Usage
- Total: ~200MB for 1.7M postcodes
- File 1: ~918k postcodes (a-l)
- File 2: ~850k postcodes (m-z)
- Perfect for Heroku 1X (512MB total)

### Startup Time
- ~2 seconds to load both msgpack files
- Data stays in memory for app lifetime
- No re-loading on requests

### Lookup Performance
- O(1) dictionary lookup
- <1ms per postcode
- Handles thousands of requests/second

---

This guide ensures consistency, maintainability, and quality across the UK Postcode API codebase. Always reference this document when working on the project to maintain coding standards and patterns.

