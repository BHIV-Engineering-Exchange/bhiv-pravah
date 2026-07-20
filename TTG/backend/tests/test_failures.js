
const io = require("socket.io-client");
const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key";
const token = jwt.sign({ userId: "test_user", role: "user" }, JWT_SECRET);

const socket = io("http://localhost:3000", {
  auth: {
    token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX3kwMzAiLCJyb2xlcyI6WyJ1c2VyIl0sImlhdCI6MTc2OTY4ODMwOCwiZXhwIjoxNzY5NjkxOTA4LCJpc3MiOiJtaWNyb2JyaWRnZS5pbnRlcm5hbCJ9.BIG9DeV6SkbXsaxH0cJHN3QUW8gbu8NqVjnoTwUrgzU"
  }
});

socket.on("connect", () => {
  console.log("✅ Connected to server");
  runFailureTests();
});

socket.on("job_status", (job) => {
  console.log(`📦 Job ${job.jobType}: ${job.status}`, job.error ? `❌ ${job.error}` : "");
});

socket.on("engine_job_failed", (data) => {
  console.log(`❌ ENGINE FAILURE: ${data.jobType} - ${data.error}`);
});

function runFailureTests() {
  console.log("\n🧪 Starting Failure Tests...\n");

  // Test 1: Bad Asset
  setTimeout(() => {
    console.log("Test 1: BAD ASSET");
    socket.emit("generate_world", {
      config: {
        schema_version: "1.0",
        world: { id: "test", name: "Test", gravity: [0, -9.8, 0] },
        scene: { id: "scene_1", ambientLight: [1, 1, 1], skybox: "default" },
        entities: [{
          id: "player_1",
          type: "player",
          transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
          material: { shader: "basic", texture: "corrupted_texture.png", color: [1, 1, 1] },
          components: { mesh: "missing_mesh", collider: "box" }
        }],
        quests: []
      },
      submittedAt: Date.now()
    });
  }, 1000);

  // Test 2: Invalid Entity
  setTimeout(() => {
    console.log("\nTest 2: INVALID ENTITY");
    socket.emit("generate_world", {
      config: {
        schema_version: "1.0",
        world: { id: "test", name: "Test", gravity: [0, -9.8, 0] },
        scene: { id: "scene_2", ambientLight: [1, 1, 1], skybox: "default" },
        entities: [{
          id: "invalid_entity_999",
          type: "player",
          transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
          material: { shader: "basic", color: [1, 1, 1] },
          components: { mesh: "player_mesh" }
        }],
        quests: []
      },
      submittedAt: Date.now()
    });
  }, 6000);

  // Test 3: Missing Transform (Invalid Entity)
  setTimeout(() => {
    console.log("\nTest 3: INVALID ENTITY (missing transform)");
    socket.emit("generate_world", {
      config: {
        schema_version: "1.0",
        world: { id: "test", name: "Test", gravity: [0, -9.8, 0] },
        scene: { id: "scene_3", ambientLight: [1, 1, 1], skybox: "default" },
        entities: [{
          id: "player_2",
          type: "player",
          material: { shader: "basic", color: [1, 1, 1] },
          components: { mesh: "player_mesh" }
        }],
        quests: []
      },
      submittedAt: Date.now()
    });
  }, 11000);

  setTimeout(() => {
    console.log("\n✅ All failure tests completed");
    process.exit(0);
  }, 20000);
}

socket.on("disconnect", () => {
  console.log("❌ Disconnected from server");
});
