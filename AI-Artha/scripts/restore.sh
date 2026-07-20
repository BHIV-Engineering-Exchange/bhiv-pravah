#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup_file>"
    echo "Example: ./scripts/restore.sh backups/artha_backup_20250125_120000.gz"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️ WARNING: This will replace the current database!"
read -p "Are you sure you want to restore from $BACKUP_FILE? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

echo "💾 Starting database restore..."

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Copy backup to container
docker cp ${BACKUP_FILE} artha-mongo-prod:/tmp/restore.gz

# Restore database
docker exec artha-mongo-prod mongorestore \
    --authenticationDatabase=admin \
    -u $MONGO_ROOT_USER \
    -p $MONGO_ROOT_PASSWORD \
    --db=artha_prod \
    --gzip \
    --archive=/tmp/restore.gz \
    --drop

# Clean up
docker exec artha-mongo-prod rm /tmp/restore.gz

echo "✅ Database restored successfully!"