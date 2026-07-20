require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const ENGINE_SHARED_SECRET = process.env.ENGINE_SHARED_SECRET;
const JWT_SECRET = process.env.JWT_SECRET;

const engineToken = jwt.sign(
  { engineId: 'test_concurrent', role: 'engine' },
  JWT_SECRET,
  { expiresIn: '1h' }
);

console.log('🧪 Test: Concurrent Jobs Execution\n');

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});

const activeJobs = new Map();

function signMessage(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts = Date.now();
  const sig = crypto
    .createHmac('sha256', ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  return { payload, nonce, ts, sig };
}

function processJob(jobId, jobType) {
  console.log(`⚙️  Processing: ${jobId} (${jobType})`);
  
  socket.emit('job_ack', signMessage({ jobId, status: 'received' }));
  
  setTimeout(() => {
    socket.emit('job_started', signMessage({ job_id: jobId, timestamp: Date.now() }));
    console.log(`  ✅ Started: ${jobId}`);
  }, 300);
  
  setTimeout(() => {
    socket.emit('job_progress', signMessage({ job_id: jobId, progress: 50, timestamp: Date.now() }));
    console.log(`  📊 Progress: ${jobId} (50%)`);
  }, 800);
  
  setTimeout(() => {
    socket.emit('job_completed', signMessage({ 
      job_id: jobId, 
      result: { success: true },
      timestamp: Date.now() 
    }));
    console.log(`  ✅ Completed: ${jobId}\n`);
    activeJobs.delete(jobId);
    
    if (activeJobs.size === 0) {
      console.log('✅ All concurrent jobs completed!\n');
      setTimeout(() => {
        socket.disconnect();
        process.exit(0);
      }, 1000);
    }
  }, 1500);
}

socket.on('connect', () => {
  console.log('✅ Engine connected\n');
  socket.emit('engine_ready');
  
  setInterval(() => socket.emit('engine_heartbeat'), 3000);
});

socket.on('engine_job', (job) => {
  const jobId = job.job_id;
  activeJobs.set(jobId, job);
  console.log(`📦 Job received: ${jobId} (${job.job_type})`);
  processJob(jobId, job.job_type);
});

socket.on('ready_ack', () => console.log('✅ Ready acknowledged\n'));

console.log('Waiting for concurrent jobs...\n');
console.log('Submit multiple jobs from UI to test concurrency\n');
