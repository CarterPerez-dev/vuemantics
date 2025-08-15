# Multimodal Search System - PG-VENV - MVP Documentation

A simplified, self-hosted multimodal search system where users can upload images/videos and search them using natural language descriptions.

## Overview

Users upload media files which are analyzed by Gemini to generate text descriptions, then embedded using OpenAI's text-embedding-3-small for semantic search via pgvector. Think of it as a smart camera roll where you can search "funny cat video" and find all your cat videos.

## Tech Stack (Simplified for MVP)

```yaml
Backend: Python 3.11 + FastAPI
Database: PostgreSQL 16 + pgvector (local Docker)
Cache: Redis (local Docker)
Storage: Local filesystem
AI Models: 
  - Gemini Pro 2.5 (multimodal analysis)
  - OpenAI text-embedding-3-small (1536 dimensions)
Auth: JWT (python-jose)
Frontend: React + TypeScript + Vite + Tailwind CSS
Infrastructure: Docker Compose + Nginx + Cloudflare
```

## Key Dependencies

```txt
# Core Framework
# ALL LATEST AS OF 07/13/2025
fastapi==0.116.1
uvicorn[standard]==0.35.0
python-multipart==0.0.20

# Database
asyncpg==0.30.0
pgvector==0.4.1
sqlalchemy==2.0.41
alembic==1.16.4

# AI/ML
google-genai==1.25.0  # New Gemini SDK - REFER TO DOCS
openai==1.95.1 # REFER TO DOCS
pillow==11.3.0
opencv-python-headless==4.12.0.88

# Authentication 
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20

# Caching
redis==5.2.0

# Utils
pydantic==2.11.7
pydantic-settings==2.10.1
python-dotenv==1.0.1
```

## Project Structure

```
Here's what goes in each file/directory:

## Backend Structure

```
backend/
├── __init__.py                    # Empty, marks directory as Python package
├── main.py                        # FastAPI app initialization, middleware, router registration
├── config.py                      # Pydantic Settings class loading from .env file
├── database.py                    # Async PostgreSQL connection, session management
├── dependencies.py                # Reusable FastAPI dependencies (get_current_user)
├── pyproject.toml                 # Python project metadata, dependencies, tool configs
│
├── auth/                          # Authentication logic
│   ├── jwt_auth.py               # JWT token creation, validation, decode functions
│   └── password.py               # Password hashing/verification with bcrypt
│
├── models/                        # Database models (SQLAlchemy/raw SQL)
│   ├── base.py                   # BaseModel class with id, created_at, updated_at
│   ├── user.py                   # User model with CRUD operations
│   └── upload.py                 # Upload model with file metadata and embeddings
│
├── routers/                       # API endpoints (controllers)
│   ├── auth.py                   # POST /register, POST /token endpoints
│   ├── upload.py                 # POST /upload, GET /uploads endpoints
│   ├── search.py                 # POST /search endpoint for semantic search
│   └── health.py                 # GET /health for container health checks
│
├── schemas/                       # Pydantic models for request/response validation
│   ├── user.py                   # UserCreate, UserResponse models
│   ├── auth.py                   # Token, TokenData, LoginRequest models
│   ├── upload.py                 # UploadResponse, UploadStatus models
│   └── search.py                 # SearchRequest, SearchResult models
│
├── services/                      # Business logic layer
│   ├── ai_service.py             # Gemini integration for media analysis
│   ├── embedding_service.py      # OpenAI embeddings generation
│   ├── search_service.py         # Vector similarity search with pgvector
│   └── storage_service.py        # Local file storage operations
│
├── utils/                         # Helper functions
│   ├── validators.py             # File type/size validation functions
│   └── helpers.py                # Misc utilities (file paths, formatting)
│
├── migrations/                    # Alembic database migrations
│
└── tests/                         # Test files
    ├── conftest.py               # Pytest fixtures (test db, client, etc)
    ├── unit/                     # Unit tests for individual functions
    └── integration/              # Integration tests for full API flows


## Frontend Structure

