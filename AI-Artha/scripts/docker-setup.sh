#!/bin/bash

# Docker setup script for ARTHA application

set -e

echo "🐳 Setting up ARTHA Docker environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file from template..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please update backend/.env with your configuration before running the application."
fi

# Build and start development environment
echo "🚀 Starting development environment..."
docker-compose -f docker-compose.dev.yml up --build -d

echo "✅ ARTHA development environment is ready!"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:5000"
echo "🗄️  MongoDB: Cloud Atlas (configured in .env)"
echo ""
echo "📋 Useful commands:"
echo "  docker-compose -f docker-compose.dev.yml logs -f    # View logs"
echo "  docker-compose -f docker-compose.dev.yml down       # Stop services"
echo "  docker-compose -f docker-compose.dev.yml restart    # Restart services"