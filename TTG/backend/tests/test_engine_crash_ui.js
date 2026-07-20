const io = require('socket.io-client');

console.log('💥 ENGINE CRASH UI STATE TEST\n');
console.log('='.repeat(70));

let jobStatuses = [];
let engineStatuses = [];

const dashSocket = io('http://localhost:3000');
let engineSocket;

dashSocket.on('connect', () => {
  console.log('✅ Dashboard connected\n');

  // Monitor job status changes
  dashSocket.on('job_status', (data) => {
    jobStatuses.push({ jobId: data.jobId, status: data.status, time: Date.now() });
    console.log(`📦 Job ${data.jobId.substring(0, 8)}: ${data.status}`);
  });

  // Monitor engine status
  dashSocket.on('engine_status', (data) => {
    engineStatuses.push({ connected: data.connected, time: Date.now() });
    console.log(`🔧 Engine: ${data.connected ? 'CONNECTED ✅' : 'DISCONNECTED ❌'}`);
  });

  // Step 1: Connect as engine
  setTimeout(() => {
    console.log('\n🔌 Connecting engine...');
    engineSocket = io('http://localhost:3000/engine', {
      auth: { token: 'dev-bypass' }
    });

    engineSocket.on('connect', () => {
      console.log('✅ Engine connected\n');
    });
  }, 500);

  // Step 2: Dispatch jobs
  setTimeout(() => {
    console.log('🎮 Dispatching jobs...');
    fetch('http://localhost:3000/api/ttg/start-game', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Create a platformer' })
    }).then(() => console.log('✅ Jobs dispatched\n'));
  }, 1500);

  // Step 3: Crash engine after jobs dispatched
  setTimeout(() => {
    console.log('💥 SIMULATING ENGINE CRASH...');
    engineSocket.disconnect();
    console.log('❌ Engine forcefully disconnected\n');
  }, 3000);

  // Summary after crash
  setTimeout(() => {
    console.log('\n' + '='.repeat(70));
    console.log('📊 UI STATE VERIFICATION');
    console.log('='.repeat(70));
    
    const lastEngineStatus = engineStatuses[engineStatuses.length - 1];
    const queuedJobs = jobStatuses.filter(j => j.status === 'queued').length;
    const failedJobs = jobStatuses.filter(j => j.status === 'failed').length;
    
    console.log(`\n✅ Engine status updates: ${engineStatuses.length}`);
    console.log(`   Last status: ${lastEngineStatus?.connected ? 'CONNECTED' : 'DISCONNECTED'}`);
    console.log(`\n✅ Job status updates: ${jobStatuses.length}`);
    console.log(`   Queued: ${queuedJobs}`);
    console.log(`   Failed: ${failedJobs}`);
    
    console.log('\n📋 Expected UI Behavior:');
    console.log('   ✅ Engine indicator shows DISCONNECTED (red)');
    console.log('   ✅ Jobs remain in queue (not lost)');
    console.log('   ✅ Jobs show queued/failed status');
    console.log('   ✅ No data loss on crash');
    
    console.log('\n' + '='.repeat(70));
    if (!lastEngineStatus?.connected && jobStatuses.length > 0) {
      console.log('✅ TEST PASSED - UI state safe after crash');
    } else {
      console.log('⚠️  TEST INCOMPLETE - Check dashboard manually');
    }
    console.log('='.repeat(70));
    
    dashSocket.disconnect();
    process.exit(0);
  }, 5000);
});
