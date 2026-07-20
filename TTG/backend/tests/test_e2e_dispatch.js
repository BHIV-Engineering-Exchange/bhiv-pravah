const io = require('socket.io-client');

console.log('🔄 END-TO-END JOB DISPATCH TEST\n');
console.log('='.repeat(70));

// Connect as engine
const engineSocket = io('http://localhost:3000/engine', {
  auth: { token: 'dev-bypass' }
});

engineSocket.on('connect', () => {
  console.log('✅ Engine connected');
  console.log(`   Socket ID: ${engineSocket.id}\n`);

  // Listen for job dispatch
  engineSocket.on('job:dispatch', (job) => {
    console.log('📦 Job received by engine:');
    console.log(`   Job ID: ${job.jobId}`);
    console.log(`   Job Type: ${job.jobType}`);
    console.log(`   Payload: ${JSON.stringify(job.payload).substring(0, 50)}...`);
    
    // Send acknowledgment
    engineSocket.emit('job:ack', {
      jobId: job.jobId,
      status: 'received'
    });
    
    console.log('✅ Acknowledgment sent\n');
    
    setTimeout(() => {
      engineSocket.disconnect();
      console.log('='.repeat(70));
      console.log('✅ TEST COMPLETE - Job dispatch working end-to-end');
      console.log('='.repeat(70));
      process.exit(0);
    }, 1000);
  });

  // Trigger job from dashboard
  setTimeout(() => {
    console.log('🎮 Dispatching game from dashboard...\n');
    
    fetch('http://localhost:3000/api/ttg/start-game', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Create a simple runner game' })
    })
      .then(res => res.json())
      .then(data => {
        console.log(`✅ Dashboard dispatched ${data.jobs.length} jobs\n`);
      })
      .catch(err => console.log('❌ ERROR:', err.message));
  }, 500);
});

engineSocket.on('connect_error', (err) => {
  console.log('❌ Engine connection failed:', err.message);
  process.exit(1);
});

setTimeout(() => {
  console.log('⚠️  Timeout - No job received');
  engineSocket.disconnect();
  process.exit(1);
}, 5000);
