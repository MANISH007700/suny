#!/bin/bash

# SUNY Academic Guidance RAG System - Setup Script
# This script automates the complete setup process

echo "🎓 SUNY Academic Guidance RAG System - Setup"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📌 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
echo -e "${GREEN}✅ Found Python $PYTHON_VERSION${NC}"
echo ""

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p backend/models
mkdir -p backend/routers
mkdir -p backend/data/pdfs
mkdir -p backend/data/processed_text
mkdir -p backend/vector_store
mkdir -p backend/utils
mkdir -p frontend/utils

# Create __init__.py files
touch backend/models/__init__.py
touch backend/routers/__init__.py
touch backend/utils/__init__.py
touch frontend/utils/__init__.py

echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip
echo ""

# Install requirements
echo "📥 Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Vector Database Configuration
USE_PINECONE=false
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here

# Application Settings
LOG_LEVEL=INFO
EOF
    echo -e "${YELLOW}⚠️  Created .env file. Please add your OpenRouter API key!${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists. Skipping...${NC}"
fi
echo ""

# Create sample README for PDFs
cat > backend/data/pdfs/README.txt << EOF
📚 PDF Documents Directory

Place your SUNY academic PDF documents here:
- Course catalogs
- Degree requirements
- General education requirements
- Major/minor guides
- Academic policies

The system will automatically process these PDFs when you initialize it.

Example PDF names:
- CS_Course_Catalog_2024.pdf
- General_Education_Requirements.pdf
- Computer_Science_Major_Requirements.pdf
EOF

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "=============================================="
echo "🎯 Next Steps:"
echo "=============================================="
echo ""
echo "1. Get your OpenRouter API key:"
echo "   → Visit: https://openrouter.ai/"
echo "   → Sign up and generate an API key"
echo "   → Add at least \$5 in credits"
echo ""
echo "2. Update your .env file:"
echo "   → Edit .env"
echo "   → Add your OPENROUTER_API_KEY"
echo ""
echo "3. Add your PDF documents:"
echo "   → Place PDFs in: backend/data/pdfs/"
echo ""
echo "4. Start the backend:"
echo "   → cd backend"
echo "   → python main.py"
echo ""
echo "5. Start the frontend (new terminal):"
echo "   → cd frontend"
echo "   → streamlit run app.py"
echo ""
echo "=============================================="
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""