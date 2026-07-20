// contract_validator.js - Standalone Engine Job Contract Validator

const SUPPORTED_JOB_TYPES = [
  'START_GAME',
  'STOP_GAME',
  'UPDATE_CONFIG',
  'BUILD_SCENE',
  'SPAWN_ENTITY',
  'SPAWN_ENTITIES',
  'START_LOOP',
  'LOAD_ASSETS',
  'MOVE_ENTITY',
  'UPDATE_PROPERTY',
  'DELETE_ENTITY',
  'EMIT_EVENT'
];

function validateContract(contract) {
  const errors = [];

  // Check contract is object
  if (!contract || typeof contract !== 'object' || Array.isArray(contract)) {
    return { valid: false, status: 'CONTRACT_REJECTED', errors: ['Contract must be an object'] };
  }

  // Check for security issues FIRST
  const keys = Object.keys(contract);
  if (keys.includes('__proto__') || keys.includes('constructor') || keys.includes('prototype')) {
    return { valid: false, status: 'CONTRACT_REJECTED', errors: ['Security violation: prototype pollution detected'] };
  }

  // Check required fields
  if (!contract.jobType || typeof contract.jobType !== 'string') {
    errors.push('Missing or invalid jobType');
  }

  if (!contract.payload || typeof contract.payload !== 'object') {
    errors.push('Missing or invalid payload');
  }

  // Check jobType is supported
  if (contract.jobType && !SUPPORTED_JOB_TYPES.includes(contract.jobType)) {
    errors.push(`Unsupported jobType: ${contract.jobType}`);
  }

  // Validate payload based on jobType
  if (contract.payload && contract.jobType) {
    const payloadErrors = validatePayload(contract.jobType, contract.payload);
    errors.push(...payloadErrors);
  }

  if (errors.length > 0) {
    return { valid: false, status: 'CONTRACT_REJECTED', errors };
  }

  return { valid: true, status: 'VALID', errors: [] };
}

function validatePayload(jobType, payload) {
  const errors = [];

  switch (jobType) {
    case 'BUILD_SCENE':
      if (!payload.sceneId || typeof payload.sceneId !== 'string') {
        errors.push('BUILD_SCENE requires valid sceneId');
      }
      if (payload.ambientLight && !isValidVector3(payload.ambientLight)) {
        errors.push('ambientLight must be [x, y, z] array');
      }
      break;

    case 'SPAWN_ENTITY':
    case 'SPAWN_ENTITIES':
      if (!payload.id || typeof payload.id !== 'string' || payload.id.trim() === '') {
        errors.push('SPAWN_ENTITY requires valid entity id');
      }
      if (payload.id && !/^[a-zA-Z0-9_-]+$/.test(payload.id)) {
        errors.push('Entity id contains invalid characters');
      }
      if (payload.transform) {
        const transformErrors = validateTransform(payload.transform);
        errors.push(...transformErrors);
      }
      break;

    case 'START_LOOP':
      if (!payload.game_mode || typeof payload.game_mode !== 'string') {
        errors.push('START_LOOP requires valid game_mode');
      }
      break;

    case 'LOAD_ASSETS':
      if (!Array.isArray(payload.assets) || payload.assets.length === 0) {
        errors.push('LOAD_ASSETS requires non-empty assets array');
      }
      break;

    case 'MOVE_ENTITY':
      if (!payload.id || typeof payload.id !== 'string') {
        errors.push('MOVE_ENTITY requires valid entity id');
      }
      if (payload.position && !isValidVector3(payload.position)) {
        errors.push('position must be [x, y, z] array');
      }
      break;

    case 'START_GAME':
      // Gameplay contract validation
      if (!payload.game_mode) {
        errors.push('START_GAME requires game_mode');
      }
      if (!payload.movement || typeof payload.movement.speed !== 'number') {
        errors.push('START_GAME requires movement.speed');
      }
      if (payload.movement && (payload.movement.speed < 1 || payload.movement.speed > 15)) {
        errors.push('movement.speed must be between 1 and 15');
      }
      if (payload.physics && payload.physics.gravity) {
        if (payload.physics.gravity < -20 || payload.physics.gravity > 0) {
          errors.push('physics.gravity must be between -20 and 0');
        }
      }
      break;

    case 'STOP_GAME':
      // Minimal validation for stop game
      break;

    case 'UPDATE_CONFIG':
      // Config updates should have some payload
      if (Object.keys(payload).length === 0) {
        errors.push('UPDATE_CONFIG requires non-empty payload');
      }
      break;
  }

  return errors;
}

