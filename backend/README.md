# PG-VENV Backend

A smart camera roll application with vector powered semantic search.

## Features

- FastAPI backend with async support
- PostgreSQL with pgvector for semantic search
- AI/ML integration with Google Gemini and OpenAI
- JWT authentication system
- Redis caching
- Image processing with OpenCV

## Installation

Run the setup script from the project root:

```bash
./setup.sh
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check
```

Run type checking:

```bash
mypy .
```
