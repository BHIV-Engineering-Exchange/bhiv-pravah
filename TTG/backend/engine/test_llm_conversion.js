// Test LLM Output → Engine Schema Conversion

const { convertLLMToEngineSchema } = require('./engine_adapter');
const validateWorldSpec = require('./world_spec_validator');

console.log('=== TESTING LLM → ENGINE SCHEMA CONVERSION ===\n');

// Real LLM output format (from your Python code)
const llmOutput = {
  "metadata": {
    "level_name": "The Ancient Forest",
    "description": "An immersive forest adventure: Create a forest level where the player has to complete 3 quests to save a village",
    "difficulty": "medium",
    "estimated_playtime": "30-40 minutes",
    "theme": "forest"
  },
  "environment": {
    "type": "forest",
    "setting": "A lush woodland area with ancient ruins and artifacts",
    "terrain": ["grass", "dirt_paths", "rocky_areas", "streams"],
    "lighting": "filtered_sunlight",
    "weather": "clear",
    "atmosphere": "mysterious",
    "size": "medium",
    "assets": ["trees", "bushes", "rocks", "flowers", "mushrooms", "ancient_ruins", "old_statues"]
  },
  "quests": [
    {
      "id": "quest_1",
      "name": "Gather Sacred Items",
      "type": "main",
      "objective": "Collect 3 herbs from the forest",
      "description": "Ancient herbs are needed to save the village",
      "requirements": [],
      "rewards": {
        "experience": 100,
        "gold": 50,
        "items": ["quest_1_reward"]
      },
      "location": "forest",
      "estimated_time": "10 minutes"
    },
    {
      "id": "quest_2",
      "name": "Defeat the Guardian",
      "type": "main",
      "objective": "Defeat the guardian that guards the temple",
      "description": "A powerful guardian blocks your path to treasure",
      "requirements": ["complete_quest_1"],
      "rewards": {
        "experience": 150,
        "gold": 75,
        "items": ["quest_2_reward"]
      },
      "location": "forest",
      "estimated_time": "15 minutes"
    },
    {
      "id": "quest_3",
      "name": "Save the Villagers",
      "type": "side",
      "objective": "Rescue 3 villagers from bandits",
      "description": "Innocent villagers are trapped and need your help",
      "requirements": ["complete_quest_2"],
      "rewards": {
        "experience": 200,
        "gold": 100,
        "items": ["quest_3_reward"]
      },
      "location": "forest",
      "estimated_time": "20 minutes"
    }
  ],
  "npcs": [
    {
      "id": "villager_npc",
      "name": "Village Elder",
      "role": "quest_giver",
      "type": "friendly",
      "location": "village_center",
      "dialogue": ["Welcome, brave adventurer!", "Our village needs your help!", "Thank you for coming!"],
      "behavior": "stationary_helpful",
      "stats": {
        "health": 100,
        "attack": 0,
        "defense": 10
      },
      "inventory": ["villager_item", "common_item"]
    },
    {
      "id": "enemy_npc",
      "name": "Hostile Creature",
      "role": "antagonist",
      "type": "hostile",
      "location": "dark_forest",
      "dialogue": ["*growls menacingly*", "*attacks without warning*"],
      "behavior": "aggressive_patrol",
      "stats": {
        "health": 80,
        "attack": 25,
        "defense": 15
      },
      "inventory": ["enemy_item", "common_item"]
    }
  ],
  "physics": {
    "player_abilities": ["walk", "run", "jump", "interact"],
    "movement_speed": 5.0,
    "jump_height": 2.0,
    "combat_system": "action_based",
    "interaction_mechanics": ["pickup_items", "talk_to_npcs", "activate_objects"],
    "special_mechanics": ["quest_tracking", "inventory_system"]
  },
  "win_conditions": ["Complete all main quests"],
  "lose_conditions": ["Player health reaches 0"],
  "assets_required": {
    "models": ["tree_oak", "tree_pine", "bush_berry", "rock_moss", "flower_wild"],
    "textures": ["bark_oak", "grass_forest", "dirt_path", "moss_rock", "leaf_texture"],
    "sounds": ["ambient_background", "footsteps", "ui_sounds"],
    "effects": ["particle_dust", "light_rays"],
    "animations": ["player_walk", "player_idle"]
  }
};

console.log('📥 INPUT: LLM Output');
console.log('Level:', llmOutput.metadata.level_name);
console.log('NPCs:', llmOutput.npcs.length);
console.log('Quests:', llmOutput.quests.length);
console.log('Environment:', llmOutput.environment.type);
console.log('');

// Convert
console.log('🔄 CONVERTING...\n');
const engineSchema = convertLLMToEngineSchema(llmOutput);

console.log('📤 OUTPUT: Engine Schema v1.0');
console.log('World ID:', engineSchema.world.id);
console.log('World Name:', engineSchema.world.name);
console.log('Scene ID:', engineSchema.scene.id);
console.log('Ambient Light:', engineSchema.scene.ambientLight);
console.log('Skybox:', engineSchema.scene.skybox);
console.log('Entities:', engineSchema.entities.length);
console.log('Quests:', engineSchema.quests.length);
console.log('');

// Show entities
console.log('🎮 ENTITIES:');
engineSchema.entities.forEach((e, i) => {
  console.log(`  ${i + 1}. ${e.id} (${e.type})`);
  console.log(`     Position: [${e.transform.position.join(', ')}]`);
  console.log(`     Mesh: ${e.components.mesh}`);
  console.log(`     Script: ${e.components.script || 'none'}`);
});
console.log('');

// Show quests
console.log('📋 QUESTS:');
engineSchema.quests.forEach((q, i) => {
  console.log(`  ${i + 1}. ${q.id}`);
  console.log(`     Trigger: ${q.triggerEntity}`);
  console.log(`     Goal: ${q.goal}`);
});
console.log('');

// Validate against frozen schema
console.log('✅ VALIDATING AGAINST FROZEN SCHEMA...');
try {
  validateWorldSpec(engineSchema);
  console.log('✅ VALIDATION PASSED!\n');
} catch (err) {
  console.error('❌ VALIDATION FAILED:');
  console.error(err.message);
  process.exit(1);
}

// Output full schema
console.log('📄 FULL ENGINE SCHEMA:');
console.log(JSON.stringify(engineSchema, null, 2));
console.log('');

console.log('=== TEST COMPLETE ===');
console.log('✅ LLM output successfully converted to engine schema v1.0');
console.log('✅ Schema validated against frozen specification');
console.log('✅ Ready for Atharva\'s OpenGL engine');
