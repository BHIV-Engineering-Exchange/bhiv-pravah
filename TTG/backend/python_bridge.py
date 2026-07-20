import socketio
import asyncio
import websockets
import json
import time
import hmac
import hashlib
import secrets

DASHBOARD_URL = "http://localhost:3000" 
# DASHBOARD_URL = "https://real-time-dashboard-backend-test.onrender.com"
ENGINE_PORT = 8080
ENGINE_ID = "engine_local_01"
JWT_SECRET = "JWT_SECRET_123456789"
ENGINE_SHARED_SECRET = "ENGINE_SHARED_SECRET_123"

# Use PyJWT for proper JWT generation
try:
    import jwt
    ENGINE_JWT = jwt.encode(
        {"engineId": ENGINE_ID, "role": "engine", "iat": int(time.time()), "exp": int(time.time()) + 3600},
        JWT_SECRET,
        algorithm="HS256"
    )
except ImportError:
    print("  PyJWT not installed. Install with: pip install pyjwt")
    print("Using basic JWT (may not work)")
    import hmac
    import hashlib
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip('=')
    payload = base64.urlsafe_b64encode(json.dumps({
        "engineId": ENGINE_ID,
        "role": "engine",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }).encode()).decode().rstrip('=')
    signature = base64.urlsafe_b64encode(
        hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    ).decode().rstrip('=')
    ENGINE_JWT = f"{header}.{payload}.{signature}"

def sign_message(payload):
    """Sign engine messages with HMAC"""
    nonce = secrets.token_hex(16)
    ts = int(time.time() * 1000)
    message = json.dumps(payload, separators=(',', ':')) + nonce + str(ts)
    sig = hmac.new(ENGINE_SHARED_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {
        "payload": payload,
        "nonce": nonce,
        "ts": ts,
        "sig": sig
    }

sio = socketio.AsyncClient(logger=False, engineio_logger=False)
engine_websocket = None

@sio.event(namespace='/engine')
async def connect():
    print(f" [Bridge] Connected to Cloud: {sio.sid}")
    await asyncio.sleep(1)
    await sio.emit('engine_ready', namespace='/engine')
    print("[Bridge] Ready")
    asyncio.create_task(send_heartbeat())

@sio.on('ready_ack', namespace='/engine')
async def on_ready_ack(data):
    print("[Bridge] Ready ACK")

@sio.on('job:dispatch', namespace='/engine')
async def on_engine_job(data):
    job_id = data.get('job_id') or data.get('jobId')
    job_type = data.get('job_type') or data.get('jobType')
    gameplay_contract = data.get('gameplay_contract') or data.get('gameplayContract') or data.get('payload')
    
    print(f"\n📦 [Cloud -> Bridge] Job: {job_type}")
    print(f"   Job ID: {job_id}")
    
    # Log gameplay details if available
    if isinstance(gameplay_contract, dict):
        game_mode = gameplay_contract.get('game_mode')
        speed = gameplay_contract.get('movement', {}).get('speed')
        obstacles = gameplay_contract.get('spawn_rules', {}).get('obstacles', 0)
        print(f"   Game Mode: {game_mode}")
        print(f"   Speed: {speed}")
        print(f"   Obstacles: {obstacles}")
    
    # Forward to C++ engine
    if engine_websocket:
        try:
            job_packet = {
                "job_id": job_id,
                "job_type": job_type,
                "gameplay_contract": gameplay_contract,
                "payload": {},
                "execution_params": {
                    "priority": "normal",
                    "timeout_ms": 300000
                },
                "submitted_at": int(time.time() * 1000),
                "user_id": "system"
            }
            await engine_websocket.send(json.dumps(job_packet))
            print(f"✅ [Bridge -> Engine] Forwarded\n")
        except Exception as e:
            print(f"❌ [Error] Could not send to Engine: {e}")
    else:
        print(f"⚠️  [Warning] No engine connected\n")

@sio.event(namespace='/engine')
async def disconnect():
    print("✗ [Bridge] Disconnected from Cloud")

async def send_heartbeat():
    while sio.connected:
        await sio.emit('engine_heartbeat', namespace='/engine')
        await asyncio.sleep(3)

async def engine_handler(websocket):
    global engine_websocket
    engine_websocket = websocket
    print("✓ [Bridge] C++ Engine Connected!")
    
    await websocket.send(json.dumps({"command": "START"}))

    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data.get("type") == "TELEMETRY":
                event = data.get("event")
                job_id = data.get("jobId")
                
                if event == "job_started":
                    print(f"  [Engine] Started: {job_id}")
                    await sio.emit('job_started', sign_message({
                        'job_id': job_id,
                        'timestamp': int(time.time() * 1000)
                    }), namespace='/engine')
                
                elif event == "job_progress":
                    await sio.emit('job_progress', sign_message({
                        'job_id': job_id,
                        'progress': data.get("progress", 0),
                        'timestamp': int(time.time() * 1000)
                    }), namespace='/engine')
                
                elif event == "job_completed":
                    print(f" [Engine] Completed: {job_id}")
                    await sio.emit('job_completed', sign_message({
                        'job_id': job_id,
                        'result': data.get('result', {'success': True}),
                        'timestamp': int(time.time() * 1000)
                    }), namespace='/engine')
                
                elif event == "job_failed":
                    print(f" [Engine] Failed: {job_id}")
                    await sio.emit('job_failed', sign_message({
                        'job_id': job_id,
                        'error': data.get("error", "Unknown error"),
                        'details': data.get('details', ''),
                        'timestamp': int(time.time() * 1000)
                    }), namespace='/engine')
                
                elif event == "tick_update":
                    print(f" [Engine Heartbeat] FPS: {data['data']['fps']:.1f}")
            
            # Handle telemetry events (game telemetry)
            elif data.get("type") == "GAME_TELEMETRY":
                # Forward game telemetry to dashboard
                await sio.emit('telemetry', data.get('data', {}), namespace='/engine')
            
            elif data.get("type") == "GAME_EVENT":
                event = data.get("event")
                if event == "game_started":
                    await sio.emit('game:started', data.get('data', {}), namespace='/engine')
                elif event == "game_ended":
                    await sio.emit('game:ended', data.get('data', {}), namespace='/engine')

    except websockets.exceptions.ConnectionClosed:
        print("✗ [Bridge] Engine Disconnected")
        engine_websocket = None

async def main():
    print("[Bridge] Starting...")
    
    # Start local WebSocket server for C++ engine
    server = await websockets.serve(engine_handler, "localhost", ENGINE_PORT)
    print(f" [Bridge] Local Server running on ws://localhost:{ENGINE_PORT}")
    
    # Connect to cloud dashboard
    try:
        await sio.connect(
            DASHBOARD_URL,
            namespaces=['/engine'],
            transports=['websocket'],
            auth={"token": ENGINE_JWT}
        )
    except Exception as e:
        print(f" [Fatal] Cloud Connection Failed: {e}")
        return
    
    await asyncio.Future()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bridge shutting down...")