frontend/
├── package.json                   # Node dependencies and scripts
├── vite.config.ts                # Vite bundler configuration
├── tsconfig.json                 # TypeScript compiler options
├── tailwind.config.js            # Tailwind CSS theme customization
├── biome.json                    # Code formatter/linter rules
│
├── src/
│   ├── main.tsx                  # React app entry point, providers setup
│   ├── App.tsx                   # Root component with router
│   ├── index.css                 # Global styles, Tailwind imports
│   ├── vite-env.d.ts            # TypeScript environment variable types
│   │
│   ├── api/
│   │   └── client.ts            # Axios instance with auth interceptors
│   │
│   ├── components/               # Reusable UI components
│   │   ├── Layout.tsx           # App layout with nav/footer
│   │   ├── FileUpload.tsx       # Drag-drop upload component
│   │   ├── MediaGrid.tsx        # Grid display of uploads
│   │   └── SearchBar.tsx        # Search input with suggestions
│   │
│   ├── pages/                    # Page components (routes)
│   │   ├── Home.tsx             # Landing/search page
│   │   ├── Login.tsx            # Login form page
│   │   ├── Register.tsx         # Registration form page
│   │   ├── Dashboard.tsx        # User's uploads gallery
│   │   └── Upload.tsx           # File upload page
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── useAuth.ts           # Authentication state hook
│   │   ├── useUpload.ts         # File upload logic hook
│   │   └── useSearch.ts         # Search functionality hook
│   │
│   ├── store/
│   │   └── authStore.ts         # Zustand auth state management
│   │
│   ├── types/                    # TypeScript type definitions
│   │   ├── api.ts               # API response types
│   │   └── models.ts            # Data model interfaces
│   │
│   └── utils/                    # Helper functions
│       ├── formatters.ts        # Date/size formatting
│       └── validators.ts        # Form validation helpers
```


## Database Schema (Simplified)

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Main uploads table
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- File information
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,  -- Local path instead of GCS
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('image', 'video')),
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    
    -- Processing
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    gemini_summary TEXT,
    embedding vector(1536),
    
    -- Metadata
    thumbnail_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_embedding ON uploads USING ivfflat (embedding vector_cosine_ops);
```

## Authentication (JWT-based)

```python
# auth/jwt_auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings from .env
SECRET_KEY = settings.secret_key  # Generate with: openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await User.find_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
```

## Local File Storage

```python
# services/storage.py
import os
import shutil
from pathlib import Path
from typing import BinaryIO

class LocalStorageService:
    """Simple local file storage"""
    
    def __init__(self, base_path: str = "./storage/uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: BinaryIO, user_id: str, file_id: str, filename: str) -> str:
        """Store file locally and return path"""
        # Create user directory
        user_path = self.base_path / str(user_id)
        user_path.mkdir(exist_ok=True)
        
        # Create file directory
        file_path = user_path / str(file_id)
        file_path.mkdir(exist_ok=True)
        
        # Save file
        full_path = file_path / filename
        with open(full_path, 'wb') as f:
            shutil.copyfileobj(file, f)
        
        return str(full_path)
    
    def get_file_url(self, file_path: str) -> str:
        """Get URL for nginx to serve file"""
        # Nginx will serve from /files/...
        relative_path = Path(file_path).relative_to(self.base_path)
        return f"/files/{relative_path}"
```

## Configuration (.env file)

```bash
# .env
# Application
APP_NAME="Multimodal Search"
ENVIRONMENT="development"
DEBUG=True

# Database
DATABASE_URL="postgresql://postgres:password@localhost:5432/multimodal_search"

# Redis
REDIS_URL="redis://localhost:6379"

# JWT Auth
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs
OPENAI_API_KEY="your-openai-key"
GEMINI_API_KEY="your-gemini-key"

# Storage
UPLOAD_PATH="./storage/uploads"
MAX_UPLOAD_SIZE=104857600  # 100MB
```

## Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: multimodal_search
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./storage:/app/storage
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/multimodal_search
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: uvicorn main:app --host 0.0.0.0 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./storage/uploads:/var/www/uploads
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
```

## Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        client_max_body_size 100M;

        # API routes
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Auth routes
        location /token {
            proxy_pass http://backend/token;
            proxy_set_header Host $host;
        }

        # Serve uploaded files
        location /files/ {
            alias /var/www/uploads/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
        }
    }
}
```

## API Endpoints

### Authentication
```python
POST /token
Body: { "username": "email@example.com", "password": "password" }
Response: { "access_token": "jwt-token", "token_type": "bearer" }

POST /register
Body: { "email": "email@example.com", "password": "password" }
Response: { "id": "user-id", "email": "email@example.com" }
```

