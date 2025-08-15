#!/bin/bash

set -e  # Exit on error

echo "PG-VENV Project Setup"
echo "⠀⠀⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⡠⢴⣴⣾⣿⡿⠓⡠⠀⠀⠀⠀⠠⢄⠁⢀⠀⠀
⠀⠀⠀⠀⠀⠳⣽⡽⠀⠀⡠⢊⣴⣿⣿⣿⣡⠖⠁⣀⡤⢖⠟⠁⡠⠀⡙⢿⣷⣄
⠀⠀⠐⡀⠀⠀⠀⠀⢠⣾⣿⣿⢽⣿⣿⣿⣥⠖⣻⣯⡾⠃⠀⡔⡀⠀⣷⢸⢿⣿
⠀⠀⠀⢰⠀⠀⠀⢠⢟⣿⠃⢀⣾⣿⠟⠋⢀⡾⢋⣾⠃⣠⡾⢰⡇⡇⣿⣿⡞⣿
⠀⠀⡤⣈⡀⠀⢀⠏⣼⣧⡴⣼⠟⠁⠀⠀⡾⠁⣾⡇⣰⢿⠃⢾⣿⣷⣿⣿⣇⢿
⠀⠀⠱⠼⠊⠀⠄⡜⣿⣿⡿⠃⠈⠁⠀⢸⠁⢠⡿⣰⢯⠃⠀⠘⣿⣿⣿⣿⣿⠸
⠀⠀⠀⠀⠀⠀⡘⡀⣸⣿⣱⡤⢴⣄⠀⠈⠀⠘⣷⠏⠌⠢⡀⠀⢿⣿⣿⣿⡟⡄
⠀⠀⠀⠀⢀⣌⠌⣴⣿⣿⠃⣴⣿⣟⡇⠀⠀⠀⠟⠀⠀⠀⠈⠢⢈⣿⡟⣿⡗⡇
⠀⠀⢀⡴⡻⣡⣾⠟⢹⡇⠀⡇⢄⢿⠇⠀⠀⠀⠀⠀⠀⣽⣶⣄⡀⠘⢷⡹⣿⣿
⠀⠀⣧⣾⡿⠋⠁⢀⡜⠙⡄⠓⠐⠁⠀⠀⠀⠀⠀⠀⡼⠛⠻⣟⠛⣆⠈⢷⣿⣿
⣴⣾⣟⣵⣿⣿⣿⣁⢇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡧⠠⠔⡹⠀⢸⠀⣼⣿⣿
⠿⡽⢫⡉⠀⣠⠔⠁⡀⠕⠠⡀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠖⠊⠀⠀⢊⣾⢿⡿⠉
⠀⠁⠀⡹⢨⠁⠐⠈⢀⡠⠐⠁⠄⠡⡀⡀⠀⠀⠀⠀⠀⠀⠀⠠⠶⢛⡨⠊⠀⠀
⠀⠀⡜⠀⠈⣂⠀⠀⠀⠀⡠⠐⠉⡆⠀⣀⢀⣀⣀⣀⡀⠀⠀⣀⠴⣁⡀⠤⠀⠀
⠀⠈⠀⠀⠀⡇⠑⢄⠀⠀⠀⠀⣲⢥⡎⠀⢰⠀⢸⠀⢀⠉⠙⣿⣧⣀⣀⣂⣤⣼
⠀⠀⠀⠆⠁⠃⠀⠀⠈⠒⠒⠊⣸⠚⠁⠀⠀⠀⠀⠀⠀⠀⡜⠁⠀⠀⠀⠀⠈⠚
⠀⠀⠀⠀⠀⠂⠀⠀⠀⠀⠀⢀⠋⢆⠀⠀⠀⠀⠀⠀⠀⡘⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠒⠂⠀⠀⠐⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀"


# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo "✅ Python $PYTHON_VERSION detected"
    else
        echo "⚠️  Python $PYTHON_VERSION detected. Python 3.10+ recommended."
    fi
else
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -ge 18 ]; then
    echo "✅ Node.js $(node -v) detected"
else
    echo "⚠️  Node.js $(node -v) detected. Node.js 18+ recommended."
fi

# Create Python virtual environment
echo ""
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
if [ -f "pyproject.toml" ]; then
    pip install -e ".[dev]"
    echo "✅ Backend dependencies installed"
else
    echo "⚠️  pyproject.toml not found, skipping backend dependencies"
fi
cd ..

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "Initializing React + Vite + TypeScript + Tailwind..."
    npm create vite@latest . -- --template react-ts
    npm install -D tailwindcss postcss autoprefixer @biomejs/biome
    npm install axios react-router-dom @tanstack/react-query zustand
    npx tailwindcss init -p
    
    # Create biome.json
    cat > biome.json << 'EOF'
{
  "$schema": "https://biomejs.dev/schemas/1.5.0/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "style": {
        "noNonNullAssertion": "off"
      },
      "suspicious": {
        "noExplicitAny": "warn"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "formatWithErrors": false,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "jsxQuoteStyle": "double",
      "semicolons": "asNeeded",
      "trailingComma": "es5",
      "arrowParentheses": "always"
    }
  }
}
EOF
    echo "✅ Frontend initialized"
else
    npm install
    echo "✅ Frontend dependencies installed"
fi

cd ..

# Create environment files if they don't exist
echo ""
echo "Setting up environment files..."

