# AI Assistant System Instructions - Multimodal Search Project

## Project Overview
You are building a multimodal search system where users can upload images/videos and search them using natural language descriptions. The system uses Gemini AI to analyze media content, OpenAI embeddings for semantic search, and PostgreSQL with pgvector for storage.

## Core Development Principles

### 1. Python Standards (STRICT REQUIREMENTS)
- **Python Version**: Use Python 3.10+ syntax exclusively
- **Type Hints**: ALWAYS include type hints for all functions, methods, and variables
  ```python
  # CORRECT
# DON'T use old typing imports for built-ins:
# from typing import Dict, List, Tuple, Set, Optional, Union

# DO use modern syntax:
names: list[str] = ["alice", "bob"]
scores: dict[str, int] = {"alice": 100}
coords: tuple[float, float] = (1.0, 2.0)
tags: set[str] = {"python", "fastapi"}

# Optional types use | None
name: str | None = None  # NOT Optional[str]
age: int | None = None   # NOT Optional[int]

# Unions use |
id_value: str | int = "abc123"  # NOT Union[str, int]
result: dict | list | None = None  # NOT Union[Dict, List, None]

# Still import these when needed:
from typing import Any, Callable, TypeVar, Protocol, Literal
from collections.abc import Sequence, Mapping, Awaitable

Import Guidelines (Python 3.10+)
python# Standard library imports
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

# Type-related imports (only what's not built-in)
from typing import Any, TypeVar, Protocol, Literal, cast
from collections.abc import Sequence, Mapping, Callable

# Third-party imports
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
Type Hints Cheat Sheet (Python 3.10+)
❌ OLD (Don't Use)
pythonfrom typing import Dict, List, Optional, Union, Tuple, Set
def old_function(data: Optional[Dict[str, List[str]]]) -> Union[str, int]:
    pass
✅ NEW (Use This)
python# Only import non-built-in types
from typing import Any, Callable, TypeVar

def new_function(data: dict[str, list[str]] | None) -> str | int:
    pass

# Common patterns:
async def upload_file(
    file: UploadFile,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None
) -> dict[str, str | int | UUID]:
    pass

# Return types
def get_user() -> User | None:  # Can return User or None
def get_count() -> int:         # Always returns int
def process() -> None:          # Returns nothing (void)

  ```

- **PEP 8 Compliance**: Follow all PEP 8 conventions
  - 4 spaces for indentation (no tabs)
  - Line length max 88 characters (Black formatter standard)
  - Two blank lines between top-level definitions
  - One blank line between method definitions
  - Snake_case for functions/variables, PascalCase for classes

### 2. Architecture Patterns (MVC)
- **Models**: ALL database operations MUST be in model classes
- **Controllers**: Thin HTTP layer only - no business logic
- **Services**: Complex business logic and external API calls
- **Schemas**: Pydantic models for request/response validation

### 3. Code Quality Standards
```python
# Every function MUST have:
# 1. Type hints
# 2. Docstring with description, args, returns, raises
# 3. Error handling
# 4. Logging where appropriate but not too much

async def create_embedding(text: str) -> list[float]: -- BUT REFER TO RESPECTIVE SDK DOCUMENTION (OPENAI & GEMINI to verify you are correctly doing it)
    """
    Generate embedding vector from text using OpenAI API.
    
    Args:
        text: Text to embed (max 8191 tokens)
        
    Returns:
        1536-dimensional embedding vector
        
    Raises:
        OpenAIError: If API call fails
        ValueError: If text exceeds token limit
    """
    try:
        response = await openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise
```

### 4. Async/Await Best Practices
- Use `async/await` for all I/O operations
- Never use blocking calls in async functions
- Use `asyncio.gather()` for concurrent operations
- Always use async context managers

```python
# CORRECT
async with aiofiles.open(file_path, 'rb') as f:
    content = await f.read()

# INCORRECT
with open(file_path, 'rb') as f:
    content = f.read()  # Blocks event loop!
```

### 5. Error Handling
- Never use bare `except:` clauses - DONT BE GREEDY
- Always log errors with context - DONT BE GREEDY
- Raise appropriate HTTP exceptions in controllers - DONT BE GREEDY
MOST DEFINITLY THIS - Use custom exception classes for domain errors - MOST DEFINITLY THIS

BUT MAKE THESE VERY DETAILED - WE SHOULD HAVE MINIUM OF 8 - no more than 12
```python
class ProcessingError(Exception):
    """Base exception for processing errors"""
    pass

class UnsupportedFileTypeError(ProcessingError):
    """Raised when file type is not supported"""
    pass
```

## Project-Specific Guidelines

### 1. File Processing
- Check file size before processing (100MB limit)
- Validate MIME types against allowed list
- Generate unique IDs using `uuid.uuid4()`
- Always clean up temporary files

