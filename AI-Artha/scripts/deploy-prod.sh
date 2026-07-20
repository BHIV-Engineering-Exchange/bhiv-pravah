#!/bin/bash

# Production deployment script for Artha
set -e

echo "🚀 Starting Artha production deployment..."

# Check if .env.production exists
if [ ! -f "backend/.env.production" ]; then
    echo "❌ Error: backend/.env.production file not found"
    echo "Generating secure configuration..."
    cd backend && npm run generate:config && cd ..
    echo "✅ Configuration generated. Please review and customize the values in:"
    echo "  - .env.production (root level)"
    echo "  - backend/.env.production"
    echo "Then run the deployment script again."
    exit 1
fi

# Check if required environment variables are set
if [ -z "$MONGO_ROOT_USER" ] || [ -z "$MONGO_ROOT_PASSWORD" ] || [ -z "$REDIS_PASSWORD" ]; then
    echo "❌ Error: Required environment variables not set"
    echo "Please set: MONGO_ROOT_USER, MONGO_ROOT_PASSWORD, REDIS_PASSWORD"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p nginx/ssl
mkdir -p backend/logs
mkdir -p backend/uploads/receipts

# Set proper permissions
chmod 755 backend/logs
chmod 755 backend/uploads

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Initialize MongoDB replica set (if needed)
echo "🔧 Initializing MongoDB replica set..."
docker exec artha-mongo-prod mongosh --eval "
try {
  rs.status();
  print('Replica set already initialized');
} catch (e) {
  rs.initiate({
    _id: 'rs0',
    members: [{ _id: 0, host: 'localhost:27017' }]
  });
  print('Replica set initialized');
}
"

# Run database seeding (optional)
if [ "$1" = "--seed" ]; then
    echo "🌱 Seeding database..."
    docker exec artha-backend-prod npm run seed
fi

# Show final status
echo "✅ Deployment completed!"
echo ""
echo "Services:"
echo "- Frontend: http://localhost (port 80)"
echo "- Backend API: http://localhost:5000"
echo "- MongoDB: localhost:27017"
echo "- Redis: localhost:6379"
echo ""
echo "To view logs:"
echo "docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To stop services:"
echo "docker-compose -f docker-compose.prod.yml down"