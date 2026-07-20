// prompt_runner/adapter.js - Adapter for external Prompt Runner service
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

const PROMPT_RUNNER_URL = process.env.PROMPT_RUNNER_URL || 'https://prompt-runner.onrender.com';

/**
 * Call external Prompt Runner service
 * @param {string} userPrompt - Natural language prompt
 * @returns {Promise<Object>} Prompt Runner output (module, intent, topic, tasks, output_format)
 */
async function callPromptRunner(userPrompt) {
  try {
    const response = await axios.post(`${PROMPT_RUNNER_URL}/run`, {
      prompt: userPrompt
    }, {
      timeout: 60000
    });

    const { status, data } = response.data;
    if (status !== 'success' || !data) {
      throw new Error('Prompt Runner returned non-success status');
    }

    const instruction = data.instruction;
    if (!instruction || !instruction.module) {
      throw new Error('Prompt Runner returned unexpected shape');
    }

    console.log('[PROMPT_RUNNER] Raw schema from Groq:');
    console.log(JSON.stringify(instruction, null, 2));

    // Call Core Integrator to generate full blueprint
    let blueprint = data.blueprint || null;
    try {
      const bpRes = await axios.post(
        'https://core-integrator-collaborative.onrender.com/creator-core/generate-blueprint',
        {
          prompt:          instruction.prompt,
          module:          instruction.module,
          intent:          instruction.intent,
          topic:           instruction.topic,
          tasks:           instruction.tasks,
          output_format:   instruction.output_format,
          product_context: instruction.product_context || 'creator_core'
        },
        { timeout: 15000 }
      );
      blueprint = bpRes.data;
      console.log('[CORE_INTEGRATOR] Blueprint generated:', JSON.stringify(blueprint, null, 2));
    } catch (bpErr) {
      console.warn('[CORE_INTEGRATOR] Blueprint generation failed (non-critical):', bpErr.message);
    }

    console.log('[PROMPT_RUNNER] Response received:', JSON.stringify(instruction));
    console.log('[PROMPT_RUNNER] Final output with blueprint:');
    console.log(JSON.stringify({ ...instruction, blueprint }, null, 2));
    return { ...instruction, blueprint };
  } catch (error) {
    console.error('[PROMPT_RUNNER] Error:', error.message);
    throw new Error(`Prompt Runner failed: ${error.message}`);
  }
}

/**
 * Convert Prompt Runner output to execution schema format
 * @param {Object} promptRunnerOutput - Output from Prompt Runner
 * @param {string} userId - User ID
 * @returns {Object} Execution data ready for registry
 */
function convertToExecutionSchema(promptRunnerOutput, userId = 'anonymous') {
  const { module, intent, topic, tasks, output_format, prompt, blueprint } = promptRunnerOutput;
  
  if (!module || !intent || !topic || !tasks || !output_format) {
    throw new Error('Invalid Prompt Runner output: missing required fields');
  }

  // Map prompt runner topic/intent to a game_mode the dispatcher understands
  const topicLower = (topic + ' ' + intent + ' ' + (prompt || '')).toLowerCase();
  let game_mode = 'runner'; // default
  if (topicLower.includes('arena') || topicLower.includes('combat') || topicLower.includes('survival') || topicLower.includes('enemy') || topicLower.includes('free roam') || topicLower.includes('open')) {
    game_mode = 'arena';
  } else if ((topicLower.includes('platform') || topicLower.includes('side')) && !topicLower.includes('runner')) {
    game_mode = 'sidescroller';
  }
  
  const execution_id = `exec_${Date.now()}_${uuidv4().slice(0, 8)}`;
  const trace_id = `trace_${Date.now()}`;
  
  return {
    execution_id,
    trace_id,
    user_id: userId,
    intent: { prompt: prompt || topic },
    executionSchema: {
      game_mode,
      module,
      intent,
      movement: { speed: topicLower.includes('fast') ? 8 : topicLower.includes('slow') ? 3 : 5 },
      physics: { gravity: -9.8, friction: 0.5, bounce: 0.3, air_resistance: 0.1, collision_force: 1 },
      spawn_rules: { obstacles: 2, frequency: topicLower.includes('hard') ? 1.5 : 2.0 },
      score_rules: { distance: 1, collectibles: 10 },
      end_conditions: ['collision'],
      player_params: { health: topicLower.includes('easy') ? 5 : 3, jetpack: false },
      world_params: { theme: 'default' },
      data: { topic, parameters: {}, original_prompt: prompt || topic },
      tasks,
      output_format,
      blueprint: blueprint || null,
      context: { source: 'prompt_runner' }
    },
    timestamp: Date.now()
  };
}

/**
 * Check if Prompt Runner service is available
 * @returns {Promise<boolean>}
 */
async function checkPromptRunnerHealth() {
  try {
    const response = await axios.get(`${PROMPT_RUNNER_URL}/health`, { timeout: 5000 });
    return response.status === 200 && response.data?.status === 'healthy';
  } catch (error) {
    return false;
  }
}

module.exports = {
  callPromptRunner,
  convertToExecutionSchema,
  checkPromptRunnerHealth
};
