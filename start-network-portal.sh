#!/bin/bash

# Home Network Portal - Startup Script

set -e

echo "======================================"
echo "Home Network Management Portal"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.network-portal .env
    echo "✓ Created .env file"
    echo ""
    echo "NOTE: Please review and update .env file with your settings"
    echo "Especially change SECRET_KEY and passwords for production use!"
    echo ""
fi

# Start services
echo "Starting all services..."
echo ""
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "Service Status:"
docker-compose ps

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Access Points:"
echo "  Main Portal:  http://localhost:8000"
echo "  Netdata:      http://localhost:19999"
echo "  LibreNMS:     http://localhost:8001"
echo "  Netbox:       http://localhost:8080"
echo ""
echo "First-time Setup:"
echo "  1. Download AI model (required for AI features):"
echo "     docker exec -it dxb-ollama-1 ollama pull llama3.2"
echo ""
echo "  2. Wait ~2 minutes for all services to fully initialize"
echo ""
echo "  3. Visit http://localhost:8000 to start using the portal"
echo ""
echo "Default Credentials:"
echo "  Netbox: admin / admin"
echo ""
echo "Useful Commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop all:      docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
echo "Documentation: See NETWORK-PORTAL-README.md"
echo "======================================"
