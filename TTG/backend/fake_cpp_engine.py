import asyncio
import websockets
import json
import random
import time

# Game state
game_running = False
score = 0
lives = 3
duration = 0
fps = 60
game_mode = None
global_speed = 5.0
websocket = None

async def send_telemetry():
    """Send real-time game telemetry"""
    global websocket, game_running, score, lives, duration, fps, global_speed
    
    while game_running:
        await asyncio.sleep(0.1)
        duration += 0.1
        score += int(10 * (global_speed / 5.0))  # Score based on speed
        fps = random.randint(55, 60)
        
        # Random coin pickup
        if random.random() < 0.1:
            score += 50
            print(f"💎 Coin collected! +50")
        
        # Random obstacle hit
        if random.random() < 0.05 and lives > 0:
            lives -= 1
            print(f"💔 Hit obstacle! Lives: {lives}")
            if lives == 0:
                await end_game('player_death')
                return
        
        # Send telemetry to bridge
        await websocket.send(json.dumps({
            "type": "GAME_TELEMETRY",
            "data": {
                "fps": fps,
                "score": int(score),
                "game_over": False,
                "lives": lives,
                "duration": round(duration, 1)
            }
        }))
        
        # Log every second
        if int(duration) % 1 == 0 and duration % 1 < 0.15:
            print(f"⏱️  {duration:.1f}s | Score: {int(score)} | Lives: {lives} | FPS: {fps}")
        
        # End after 30 seconds
        if duration >= 30:
            await end_game('time_up')
            return

async def end_game(reason):
    """End game and send final telemetry"""
    global websocket, game_running, score, duration
    
    print(f"\n🏁 GAME OVER - {reason}")
    print(f"Final Score: {int(score)}")
    print(f"Duration: {duration:.1f}s\n")
    
    game_running = False
    
    # Send final telemetry
    await websocket.send(json.dumps({
        "type": "GAME_TELEMETRY",
        "data": {
            "fps": fps,
            "score": int(score),
            "game_over": True,
            "lives": lives,
            "duration": round(duration, 1)
        }
    }))
    
    # Send game ended event
    await websocket.send(json.dumps({
        "type": "GAME_EVENT",
        "event": "game_ended",
        "data": {
            "reason": reason,
            "final_score": int(score),
            "duration": round(duration, 1)
        }
    }))

async def fake_cpp_engine():
    global websocket, game_running, score, lives, duration, game_mode, global_speed
    
    uri = "ws://localhost:8080"
    
    print("🎮 Fake C++ Engine Starting...")
    print(f"   Connecting to Bridge: {uri}\n")
    
    async with websockets.connect(uri) as ws:
        websocket = ws
        print("✅ Connected to Bridge\n")
        
        # Wait for START command from bridge
        message = await websocket.recv()
        data = json.loads(message)
        print(f"[Engine] Received: {data.get('command')}\n")
        
        # Process jobs from bridge
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            job_id = data.get("job_id") or data.get("jobId")
            job_type = data.get("job_type") or data.get("jobType")
            gameplay_contract = data.get("gameplay_contract") or data.get("gameplayContract") or data.get("payload")
            
            print(f"📦 Received Job: {job_type}")
            print(f"   Job ID: {job_id}")
            
            # Parse gameplay contract
            if isinstance(gameplay_contract, dict):
                game_mode = gameplay_contract.get('game_mode', 'runner')
                global_speed = gameplay_contract.get('movement', {}).get('speed', 5.0)
                obstacles = gameplay_contract.get('spawn_rules', {}).get('obstacles', 0)
                lives = gameplay_contract.get('player_params', {}).get('health', 3)
                
                print(f"   Game Mode: {game_mode}")
                print(f"   Speed: {global_speed}")
                print(f"   Obstacles: {obstacles}")
                print(f"   Lives: {lives}")
            
            # Send job_started
            await websocket.send(json.dumps({
                "type": "TELEMETRY",
                "event": "job_started",
                "jobId": job_id
            }))
            
            await asyncio.sleep(0.5)
            
            # Send job_completed
            await websocket.send(json.dumps({
                "type": "TELEMETRY",
                "event": "job_completed",
                "jobId": job_id,
                "result": {"success": True}
            }))
            
            # Start game if START_LOOP job
            if job_type == 'START_LOOP':
                await asyncio.sleep(1)
                print('\n🎮 GAME STARTED\n')
                
                game_running = True
                score = 0
                lives = gameplay_contract.get('params', {}).get('end_condition', {}).get('value', 3)
                duration = 0
                
                # Send game started event
                await websocket.send(json.dumps({
                    "type": "GAME_EVENT",
                    "event": "game_started",
                    "data": {
                        "game_mode": game_mode,
                        "speed": global_speed
                    }
                }))
                
                # Start telemetry loop
                asyncio.create_task(send_telemetry())

if __name__ == '__main__':
    try:
        asyncio.run(fake_cpp_engine())
    except KeyboardInterrupt:
        print('\n🛑 Shutting down...')
