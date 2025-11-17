#!/bin/bash
# Agent Demo Project Generator
# Copy this entire script and run it inside your cloned agent-demo directory

echo "🤖 Creating Agent Data Flow Visualizer project..."

# Verify we're in the right place
if [ -f "COPY_PASTE_SETUP.sh" ]; then
    echo "Error: Files already exist. Remove them first or run in an empty directory."
    exit 1
fi

echo "Creating directory structure..."
mkdir -p mcp_servers static templates data/sample_files

echo "Creating files..."