### File Management
```python
POST /api/upload
Headers: Authorization: Bearer {token}
Body: multipart/form-data with file
Response: { "upload_id": "uuid", "status": "processing" }

GET /api/uploads
Headers: Authorization: Bearer {token}
Response: { "uploads": [...], "total": 50 }

GET /api/upload/{upload_id}
Headers: Authorization: Bearer {token}
Response: { upload details }

DELETE /api/upload/{upload_id}
Headers: Authorization: Bearer {token}
Response: { "success": true }
```

### Search
```python
POST /api/search
Headers: Authorization: Bearer {token}
Body: { "query": "funny cat video", "limit": 20 }
Response: { 
    "results": [
        {
            "id": "uuid",
            "filename": "cat_video.mp4",
            "summary": "A cat doing funny things...",
            "similarity_score": 0.92,
            "thumbnail_url": "/files/user-id/file-id/thumbnail.jpg"
        }
    ]
}
```

## Frontend Setup (React + TypeScript)

```json
// frontend/package.json
{
  "name": "multimodal-search-frontend",
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "axios": "^1.6.7",
    "@tanstack/react-query": "^5.20.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.19",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.1.0"
  }
}
```
also i want npm install --save-dev --save-exact @biomejs/biome
Use code with caution.
Bash
2. Create a configuration file:
Biome can generate a biome.json file for you.
Generated bash
npx @biomejs/biome init 
so i guess add to package.json or soemtrhing?
for ruff like linting but for frotnend lol
(so ruff for abckend, biome for fortnned and well have to mnake a not super strict biome.json as well and pyproject.toml for ruff and future pytesting)
and then well add commands to both in the Makefile as well
```typescript
// frontend/src/api/client.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## MVC Architecture (Your Preferred Pattern)

### Models - Database Operations
```python
# models/upload.py
class Upload(BaseModel):
    """All database operations for uploads"""
    
    @classmethod
    async def create(cls, user_id: UUID, file_data: dict) -> 'Upload':
        """Create upload record"""
        # Database logic here
        pass
    
    @classmethod
    async def find_by_user(cls, user_id: UUID) -> List['Upload']:
        """Get all uploads for user"""
        # Database query here
        pass
    
    async def update_embedding(self, summary: str, embedding: List[float]):
        """Update with AI results"""
        # Update logic here
        pass
```

### Controllers - Thin HTTP Layer
```python
# routers/upload.py
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Thin controller - just orchestrates"""
    # Validate file
    if file.size > settings.max_upload_size:
        raise HTTPException(400, "File too large")
    
    # Call service
    result = await UploadService.process_upload(user.id, file)
    
    # Return response
    return {"upload_id": result.id, "status": "processing"}
```

### Services - Business Logic
```python
# services/upload_service.py
class UploadService:
    """Complex business logic"""
    
    @staticmethod
    async def process_upload(user_id: UUID, file: UploadFile):
        # Save file locally
        file_id = uuid4()
        path = await LocalStorageService.upload_file(
            file.file, user_id, file_id, file.filename
        )
        
        # Create database record
        upload = await Upload.create(
            user_id=user_id,
            file_data={
                'filename': file.filename,
                'file_path': path,
                'file_type': detect_file_type(file),
                'file_size': file.size
            }
        )
        
        # Queue for AI processing
        await process_with_ai.delay(upload.id)
        
        return upload
```

## Next Steps for MVP

1. **Set up Docker Compose** and get PostgreSQL + Redis running
2. **Create database schema** with pgvector extension
3. **Implement JWT auth** endpoints (register/login)
4. **Build file upload** with local storage
5. **Integrate AI services** (Gemini + OpenAI)
6. **Create search endpoint** using pgvector
7. **Build React frontend** with upload and search UI

## Deployment (Simple Approach)

1. Use Cloudflare for DNS and SSL
2. Deploy with Docker Compose on a VPS
3. Use Nginx as reverse proxy
4. Add `.env` for production secrets
5. Use systemd to manage Docker Compose


* **please now read and refer to the .context/context/MVP.md** 

# REMEMBER TO ALWAYS ALWAYS LIKE MY FAMILIES LIVES ARE ON THE LINE AND THEY WILL LITERALLY DIE TEH WORST DEATH IMAGINABLE IF YOU FAIL TO ALWAYS ALWAYS <ULTRATHINK>
