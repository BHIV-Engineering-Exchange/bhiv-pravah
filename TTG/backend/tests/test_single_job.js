require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const ENGINE_SHARED_SECRET = process.env.ENGINE_SHARED_SECRET;
const JWT_SECRET = process.env.JWT_SECRET;

const engineToken = jwt.sign(
  { engineId: 'test_single_job', role: 'engine' },
  JWT_SECRET,
  { expiresIn: '1h' }
);

console.log('🧪 Test: Single Job Execution\n');

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});

function signMessage(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts = Date.now();
  const sig = crypto
    .createHmac('sha256', ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  return { payload, nonce, ts, sig };
}

socket.on('connect', () => {
  console.log('✅ Engine connected\n');
  socket.emit('engine_ready');
  socket.emit('engine_heartbeat');
});

socket.on('engine_job', (job) => {
  console.log(`📦 Job received: ${job.job_id}`);
  console.log(`   Type: ${job.job_type}`);
  console.log(`   User: ${job.user_id}\n`);
  
  const jobId = job.job_id;
  
  // Ack
  socket.emit('job_ack', signMessage({ jobId, status: 'received' }));
  console.log('✅ Sent: job_ack');
  
  // Started
  setTimeout(() => {
    socket.emit('job_started', signMessage({ job_id: jobId, timestamp: Date.now() }));
    console.log('✅ Sent: job_started');
  }, 500);
  
  // Progress
  setTimeout(() => {
    socket.emit('job_progress', signMessage({ job_id: jobId, progress: 50, timestamp: Date.now() }));
    console.log('✅ Sent: job_progress (50%)');
  }, 1000);
  
  // Completed
  setTimeout(() => {
    socket.emit('job_completed', signMessage({ 
      job_id: jobId, 
      result: { success: true },
      timestamp: Date.now() 
    }));
    console.log('✅ Sent: job_completed\n');
    console.log('✅ Single job test complete!\n');
    
    setTimeout(() => {
      socket.disconnect();
      process.exit(0);
    }, 1000);
  }, 1500);
});

socket.on('ready_ack', () => console.log('✅ Ready acknowledged'));
socket.on('heartbeat_ack', () => console.log('💓 Heartbeat ack'));

console.log('Waiting for job...\n');
