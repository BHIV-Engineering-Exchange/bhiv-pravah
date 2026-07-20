// Mongo shell script: Keep latest 14 jobs and delete the rest (with preview + confirmation)
// Usage:
//   1) cd C:\Infiverse-HR\backend
//   2) mongosh "$env:MONGODB_URI" --file scripts/cleanup_keep_latest_14_jobs.mongosh.js
//      (PowerShell)
//   3) Type YES when prompted to execute deletion

const DB_NAME = "bhiv_hr";
const KEEP_COUNT = 14;
const BACKUP_COLLECTION = "job_cleanup_backups";

// Candidate browse jobs typically shows active jobs only.
// Change to {} if you want to include all statuses.
const JOB_FILTER = { status: "active" };
const SORT_ORDER = { created_at: -1, _id: -1 };

const dbHandle = db.getSiblingDB(DB_NAME);
const totalJobs = dbHandle.jobs.countDocuments(JOB_FILTER);

print("Total matching jobs: " + totalJobs);
print("Filter: " + tojson(JOB_FILTER));

if (totalJobs <= KEEP_COUNT) {
  print("Nothing to delete. Matching jobs are already <= " + KEEP_COUNT);
  quit(0);
}

const keepJobs = dbHandle.jobs
  .find(JOB_FILTER, { title: 1, company: 1, created_at: 1, recruiter_id: 1 })
  .sort(SORT_ORDER)
  .limit(KEEP_COUNT)
  .toArray();

const deleteJobs = dbHandle.jobs
  .find(JOB_FILTER, { title: 1, company: 1, created_at: 1, recruiter_id: 1 })
  .sort(SORT_ORDER)
  .skip(KEEP_COUNT)
  .toArray();

print("\n===== PREVIEW: LATEST " + KEEP_COUNT + " JOBS TO KEEP =====");
keepJobs.forEach((j, i) => {
  print(
    (i + 1) + ". " +
    (j.title || "(no title)") +
    " | company: " + (j.company || "-") +
    " | created_at: " + (j.created_at || "-") +
    " | _id: " + j._id
  );
});

print("\nJobs that will be deleted: " + deleteJobs.length);
print("First 10 from delete list preview:");
deleteJobs.slice(0, 10).forEach((j, i) => {
  print(
    (i + 1) + ". " +
    (j.title || "(no title)") +
    " | created_at: " + (j.created_at || "-") +
    " | _id: " + j._id
  );
});

const confirm = prompt("\nType YES to delete all jobs except latest " + KEEP_COUNT + ": ");
if (confirm !== "YES") {
  print("Cancelled. No data deleted.");
  quit(0);
}

const deleteObjectIds = deleteJobs.map((j) => j._id);
const deleteJobIdStrings = deleteObjectIds.map((id) => id.toString());

// Create an in-database backup snapshot before deletion.
const backupDoc = {
  created_at: new Date(),
  db_name: DB_NAME,
  keep_count: KEEP_COUNT,
  filter: JOB_FILTER,
  summary: {
    total_matching_jobs: totalJobs,
    jobs_kept: keepJobs.length,
    jobs_marked_for_delete: deleteJobs.length,
  },
  keep_job_ids: keepJobs.map((j) => j._id.toString()),
  delete_job_ids: deleteJobIdStrings,
  jobs: dbHandle.jobs.find({ _id: { $in: deleteObjectIds } }).toArray(),
  job_applications: dbHandle.job_applications.find({ job_id: { $in: deleteJobIdStrings } }).toArray(),
  interviews: dbHandle.interviews.find({ job_id: { $in: deleteJobIdStrings } }).toArray(),
  offers: dbHandle.offers.find({ job_id: { $in: deleteJobIdStrings } }).toArray(),
  feedback: dbHandle.feedback.find({ job_id: { $in: deleteJobIdStrings } }).toArray(),
  notification_logs: dbHandle.notification_logs.find({ job_id: { $in: deleteJobIdStrings } }).toArray(),
};

const backupRes = dbHandle[BACKUP_COLLECTION].insertOne(backupDoc);
print("Backup created in collection '" + BACKUP_COLLECTION + "' with _id: " + backupRes.insertedId);

// Delete related process data first, then jobs.
const appRes = dbHandle.job_applications.deleteMany({ job_id: { $in: deleteJobIdStrings } });
const intRes = dbHandle.interviews.deleteMany({ job_id: { $in: deleteJobIdStrings } });
const offRes = dbHandle.offers.deleteMany({ job_id: { $in: deleteJobIdStrings } });
const fbRes = dbHandle.feedback.deleteMany({ job_id: { $in: deleteJobIdStrings } });
const nlRes = dbHandle.notification_logs.deleteMany({ job_id: { $in: deleteJobIdStrings } });
const jobRes = dbHandle.jobs.deleteMany({ _id: { $in: deleteObjectIds } });

print("\n===== DELETE SUMMARY =====");
printjson({
  backup_id: backupRes.insertedId,
  jobs_deleted: jobRes.deletedCount,
  job_applications_deleted: appRes.deletedCount,
  interviews_deleted: intRes.deletedCount,
  offers_deleted: offRes.deletedCount,
  feedback_deleted: fbRes.deletedCount,
  notification_logs_deleted: nlRes.deletedCount,
});

const remaining = dbHandle.jobs.countDocuments(JOB_FILTER);
print("Remaining matching jobs after cleanup: " + remaining);
