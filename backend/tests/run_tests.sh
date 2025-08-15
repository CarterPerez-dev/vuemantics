#!/bin/bash
# Test runner script for backend tests
# Usage: ./run_tests.sh [options]

set -e

# Find project root (where .env.test should be)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Load test environment variables
if [ -f "$PROJECT_ROOT/.env.test" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env.test" | xargs)
fi

# Load local test overrides if they exist
if [ -f "$PROJECT_ROOT/.env.test.local" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env.test.local" | xargs)
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 PG-VENV Backend Test Runner${NC}"
echo "================================"

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --no-coverage   Skip coverage report"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${RED}PostgreSQL is not running!${NC}"
    echo "Please start PostgreSQL or run: make dev"
    exit 1
fi

# Check if Redis is running
echo -e "${YELLOW}Checking Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}Redis is not running!${NC}"
    echo "Please start Redis or run: make dev"
    exit 1
fi

# Create test database if it doesn't exist
echo -e "${YELLOW}Setting up test database...${NC}"
PGPASSWORD=devpassword psql -h localhost -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'multimodal_test'" | grep -q 1 || \
PGPASSWORD=devpassword psql -h localhost -U postgres -c "CREATE DATABASE multimodal_test"

# Build pytest command
PYTEST_CMD="pytest"

# Add test type filter
case $TEST_TYPE in
    unit)
        PYTEST_CMD="$PYTEST_CMD -m unit"
        echo -e "${GREEN}Running unit tests only...${NC}"
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD -m integration"
        echo -e "${GREEN}Running integration tests only...${NC}"
        ;;
    *)
        echo -e "${GREEN}Running all tests...${NC}"
        ;;
esac

# Add coverage if enabled
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term-missing:skip-covered --cov-fail-under=0"
fi

# Add verbose if enabled
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add color
PYTEST_CMD="$PYTEST_CMD --color=yes"

echo "================================"
echo -e "${YELLOW}Running: $PYTEST_CMD${NC}"
echo "================================"

# Run tests
if $PYTEST_CMD; then
    echo "================================"
    echo -e "${GREEN}✅ All tests passed!${NC}"

    if [ "$COVERAGE" = true ]; then
        echo -e "${YELLOW}Coverage report generated in htmlcov/index.html${NC}"
    fi
else
    echo "================================"
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi
