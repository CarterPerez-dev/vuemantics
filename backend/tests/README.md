# PG-VENV Backend Tests

## Overview

This directory contains all tests for the PG-VENV backend application. Tests are organized into unit and integration tests, with comprehensive fixtures for database isolation and async support.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual components
│   ├── test_models_base.py    # BaseModel tests
│   ├── test_models_user.py    # User model tests
│   └── test_models_upload.py  # Upload model tests
└── integration/          # Integration tests for API endpoints
    └── test_auth_routes.py     # Authentication endpoint tests
```

## Running Tests

### Prerequisites

1. PostgreSQL must be running with pgvector extension available
2. Redis must be running
3. Test database will be created automatically

### Quick Start

```bash
# Run all tests with coverage
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -vv

# Run specific test file
pytest tests/unit/test_models_user.py

# Run specific test
pytest tests/unit/test_models_user.py::TestUserModel::test_create_user
```

### Using the Test Runner Script

```bash
# Make the script executable
chmod +x run_tests.sh

# Run all tests
./run_tests.sh

# Run only unit tests
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration

# Skip coverage report
./run_tests.sh --no-coverage

# Verbose output
./run_tests.sh --verbose
```

## Test Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_api_keys` - Tests requiring real API keys

## Key Fixtures

### Database Fixtures

- `test_db` - Test database pool (session scoped)
- `db_connection` - Database connection with transaction rollback
- `clean_tables` - Ensures clean tables before each test

### User Fixtures

- `test_user` - Creates an active test user
- `inactive_user` - Creates an inactive test user
- `make_user_data` - Factory for user test data

### Client Fixtures

- `authenticated_client` - HTTP client with valid JWT token
- `unauthenticated_client` - HTTP client without authentication

### Utility Fixtures

- `sample_embedding` - Generates 1536-dimensional test embedding
- `async_run` - Helper to run async functions in sync tests

## Test Database

Tests use a separate `multimodal_test` database that is created automatically. Each test runs in a transaction that is rolled back, ensuring complete isolation.

## Coverage

Current coverage target: 80%

View coverage report:
```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Writing New Tests

### Unit Test Example

```python
@pytest.mark.unit
class TestNewFeature:
    async def test_feature_behavior(self, db_connection: Connection):
        """Test that feature does X when Y."""
        # Arrange
        data = create_test_data()

        # Act
        result = await feature_function(data)

        # Assert
        assert result.status == "expected"
```

### Integration Test Example

```python
@pytest.mark.integration
class TestNewEndpoint:
    async def test_endpoint_success(self, authenticated_client: AsyncClient):
        """Test successful API call."""
        response = await authenticated_client.post(
            "/api/endpoint",
            json={"key": "value"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

## Debugging Tests

### Run with print statements visible
```bash
pytest -s
```

### Run with debugger
```python
import pdb; pdb.set_trace()  # Add breakpoint
```

### Check test database state
```bash
PGPASSWORD=devpassword psql -h localhost -U postgres -d multimodal_test
```

## CI/CD Integration

Tests are configured to run in CI with:
- Coverage reporting
- JUnit XML output
- Parallel execution support

## Common Issues

### PostgreSQL not running
```bash
# Start with Docker
make dev

# Or start locally
pg_ctl start
```

### Test database permission issues
```bash
# Grant permissions
PGPASSWORD=devpassword psql -h localhost -U postgres -c "GRANT ALL ON DATABASE multimodal_test TO postgres"
```

### Async test issues
- Always use `pytest-asyncio` fixtures
- Mark async tests with `async def`
- Use `await` for all async operations

## Contributing

1. Write tests for all new features
2. Maintain >80% coverage
3. Use appropriate markers
4. Follow existing patterns
5. Run tests before committing
