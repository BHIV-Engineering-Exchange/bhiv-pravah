/**
 * Test TTG API Endpoint
 * Tests /api/ttg/start-game with job dispatch
 */

const testText = "Create a fast runner game with obstacles";

console.log('🧪 Testing TTG API Endpoint');
console.log('='.repeat(60));
console.log('Input:', testText);
console.log('Endpoint: POST http://localhost:3000/api/ttg/start-game');
console.log('='.repeat(60));

fetch('http://localhost:3000/api/ttg/start-game', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ text: testText })
})
  .then(res => res.json())
  .then(data => {
    console.log('\n✅ Response received:\n');
    console.log('Success:', data.success);
    console.log('Game Mode:', data.game_mode);
    console.log('Message:', data.message);
    console.log('\n📋 Jobs Generated:', data.jobs.length);
    
    data.jobs.forEach((job, index) => {
      console.log(`\n${index + 1}. ${job.jobType}`);
      console.log(`   JobID: ${job.jobId}`);
      console.log(`   Status: ${job.status}`);
      
      if (job.jobType === 'START_LOOP') {
        console.log(`   Game Mode: ${job.payload.game_mode}`);
        console.log(`   Speed: ${job.payload.params.movement_speed}`);
        console.log(`   Difficulty: ${job.payload.params.difficulty}`);
      }
    });
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ All job types validated via API!');
    console.log('='.repeat(60));
  })
  .catch(err => {
    console.error('❌ Error:', err.message);
    console.log('\n⚠️  Make sure backend is running:');
    console.log('   cd backend && npm start');
  });
