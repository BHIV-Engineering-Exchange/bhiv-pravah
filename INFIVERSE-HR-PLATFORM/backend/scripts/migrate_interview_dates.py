#!/usr/bin/env python3
"""
Migration script to convert interview_date from string to datetime in job_applications
"""
import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.environ.get("MONGODB_URI") or os.environ.get("DATABASE_URL")
DB_NAME = os.environ.get("MONGODB_DB_NAME", "bhiv_hr")

async def migrate_interview_dates():
    """Convert string interview_date to datetime objects in job_applications"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print("🔍 Checking job_applications with interview_scheduled status...")
    
    # Find all applications with interview_scheduled status
    cursor = db.job_applications.find({"status": "interview_scheduled"})
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    async for doc in cursor:
        interview_date = doc.get("interview_date")
        
        # Skip if interview_date doesn't exist
        if not interview_date:
            print(f"  ⚠️ Skipping {doc.get('candidate_id')} - no interview_date")
            skipped_count += 1
            continue
        
        # Skip if already a datetime object
        if isinstance(interview_date, datetime):
            print(f"  ✓ Skipping {doc.get('candidate_id')} - already datetime")
            skipped_count += 1
            continue
        
        # Convert string to datetime
        if isinstance(interview_date, str):
            try:
                # Try ISO format
                date_obj = datetime.fromisoformat(interview_date.replace('Z', '+00:00'))
                
                # Update the document
                await db.job_applications.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"interview_date": date_obj}}
                )
                
                print(f"  ✅ Converted {doc.get('candidate_id')}: '{interview_date}' → {date_obj}")
                updated_count += 1
                
            except Exception as e:
                print(f"  ❌ Error converting {doc.get('candidate_id')}: {e}")
                error_count += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ⚠️ Skipped: {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    
    client.close()

if __name__ == "__main__":
    print("🚀 Starting interview_date migration...\n")
    asyncio.run(migrate_interview_dates())
    print("\n✅ Migration complete!")
