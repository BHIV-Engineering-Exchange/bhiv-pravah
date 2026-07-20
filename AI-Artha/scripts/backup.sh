#!/bin/bash

set -e

echo "💾 Starting ARTHA database backup..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create backup directory if it doesn't exist
mkdir -p backups

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backups/artha_backup_${TIMESTAMP}.gz"

echo -e "${YELLOW}Creating backup: ${BACKUP_FILE}${NC}"

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Create database backup
docker exec artha-mongo-prod mongodump \
    --authenticationDatabase=admin \
    -u $MONGO_ROOT_USER \
    -p $MONGO_ROOT_PASSWORD \
    --db=artha_prod \
    --gzip \
    --archive=/tmp/backup.gz

# Copy backup from container to host
docker cp artha-mongo-prod:/tmp/backup.gz ${BACKUP_FILE}

# Clean up temporary file in container
docker exec artha-mongo-prod rm /tmp/backup.gz

# Get backup size
BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)

echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo "Backup file: ${BACKUP_FILE}"
echo "Backup size: ${BACKUP_SIZE}"

# Keep only last 7 backups
echo -e "${YELLOW}Cleaning up old backups...${NC}"
ls -t backups/artha_backup_*.gz | tail -n +8 | xargs -r rm

echo -e "${GREEN}Backup process completed${NC}"