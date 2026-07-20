// test_telemetry_replay.js - Telemetry Replay Test
const { loadTelemetry, replayTelemetry, clearTelemetry } = require('./engine/engine_telemetry');

console.log('=== TELEMETRY REPLAY TEST ===\n');

// Load telemetry log
const events = loadTelemetry();

if (events.length === 0) {
  console.log('No telemetry events found. Run the system first to generate events.\n');
  process.exit(0);
}

console.log(`Loaded ${events.length} events\n`);

// Verify sequence continuity
console.log('--- Sequence Continuity Check ---');
const withSeq = events.filter(e => e.seq !== undefined);
const withoutSeq = events.length - withSeq.length;

if (withoutSeq > 0) {
  console.log(`⚠️  ${withoutSeq} legacy events without seq field (ignored)`);
}

if (withSeq.length === 0) {
  console.log('⚠️  No events with seq field found\n');
} else {
  let gaps = 0;
  for (let i = 1; i < withSeq.length; i++) {
    if (withSeq[i].seq !== withSeq[i-1].seq + 1) {
      console.log(`❌ Gap: ${withSeq[i-1].seq} → ${withSeq[i].seq}`);
      gaps++;
    }
  }
  if (gaps === 0) {
    console.log(`✅ No gaps in ${withSeq.length} sequenced events\n`);
  } else {
    console.log(`❌ Found ${gaps} gaps\n`);
  }
}

// Replay events and build job timeline
console.log('--- Job Timeline Reconstruction ---');
const jobTimeline = {};

// Only replay events with proper structure
const validEvents = events.filter(e => e.event && e.jobId !== undefined);

replayTelemetry(validEvents, {
  JOB_QUEUED: (e) => {
    jobTimeline[e.jobId] = {
      jobId: e.jobId,
      userId: e.userId,
      jobType: e.payload.jobType,
      queued: e.ts,
      states: ['queued']
    };
  },
  JOB_DISPATCHED: (e) => {
    if (jobTimeline[e.jobId]) {
      jobTimeline[e.jobId].dispatched = e.ts;
      jobTimeline[e.jobId].states.push('dispatched');
    }
  },
  JOB_RUNNING: (e) => {
    if (jobTimeline[e.jobId]) {
      jobTimeline[e.jobId].running = e.ts;
      jobTimeline[e.jobId].states.push('running');
    }
  },
  JOB_COMPLETED: (e) => {
    if (jobTimeline[e.jobId]) {
      jobTimeline[e.jobId].completed = e.ts;
      jobTimeline[e.jobId].duration = e.payload.duration;
      jobTimeline[e.jobId].states.push('completed');
    }
  },
  JOB_FAILED: (e) => {
    if (jobTimeline[e.jobId]) {
      jobTimeline[e.jobId].failed = e.ts;
      jobTimeline[e.jobId].error = e.payload.error;
      jobTimeline[e.jobId].states.push('failed');
    }
  }
});

// Display job timelines
Object.values(jobTimeline).forEach(job => {
  console.log(`\nJob: ${job.jobId}`);
  console.log(`  Type: ${job.jobType}`);
  console.log(`  User: ${job.userId}`);
  console.log(`  States: ${job.states.join(' → ')}`);
  if (job.duration) {
    console.log(`  Duration: ${job.duration}ms`);
  }
  if (job.error) {
    console.log(`  Error: ${job.error}`);
  }
});

// Event type summary
console.log('\n--- Event Type Summary ---');
const eventCounts = {};
events.forEach(e => {
  eventCounts[e.event] = (eventCounts[e.event] || 0) + 1;
});

Object.entries(eventCounts)
  .sort((a, b) => b[1] - a[1])
  .forEach(([event, count]) => {
    console.log(`${event}: ${count}`);
  });

console.log('\n=== REPLAY TEST COMPLETE ===');