### 2. AI Integration
```python
# Gemini Analysis Pattern
2. AI Integration
python# Gemini Analysis Pattern
async def analyze_with_gemini(
    file_path: str, 
    file_type: str,
    max_frames: int | None = None
) -> str:
    """
    Analyze media file with Gemini and return description.
    
    Args:
        file_path: Path to media file
        file_type: Type of file ('image' or 'video')
        max_frames: Max frames to extract for video (default: 10)
        
    Returns:
        Text description of the media content
    """
    # For images: send directly
    # For videos: extract frames first (1 fps)
    # Always handle rate limits and retries
```

### 3. Database Operations
- Use connection pooling
- Always use parameterized queries
- Handle pgvector operations carefully
- Index all foreign keys and search fields

### 4. Security
- Validate all inputs with Pydantic
- Use `python-jose` for JWT, not PyJWT
- Hash passwords with bcrypt (min 12 rounds)
- Sanitize filenames before storage

## Communication Protocol

### 1. Ask Questions When:
- Architecture decisions conflict with requirements
- Performance vs simplicity tradeoffs arise
- Security implications are unclear
- Third-party service limits/costs need clarification
- User experience decisions needed

### 2. Question Format:
```markdown
**Question**: [Specific question]
**Context**: [Why this matters]
**Options**: 
1. [Option A with pros/cons]
2. [Option B with pros/cons]
**Recommendation**: [Your suggested approach and why]
```

## Progress Documentation

### 1. Checkpoint Files
Create `checkpoints/YYYY-MM-DD-checkpoint-N.md` files with:

```markdown
# Checkpoint [N] - [Date]

## Completed
- [x] Set up project structure
- [x] Implemented JWT authentication
- [x] Created base models with type hints

## Current Status
Working on: [Current task]
Blockers: [Any blockers]

## Code Statistics
- Files created: X
- Lines of code: Y
- Test coverage: Z%

## Key Decisions
1. Chose X because Y
2. Implemented Z pattern for [reason]

## Next Steps
1. [ ] Implement file upload endpoint
2. [ ] Integrate Gemini API
3. [ ] Set up pgvector search

## Questions for Review
- Should we cache embeddings in Redis?
- File storage structure: user_id/file_id ok?
```

### 2. Documentation Updates
- Update README.md with setup instructions as you go
- Document all environment variables needed
- Create API documentation with examples
- Add inline comments for complex logic only
- AFTER EACH CHECKPOINT/MILSESTONE/NEW IMPLEMENATION ETC ETC - PLEASE CREATE A DETAILED CHECKPOINT[number].md OF WHAT WE HAVE DONE, IMPORANT FILES FOR THE NEXT AI ASSISTANT TO READ FROR MAXIUMUM CONTEXT - AND NEXT STEPS!


## Git Practices
- Commit messages: "feat/fix/docs: [description]" - AFTER EACH CHECKPOINT OR MAJOR IMPLEMENTION / NEW
- Commit messages but be above instruction and not have anything liek 'claude co author' or anythinmg of the sort, make sure to 'git add .' before hand, and just have the comminit message and nothing esle in the commit mesaage - not extar fluff or irrelevance please, commit alottt!! its better to commit more than commit les!!!
- Include .gitignore from start (already created but if creating new sensitive file please add or check .gitignore to ensure its there)

## Performance Considerations
- Use Redis for caching search results
- Batch embedding requests when possible
- Implement pagination (20 items default) - but not too much as this is an MVP
- Use database indexes effectively -- and not overly greedy, only iompleennbt indexes for actuall needed indexed queires/fields
- Profile before optimizing

## When Writing Code:
1. **Think First**: Plan the approach before coding <ULTRATHINK>
2. **Type Everything**: No `Any` types unless absolutely necessary - DONT BE GREEDY
3. **Handle Errors**: Every external call needs try/except - DONT BE GREEDY
4. **Document Intent**: Why, not what!!!
5. **Test Edge Cases**: Empty files, huge files, weird formats - when we do testing tho

## Red Flags to Avoid
- Synchronous I/O in async functions
- Direct database queries in controllers
- Storing secrets in code
- Unvalidated user input
- Unbounded queries without pagination
- Missing error handling - - DONT BE GREEDY
- Type hints with `Any` everywhere - - DONT BE GREEDY

## Remember
- This is an MVP - keep it simple but maintainable
- Ask questions rather than assume
- Document decisions for future reference
- Security and correctness over premature optimization - however i prefer availabitly over security - keep in mind its an MVP and securiy can always vbe implented - too much securtyu and less availabilty fro an MVP is not good
- Code should be readable without comments - !!code shopuld be self explanatory!!

* **please now read and refer to the .context/instructions/checklist.md** 

# REMEMBER TO ALWAYS ALWAYS LIKE MY FAMILIES LIVES ARE ON THE LINE AND THEY WILL LITERALLY DIE TEH WORST DEATH IMAGINABLE IF YOU FAIL TO ALWAYS ALWAYS <ULTRATHINK>
