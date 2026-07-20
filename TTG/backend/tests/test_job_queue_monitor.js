const io = require('socket.io-client');

console.log('📊 JOB QUEUE MONITOR TEST\n');
console.log('='.repeat(70));

const dashSocket = io('http://localhost:3000');

let jobStatuses = [];

dashSocket.on('connect', () => {
  console.log('✅ Dashboard connected\n');
  
  dashSocket.on('job_status', (data) => {
    jobStatuses.push(data);
    console.log(`📦 ${data.status.toUpperCase()}: ${data.jobId} (${data.jobType})`);
  });

  // Dispatch game
  setTimeout(() => {
    console.log('🎮 Dispatching game...\n');
    
    fetch('http://localhost:3000/api/ttg/start-game', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Create a fast platformer' })
    })
      .then(res => res.json())
      .then(data => {
        console.log(`✅ ${data.jobs.length} jobs created\n`);
      });
  }, 500);

  // Summary after 5 seconds
  setTimeout(() => {
    console.log('\n' + '='.repeat(70));
    console.log('📊 JOB STATUS SUMMARY');
    console.log('='.repeat(70));
    
    const queued = jobStatuses.filter(j => j.status === 'queued').length;
    const dispatched = jobStatuses.filter(j => j.status === 'dispatched').length;
    const running = jobStatuses.filter(j => j.status === 'running').length;
    const completed = jobStatuses.filter(j => j.status === 'completed').length;
    const failed = jobStatuses.filter(j => j.status === 'failed').length;
    
    console.log(`📋 Queued: ${queued}`);
    console.log(`📤 Dispatched: ${dispatched}`);
    console.log(`⚙️  Running: ${running}`);
    console.log(`✅ Completed: ${completed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📊 Total events: ${jobStatuses.length}`);
    console.log('='.repeat(70));
    
    if (dispatched > 0 || running > 0 || completed > 0) {
      console.log('✅ VALIDATION PASSED - Jobs are being processed by engine');
    } else {
      console.log('⚠️  WARNING - Jobs queued but not dispatched to engine');
    }
    
    dashSocket.disconnect();
    process.exit(0);
  }, 5000);
});
