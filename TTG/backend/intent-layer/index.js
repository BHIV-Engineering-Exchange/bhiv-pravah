const { compile } = require('./compiler/intentCompiler');
const { contractValidator } = require('./validators/contractValidator');

function textToSchema(text) {
  try {
    const schema = compile(text);
    return {
      success: true,
      schema,
      intent: extractIntent(text),
      validation: { valid: true }
    };
  } catch (error) {
    return {
      success: false,
      explanation: error.message,
      validation: { valid: false }
    };
  }
}

function extractIntent(text) {
  const lower = text.toLowerCase();
  return {
    genre: lower.includes('platform') ? 'platformer' : 'runner',
    pacing: lower.includes('fast') ? 'fast' : lower.includes('slow') ? 'slow' : 'medium',
    difficulty: lower.includes('hard') ? 'hard' : lower.includes('easy') ? 'easy' : 'medium',
    abilities: [
      lower.includes('jump') && 'jump',
      lower.includes('dash') && 'dash',
      lower.includes('jetpack') && 'jetpack'
    ].filter(Boolean),
    obstacles: lower.includes('obstacle'),
    pickups: lower.includes('coin') || lower.includes('pickup') || lower.includes('collect')
  };
}

function getSupportedFeatures() {
  return {
    genres: ['runner', 'sidescroller'],
    abilities: ['jump', 'dash', 'jetpack'],
    difficulty: ['easy', 'medium', 'hard'],
    pacing: ['slow', 'medium', 'fast']
  };
}

module.exports = { textToSchema, getSupportedFeatures, compile, contractValidator };
