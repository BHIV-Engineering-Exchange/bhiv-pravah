#!/bin/bash

set -e

echo "🚀 Starting ARTHA deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
SEED_DB=false
for arg in "$@"; do
    case $arg in
        --seed)
            SEED_DB=true
            shift
            ;;
    esac
done

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production not found${NC}"
    echo "Please create .env.production from .env.production.example"
    exit 1
fi

# Check if backend/.env.production exists
if [ ! -f backend/.env.production ]; then
    echo -e "${RED}❌ Error: backend/.env.production not found${NC}"
    echo "Please create backend/.env.production from backend/.env.production.example"
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

echo -e "${YELLOW}📦 Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down

echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# Check MongoDB health
echo -e "${YELLOW}Checking MongoDB...${NC}"
docker exec artha-mongo-prod mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MongoDB is healthy${NC}"
else
    echo -e "${RED}✗ MongoDB is not responding${NC}"
    exit 1
fi

# Initialize replica set (if not already done)
echo -e "${YELLOW}Initializing MongoDB replica set...${NC}"
docker exec artha-mongo-prod mongosh --eval "rs.initiate()" > /dev/null 2>&1 || echo "Replica set already initialized"

# Wait for replica set to be ready
sleep 5

# Check Redis health
echo -e "${YELLOW}Checking Redis...${NC}"
docker exec artha-redis-prod redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
    exit 1
fi

# Check backend health
echo -e "${YELLOW}Checking backend...${NC}"
sleep 10
curl -f http://localhost:5000/ready > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
    docker logs artha-backend-prod --tail 50
    exit 1
fi

# Create database indexes
echo -e "${YELLOW}Creating database indexes...${NC}"
docker exec artha-backend-prod npm run create-indexes

# Seed database if requested
if [ "$SEED_DB" = true ]; then
    echo -e "${YELLOW}Seeding database...${NC}"
    docker exec artha-backend-prod npm run seed
fi

# Check frontend health
echo -e "${YELLOW}Checking frontend...${NC}"
curl -f http://localhost/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${RED}✗ Frontend is not responding${NC}"
    docker logs artha-frontend-prod --tail 50
    exit 1
fi

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Services:"
echo "  Backend:  http://localhost:5000"
echo "  Frontend: http://localhost"
echo "  Health:   http://localhost:5000/health/detailed"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"