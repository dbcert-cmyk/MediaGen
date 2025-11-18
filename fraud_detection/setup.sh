#!/bin/bash

# Setup script for Multi-Agent Fraud Detection System

echo "================================================"
echo "Multi-Agent Fraud Detection System - Setup"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker Compose is installed"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION is installed"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

echo "✅ Virtual environment created"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit the .env file and add your Google API key!"
    echo "   Get a free API key from: https://ai.google.dev/"
else
    echo "✅ .env file already exists"
fi

# Start Docker services
echo ""
echo "Starting Docker services (PostgreSQL, Redpanda, Redis)..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Check PostgreSQL
if docker exec fraud_detection_postgres pg_isready -U fraud_user -d fraud_detection &> /dev/null; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is still starting up..."
fi

# Check Redpanda
if docker exec fraud_detection_redpanda rpk cluster health &> /dev/null; then
    echo "✅ Redpanda is ready"
else
    echo "⚠️  Redpanda is still starting up..."
fi

# Check Redis
if docker exec fraud_detection_redis redis-cli ping &> /dev/null; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is still starting up..."
fi

echo ""
echo "================================================"
echo "Setup Complete! 🎉"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your Google API key:"
echo "   GOOGLE_API_KEY=your-api-key-here"
echo ""
echo "2. Run the demo application:"
echo "   python demo_app.py"
echo ""
echo "3. Open http://localhost:8000 in your browser"
echo ""
echo "Or run the streaming mode:"
echo "   Terminal 1: python -m fraud_detection.main"
echo "   Terminal 2: python -m fraud_detection.streaming.producer"
echo ""
echo "================================================"
