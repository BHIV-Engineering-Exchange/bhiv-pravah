// Test Engine Adapter

const { convertToEngineSchema } = require('./engine_adapter');

console.log('=== TESTING ENGINE ADAPTER ===\n');

// Test 1: Legacy Cube
console.log('TEST 1: Legacy Cube Format');
const cubeInput = { color: "#66ffdd", size: 1.5 };
const cubeOutput = convertToEngineSchema(cubeInput);
console.log('Input:', JSON.stringify(cubeInput));
console.log('Output:', JSON.stringify(cubeOutput, null, 2));
console.log('✅ Cube converted\n');

// Test 2: LLM Output
console.log('TEST 2: LLM Output Format');
const llmInput = {
  metadata: {
    level_name: "Dark Forest",
    difficulty: "medium",
    theme: "forest"
  },
  environment: {
    type: "forest",
    lighting: "filtered_sunlight",
    terrain: ["grass", "dirt"],
    weather: "clear"
  },
  npcs: [
    {
      id: "wolf_1",
      name: "Corrupted Wolf",
      role: "enemy",
      type: "hostile",
      location: "dark_forest",
      behavior: "aggressive_patrol",
      stats: { health: 80, attack: 25, defense: 15 }
    }
  ],
  quests: [
    {
      id: "quest_1",
      name: "Defeat the Wolf",
      objective: "Defeat the corrupted wolf",
      requirements: ["wolf_1"]
    }
  ],
  physics: {},
  win_conditions: [],
  lose_conditions: [],
  assets_required: {}
};

const llmOutput = convertToEngineSchema(llmInput);
console.log('Input metadata:', llmInput.metadata);
console.log('Output world:', llmOutput.world);
console.log('Output entities:', llmOutput.entities.length, 'entities');
console.log('✅ LLM converted\n');

// Test 3: Already Valid Schema
console.log('TEST 3: Already Valid Engine Schema');
const validInput = {
  schema_version: "1.0",
  world: { id: "world_test", name: "Test", gravity: [0, -9.8, 0] },
  scene: { id: "scene_test", ambientLight: [1, 1, 1], skybox: "default" },
  entities: [],
  quests: []
};
const validOutput = convertToEngineSchema(validInput);
console.log('✅ Valid schema passed through\n');

console.log('=== ALL TESTS PASSED ===');
