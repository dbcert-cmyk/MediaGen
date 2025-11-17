#!/bin/bash

echo "=========================================="
echo "Network Management Portal - Quick Start"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "Creating default config.yaml..."
    cp config.example.yaml config.yaml
    echo "⚠️  Please edit config.yaml to add your devices"
fi

# Create data directory
mkdir -p data

echo ""
echo "=========================================="
echo "Starting Network Management Portal..."
echo "=========================================="
echo ""

# Run the application
python app.py
