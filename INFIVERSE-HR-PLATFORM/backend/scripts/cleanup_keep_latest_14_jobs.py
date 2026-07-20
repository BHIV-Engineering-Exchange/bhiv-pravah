#!/usr/bin/env python3
r"""
Keep latest N active jobs and delete older ones, with preview + backup + confirmation.

Usage (Windows CMD):
  cd C:\Infiverse-HR\backend
  venv\Scripts\python.exe scripts\cleanup_keep_latest_14_jobs.py

It will:
1) Preview latest jobs to keep
2) Preview jobs to delete
3) Create backup in MongoDB collection: job_cleanup_backups
4) Delete related records + jobs only after typing YES
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient

DB_NAME = "bhiv_hr"
KEEP_COUNT = 14
BACKUP_COLLECTION = "job_cleanup_backups"
JOB_FILTER: dict[str, Any] = {"status": "active"}
SORT_ORDER = [("created_at", -1), ("_id", -1)]


def to_str(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def main() -> int:
    load_dotenv()

    mongodb_uri = os.getenv("DATABASE_URL") or os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME") or DB_NAME

    if not mongodb_uri:
        print("ERROR: DATABASE_URL/MONGODB_URI not found in environment.")
        return 1

    client = MongoClient(mongodb_uri)
    db = client[db_name]

    total_jobs = db.jobs.count_documents(JOB_FILTER)
    print(f"Total matching jobs: {total_jobs}")
    print(f"Filter: {JOB_FILTER}")

    if total_jobs <= KEEP_COUNT:
        print(f"Nothing to delete. Matching jobs are already <= {KEEP_COUNT}.")
        return 0

    projection = {"title": 1, "company": 1, "created_at": 1, "recruiter_id": 1}

    keep_jobs = list(
        db.jobs.find(JOB_FILTER, projection).sort(SORT_ORDER).limit(KEEP_COUNT)
    )
    delete_jobs = list(
        db.jobs.find(JOB_FILTER, projection).sort(SORT_ORDER).skip(KEEP_COUNT)
    )

    print(f"\n===== PREVIEW: LATEST {KEEP_COUNT} JOBS TO KEEP =====")
    for idx, job in enumerate(keep_jobs, 1):
        print(
            f"{idx}. {to_str(job.get('title'))}"
            f" | company: {to_str(job.get('company'))}"
            f" | created_at: {to_str(job.get('created_at'))}"
            f" | _id: {job.get('_id')}"
        )

    print(f"\nJobs that will be deleted: {len(delete_jobs)}")
    print("First 10 from delete list preview:")
    for idx, job in enumerate(delete_jobs[:10], 1):
        print(
            f"{idx}. {to_str(job.get('title'))}"
            f" | created_at: {to_str(job.get('created_at'))}"
            f" | _id: {job.get('_id')}"
        )

    confirm = input(f"\nType YES to delete all jobs except latest {KEEP_COUNT}: ").strip()
    if confirm != "YES":
        print("Cancelled. No data deleted.")
        return 0

    delete_object_ids = [j["_id"] for j in delete_jobs]
    delete_job_id_strings = [str(oid) for oid in delete_object_ids]

    backup_doc = {
        "created_at": datetime.now(timezone.utc),
        "db_name": db_name,
        "keep_count": KEEP_COUNT,
        "filter": JOB_FILTER,
        "summary": {
            "total_matching_jobs": total_jobs,
            "jobs_kept": len(keep_jobs),
            "jobs_marked_for_delete": len(delete_jobs),
        },
        "keep_job_ids": [str(j["_id"]) for j in keep_jobs],
        "delete_job_ids": delete_job_id_strings,
        "jobs": list(db.jobs.find({"_id": {"$in": delete_object_ids}})),
        "job_applications": list(db.job_applications.find({"job_id": {"$in": delete_job_id_strings}})),
        "interviews": list(db.interviews.find({"job_id": {"$in": delete_job_id_strings}})),
        "offers": list(db.offers.find({"job_id": {"$in": delete_job_id_strings}})),
        "feedback": list(db.feedback.find({"job_id": {"$in": delete_job_id_strings}})),
        "notification_logs": list(db.notification_logs.find({"job_id": {"$in": delete_job_id_strings}})),
    }

    backup_res = db[BACKUP_COLLECTION].insert_one(backup_doc)
    print(f"Backup created in collection '{BACKUP_COLLECTION}' with _id: {backup_res.inserted_id}")

    app_res = db.job_applications.delete_many({"job_id": {"$in": delete_job_id_strings}})
    int_res = db.interviews.delete_many({"job_id": {"$in": delete_job_id_strings}})
    off_res = db.offers.delete_many({"job_id": {"$in": delete_job_id_strings}})
    fb_res = db.feedback.delete_many({"job_id": {"$in": delete_job_id_strings}})
    nl_res = db.notification_logs.delete_many({"job_id": {"$in": delete_job_id_strings}})
    job_res = db.jobs.delete_many({"_id": {"$in": delete_object_ids}})

    print("\n===== DELETE SUMMARY =====")
    print(
        {
            "backup_id": str(backup_res.inserted_id),
            "jobs_deleted": job_res.deleted_count,
            "job_applications_deleted": app_res.deleted_count,
            "interviews_deleted": int_res.deleted_count,
            "offers_deleted": off_res.deleted_count,
            "feedback_deleted": fb_res.deleted_count,
            "notification_logs_deleted": nl_res.deleted_count,
        }
    )

    remaining = db.jobs.count_documents(JOB_FILTER)
    print(f"Remaining matching jobs after cleanup: {remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
