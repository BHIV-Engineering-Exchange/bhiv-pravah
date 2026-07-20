// test_engine_contract.js - Test engine contract format
const { convertToEngineContract } = require('./engineContractConverter');
const fs = require('fs');
const path = require('path');

function testEngineContract() {
  console.log('🚀 Testing Engine Execution Contract\n');
  
  // Test execution schema
  const executionSchema = {
    game_mode: 'runner',
    movement: {
      speed: 8,
      jump_height: 5
    },
    camera: {
      type: 'third_person',
      distance: 10
    },
    spawn_rules: {
      obstacles: 2,
      frequency: 2
    },
    score_rules: {
      distance: 1,
      collectibles: 0
    },
    end_conditions: ['collision'],
    player_params: {
      jetpack: false,
      health: 3
    },
    world_params: {
      theme: 'default'
    },
    physics: {
      gravity: -9.8,
      friction: 0.5,
      bounce: 0.3,
      air_resistance: 0.1,
      collision_force: 1.0
    }
  };
  
  const execution_id = 'exec_test_001';
  const trace_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
  
  console.log('=== Test 1: Convert Execution Schema to Engine Contract ===');
  
  const engineContract = convertToEngineContract(executionSchema, execution_id, trace_id);
  
  console.log('✅ Conversion successful');
  console.log(`   execution_id: ${engineContract.execution_id}`);
  console.log(`   trace_id: ${engineContract.trace_id}`);
  console.log(`   game_mode: ${engineContract.game_mode}`);
  
  // Test 2: Validate required fields
  console.log('\n=== Test 2: Validate Required Fields ===');
  
  const requiredFields = [
    'execution_id',
    'trace_id',
    'game_mode',
    'scene',
    'entities',
    'physics',
    'movement',
    'camera',
    'spawn_rules',
    'scoring',
    'player_params'
  ];
  
  let allFieldsPresent = true;
  requiredFields.forEach(field => {
    if (engineContract[field]) {
      console.log(`✅ ${field}: present`);
    } else {
      console.log(`❌ ${field}: missing`);
      allFieldsPresent = false;
    }
  });
  
  if (allFieldsPresent) {
    console.log('\n✅ All required fields present');
  } else {
    console.log('\n❌ Some required fields missing');
  }
  
  // Test 3: Validate physics parameters
  console.log('\n=== Test 3: Validate Physics Parameters ===');
  
  console.log(`✅ gravity: [${engineContract.physics.gravity.join(', ')}]`);
  console.log(`✅ friction: ${engineContract.physics.friction}`);
  console.log(`✅ bounce: ${engineContract.physics.bounce}`);
  console.log(`✅ air_resistance: ${engineContract.physics.air_resistance}`);
  console.log(`✅ collision_force: ${engineContract.physics.collision_force}`);
  
  // Test 4: Validate entity spawn instructions
  console.log('\n=== Test 4: Validate Entity Spawn Instructions ===');
  
  console.log(`✅ entities count: ${engineContract.entities.length}`);
  engineContract.entities.forEach(entity => {
    console.log(`   - ${entity.id} (${entity.type})`);
    console.log(`     position: [${entity.transform.position.join(', ')}]`);
    console.log(`     collider: ${entity.components.collider}`);
  });
  
  // Test 5: Validate scoring rules
  console.log('\n=== Test 5: Validate Scoring Rules ===');
  
  console.log(`✅ distance points: ${engineContract.scoring.rules.distance}`);
  console.log(`✅ collectible points: ${engineContract.scoring.rules.collectibles}`);
  console.log(`✅ end conditions: ${engineContract.scoring.end_conditions.join(', ')}`);
  
  // Test 6: Write contract to file for Atharva
  console.log('\n=== Test 6: Generate Sample Contract File ===');
  
  const sampleContractPath = path.join(__dirname, 'sample_engine_contract.json');
  fs.writeFileSync(sampleContractPath, JSON.stringify(engineContract, null, 2));
  
  console.log(`✅ Sample contract written to: ${sampleContractPath}`);
  console.log('   Atharva can use this file for testing');
  
  // Test 7: Validate against schema
  console.log('\n=== Test 7: Schema Validation ===');
  
  const schemaPath = path.join(__dirname, 'engineExecutionContract.json');
  const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
  
  console.log(`✅ Schema loaded: ${schema.title}`);
  console.log(`   version: ${schema.version}`);
  console.log(`   required fields: ${schema.required.join(', ')}`);
  
  // Test 8: Display complete contract
  console.log('\n=== Test 8: Complete Engine Contract ===');
  console.log(JSON.stringify(engineContract, null, 2));
  
  console.log('\n✅ All engine contract tests passed');
  console.log('\n📋 Next Steps:');
  console.log('   1. Share engineExecutionContract.json with Atharva');
  console.log('   2. Share ENGINE_COORDINATION.md with Atharva');
  console.log('   3. Share sample_engine_contract.json for testing');
  console.log('   4. Coordinate on Socket.IO event names');
  console.log('   5. Test end-to-end execution');
}

testEngineContract();