function validateTransform(transform) {
  const errors = [];

  if (typeof transform !== 'object' || Array.isArray(transform)) {
    errors.push('transform must be an object');
    return errors;
  }

  if (transform.position && !isValidVector3(transform.position)) {
    errors.push('transform.position must be [x, y, z] array with valid numbers');
  }

  if (transform.rotation && !isValidVector3(transform.rotation)) {
    errors.push('transform.rotation must be [x, y, z] array with valid numbers');
  }

  if (transform.scale && !isValidVector3(transform.scale)) {
    errors.push('transform.scale must be [x, y, z] array with valid numbers');
  }

  return errors;
}

function isValidVector3(vec) {
  if (!Array.isArray(vec) || vec.length !== 3) return false;
  return vec.every(v => typeof v === 'number' && !isNaN(v) && isFinite(v));
}

// CLI Test Runner
if (require.main === module) {
  console.log('=== Contract Validator Test Harness ===\n');

  const testCases = [
    {
      name: 'Valid BUILD_SCENE',
      contract: {
        jobType: 'BUILD_SCENE',
        payload: {
          sceneId: 'forest_scene',
          ambientLight: [0.4, 0.6, 0.4],
          skybox: 'forest_sky'
        }
      }
    },
    {
      name: 'Valid SPAWN_ENTITY',
      contract: {
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'player_1',
          type: 'player',
          transform: {
            position: [0, 0, 0],
            rotation: [0, 0, 0],
            scale: [1, 1, 1]
          }
        }
      }
    },
    {
      name: 'Valid START_GAME',
      contract: {
        jobType: 'START_GAME',
        payload: {
          game_mode: 'runner',
          movement: { speed: 5, jump_height: 3 },
          camera: { type: 'third_person' },
          spawn_rules: { obstacles: 2 },
          score_rules: {},
          end_conditions: ['collision']
        }
      }
    },
    {
      name: 'Invalid - Missing jobType',
      contract: {
        payload: { sceneId: 'test' }
      }
    },
    {
      name: 'Invalid - Unsupported jobType',
      contract: {
        jobType: 'HACK_SYSTEM',
        payload: {}
      }
    },
    {
      name: 'Invalid - Malformed transform',
      contract: {
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'player_1',
          transform: {
            position: [0, 'invalid', 0]
          }
        }
      }
    },
    {
      name: 'Invalid - Bad entity ID',
      contract: {
        jobType: 'SPAWN_ENTITY',
        payload: {
          id: 'player@#$%',
          transform: { position: [0, 0, 0] }
        }
      }
    },
    {
      name: 'Invalid - Speed out of range',
      contract: {
        jobType: 'START_GAME',
        payload: {
          game_mode: 'runner',
          movement: { speed: 50 }
        }
      }
    },
    {
      name: 'Invalid - Prototype pollution attempt',
      contract: JSON.parse('{"jobType":"BUILD_SCENE","payload":{"sceneId":"test"},"__proto__":{"admin":true}}')
    }
  ];

  let passed = 0;
  let failed = 0;

  testCases.forEach((test, idx) => {
    const result = validateContract(test.contract);
    const expectValid = !test.name.startsWith('Invalid');
    const success = result.valid === expectValid;

    console.log(`Test ${idx + 1}: ${test.name}`);
    console.log(`  Status: ${result.status}`);
    if (result.errors.length > 0) {
      console.log(`  Errors: ${result.errors.join(', ')}`);
    }
    console.log(`  Result: ${success ? '✓ PASS' : '✗ FAIL'}\n`);

    if (success) passed++;
    else failed++;
  });

  console.log(`=== Test Summary ===`);
  console.log(`Passed: ${passed}/${testCases.length}`);
  console.log(`Failed: ${failed}/${testCases.length}`);
  console.log(`Success Rate: ${((passed / testCases.length) * 100).toFixed(1)}%`);
}

module.exports = { validateContract, SUPPORTED_JOB_TYPES };
