require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'JWT_SECRET_123456789';
const JWT_ISSUER = process.env.JWT_ISSUER || 'microbridge.internal';

const engineToken = jwt.sign(
  { engineId: 'mock_engine_telemetry', role: 'engine' },
  JWT_SECRET,
  { issuer: JWT_ISSUER, expiresIn: '1h' }
);

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});

let gameRunning = false;
let score = 0;
let lives = 3;
let duration = 0;
let fps = 60;

console.log('🎮 Mock Engine Starting...');

socket.on('connect', () => {
  console.log('✅ Connected to dashboard');
  
  // Send heartbeat every 3 seconds
  setInterval(() => {
    socket.emit('engine_heartbeat');
  }, 3000);
});

socket.on('job:dispatch', (job) => {
  console.log(`📦 Job: ${job.jobType}`);
  
  if (job.jobType === 'START_LOOP') {
    setTimeout(() => {
      console.log('🎮 GAME STARTED\n');
      gameRunning = true;
      score = 0;
      lives = job.payload.params.end_condition.value;
      duration = 0;
      
      socket.emit('game:started', { game_mode: job.payload.game_mode });
      
      const gameLoop = setInterval(() => {
        if (!gameRunning) {
          clearInterval(gameLoop);
          return;
        }
        
        duration += 0.1;
        score += job.payload.params.scoring.points_per_second / 10;
        fps = 55 + Math.floor(Math.random() * 6);
        
        if (Math.random() < 0.1) {
          score += job.payload.params.scoring.obstacle_bonus;
          console.log(`💎 +${job.payload.params.scoring.obstacle_bonus}`);
        }
        
        if (Math.random() < 0.05 && lives > 0) {
          lives--;
          console.log(`💔 Lives: ${lives}`);
          if (lives === 0) {
            endGame('player_death');
            return;
          }
        }
        
        socket.emit('telemetry', {
          fps,
          score: Math.floor(score),
          game_over: false,
          lives,
          duration: parseFloat(duration.toFixed(1))
        });
        
        if (duration % 1 < 0.15) {
          console.log(`⏱️  ${duration.toFixed(1)}s | Score: ${Math.floor(score)} | FPS: ${fps}`);
        }
        
        if (duration >= 30) {
          endGame('time_up');
        }
      }, 100);
    }, 2000);
  }
});

function endGame(reason) {
  console.log(`\n🏁 GAME OVER - ${reason}`);
  console.log(`Final Score: ${Math.floor(score)}\n`);
  
  gameRunning = false;
  
  socket.emit('telemetry', {
    fps,
    score: Math.floor(score),
    game_over: true,
    lives,
    duration: parseFloat(duration.toFixed(1))
  });
  
  socket.emit('game:ended', {
    reason,
    final_score: Math.floor(score),
    duration: parseFloat(duration.toFixed(1))
  });
}

socket.on('heartbeat_ack', () => {
  // Silent heartbeat ack
});

socket.on('disconnect', () => {
  console.log('❌ Disconnected');
  gameRunning = false;
});

process.on('SIGINT', () => {
  if (gameRunning) endGame('manual_stop');
  socket.disconnect();
  process.exit(0);
});

console.log('✅ Ready. Start a game from dashboard.\n');