# Dev environment
if [ ! -f "infra/dev/env/.env.dev" ]; then
    cat > infra/dev/env/.env.dev << 'EOF'
# Application
APP_NAME="Multimodal Search Dev"
ENVIRONMENT="development"
DEBUG=True

# Database
DATABASE_URL="postgresql://postgres:devpassword@postgres:5432/multimodal_search_dev"

# Redis
REDIS_URL="redis://redis:6379/0"

# JWT Auth
SECRET_KEY="dev-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs (Add your keys here)
OPENAI_API_KEY=""
GEMINI_API_KEY=""

# Storage
UPLOAD_PATH="/app/storage/uploads"
MAX_UPLOAD_SIZE=104857600

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
EOF
    echo "✅ Created infra/dev/env/.env.dev (add your API keys!)"
else
    echo "✅ infra/dev/env/.env.dev already exists"
fi

# Prod environment
if [ ! -f "infra/prod/env/.env.prod" ]; then
    cat > infra/prod/env/.env.prod << 'EOF'
# Application
APP_NAME="Multimodal Search"
ENVIRONMENT="production"
DEBUG=False

# Database
DATABASE_URL="postgresql://postgres:CHANGE_THIS_PASSWORD@postgres:5432/multimodal_search_prod"

# Redis
REDIS_URL="redis://redis:6379/0"

# JWT Auth
SECRET_KEY="GENERATE_WITH_OPENSSL_RAND_HEX_32"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs (Add your keys here)
OPENAI_API_KEY=""
GEMINI_API_KEY=""

# Storage
UPLOAD_PATH="/app/storage/uploads"
MAX_UPLOAD_SIZE=104857600

# CORS
CORS_ORIGINS=["https://yourdomain.com"]
EOF
    echo "✅ Created infra/prod/env/.env.prod (configure before deploying!)"
else
    echo "✅ infra/prod/env/.env.prod already exists"
fi

# Create .env.example
if [ ! -f "backend/.env.example" ]; then
    cat > backend/.env.example << 'EOF'
# Copy this to .env and fill in your values

# Application
APP_NAME="Multimodal Search"
ENVIRONMENT="development"
DEBUG=True

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Redis
REDIS_URL="redis://localhost:6379"

# JWT Auth
SECRET_KEY="your-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI APIs
OPENAI_API_KEY="your-openai-key"
GEMINI_API_KEY="your-gemini-key"

# Storage
UPLOAD_PATH="./storage/uploads"
MAX_UPLOAD_SIZE=104857600
EOF
    echo "✅ Created backend/.env.example"
fi

# Setup complete
echo ""
echo "Setup complete!"
echo "⡇⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⢁⣿⣿⡏⠉⠉⠉⠉⠉⠉⠉⠉⠉⢹⣇⠉⠉⢳⣌⢉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⢸⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣧⠀⠀⢻⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣰⠀⠀⢸⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣷⣄⠀⠹⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⢸⢸⣿⡿⠿⢃⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⠿⣿⣦⣀⠙⢿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⣈⣛⣋⡄⢨⣨⣶⣶⣶⣷⡶⡀⠀⠀⠀⠀⠀⢀⠀⢿⣷⣶⣶⣶⣶⣷⣤⣭⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⡄⣇⣟⠿⣿⣿⣷⣱⡀⠀⠀⠀⠀⢸⡄⢸⣿⠿⢛⠛⠛⠻⢿⡟⣽⠆⡀⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠂⠀⠀⠓⠀⠐⠒⠈⠻⣷⣌⠟⣿⣧⣵⡐⡄⠀⠀⠸⡿⠀⠀⠀⢀⡀⠀⠀⠀⠈⠃⢜⡁⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⡐⠀⠀⠠⠤⠀⠀⠈⠻⣦⣽⣿⣿⣷⡜⠆⠀⠀⣵⡆⠀⠈⠛⠁⠀⠀⢢⡀⠘⢿⡇⠀⠀⠀⠀⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⢀⢡⡀⢀⢠⠀⠀⠆⡀⣿⣧⣼⣿⣿⣿⣿⣯⣼⣷⣄⠸⣇⢠⣲⣤⣜⣠⢀⣾⠟⣠⣾⣇⠀⠀⣠⣤⠀⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠈⠆⣩⣈⠻⣿⣿⠞⣡⡿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣜⡢⢝⣻⠛⠋⠵⠖⠖⣢⣿⡇⠀⠀⣭⡹⣇⠀⠀⡇
⡇⠀⠀⠀⠀⠀⠀⠀⠀⠰⣶⣭⣛⣓⣂⣭⣵⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡖⢶⠒⠿⠷⢿⣿⣿⡇⠀⠈⣿⢡⣿ ⠀⡇
⡇ ⠀⠀⠀⠀⠀⠀⠀⠀⠉⣋⠉⣫⣼⣿⣿⣿⣿⣿⣿⣿⡿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣿⣶⣶⣾⣿⣿⠀⢀⡠⢟⣼⠏ ⠀⡇
⡇⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⢹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⢀⣼⡰⢛⣁⣀⣀⣀⡇"
echo "NEXT STEPS:"
echo "1. ACTIVATE the virtual environment in your current shell, run:"
echo "source venv/bin/activate"
echo "2. Add your API keys to infra/dev/env/.env.dev"
echo "3. Run 'make dev' to start the development environment"
echo "4. Visit http://localhost:3000 for the frontend"
echo "5. Visit http://localhost:8000/docs for the API documentation"

