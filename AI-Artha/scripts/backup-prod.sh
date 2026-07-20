#!/bin/bash

# Production backup script for Artha
set -e

# Configuration
BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
MONGO_CONTAINER="artha-mongo-prod"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

echo "🔄 Starting Artha production backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# MongoDB backup
echo "📦 Creating MongoDB backup..."
docker exec $MONGO_CONTAINER mongodump \
  --host localhost:27017 \
  --db artha_prod \
  --out /tmp/backup_$DATE

# Copy backup from container
docker cp $MONGO_CONTAINER:/tmp/backup_$DATE $BACKUP_DIR/

# Compress backup
echo "🗜️ Compressing backup..."
cd $BACKUP_DIR
tar -czf mongodb_backup_$DATE.tar.gz backup_$DATE/
rm -rf backup_$DATE/

# Upload to S3 (if configured)
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 cp mongodb_backup_$DATE.tar.gz s3://$BACKUP_S3_BUCKET/artha/mongodb/
fi

# Backup uploaded files
echo "📁 Backing up uploaded files..."
tar -czf uploads_backup_$DATE.tar.gz -C /app uploads/

if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    aws s3 cp uploads_backup_$DATE.tar.gz s3://$BACKUP_S3_BUCKET/artha/uploads/
fi

# Clean up old backups
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Clean up container backup
docker exec $MONGO_CONTAINER rm -rf /tmp/backup_$DATE

echo "✅ Backup completed successfully!"
echo "Backup files:"
echo "- MongoDB: $BACKUP_DIR/mongodb_backup_$DATE.tar.gz"
echo "- Uploads: $BACKUP_DIR/uploads_backup_$DATE.tar.gz"

# Log backup completion
echo "$(date): Backup completed - mongodb_backup_$DATE.tar.gz, uploads_backup_$DATE.tar.gz" >> $BACKUP_DIR/backup.log