/**
 * TTG Integration - Text to JSON Converter
 * Extracted from: TTG_HandOver/02-Web-Interface/backend/TTG_MAIN_SERVER.py
 * 
 * EXTRACTED:
 * - Theme detection logic (lines 200-250)
 * - Text analysis functions (lines 250-350)
 * - Parameter extraction (lines 350-450)
 * 
 * REMOVED:
 * - UE5 integration
 * - Complex NPC/Quest systems
 * - Ollama LLM integration
 * - Flask server code
 */

/**
 * Analyze theme from user text
 * Extracted from: analyze_theme() in TTG_MAIN_SERVER.py
 */
function analyzeTheme(promptLower, words = []) {
  // Theme detection with priority order (more specific first)
  const themeKeywords = {
    'runner': ['run', 'runner', 'endless', 'chase', 'fast', 'sprint'],
    'side_scroller': ['side', 'platform', 'jump', 'scroll', 'mario', 'platformer'],
    'alien': ['alien', 'extraterrestrial', 'ufo', 'space', 'sci-fi', 'futuristic'],
    'horror': ['horror', 'scary', 'haunted', 'ghost', 'zombie', 'dark'],
    'medieval': ['medieval', 'castle', 'knight', 'dragon', 'sword', 'kingdom'],
    'fantasy': ['magic', 'wizard', 'fairy', 'forest', 'crystal', 'magical']
  };

  let detectedTheme = 'runner'; // default

  // Check themes in priority order
  for (const [theme, keywords] of Object.entries(themeKeywords)) {
    if (keywords.some(keyword => promptLower.includes(keyword))) {
      detectedTheme = theme;
      console.log(`🎯 Detected theme: ${detectedTheme}`);
      break;
    }
  }

  return {
    type: detectedTheme,
    atmosphere: promptLower.includes('dark') ? 'mysterious' : 'adventurous',
    size: detectSize(promptLower)
  };
}

/**
 * Detect world size from prompt
 */
function detectSize(promptLower) {
  if (['small', 'tiny', 'mini', 'little'].some(w => promptLower.includes(w))) {
    return 'small';
  }
  if (['large', 'huge', 'massive', 'giant', 'vast'].some(w => promptLower.includes(w))) {
    return 'large';
  }
  return 'medium';
}

/**
 * Detect movement speed from prompt
 * Extracted from: detect_speed() logic
 */
function detectSpeed(promptLower) {
  if (['fast', 'quick', 'rapid', 'speedy'].some(w => promptLower.includes(w))) {
    return 8.0;
  }
  if (['slow', 'sluggish', 'careful'].some(w => promptLower.includes(w))) {
    return 3.0;
  }
  return 5.0; // default
}

/**
 * Detect difficulty from prompt
 * Extracted from: _determine_difficulty() in prompt_parser.py
 */
function detectDifficulty(promptLower) {
  const difficultyKeywords = {
    'easy': ['easy', 'simple', 'beginner', 'casual', 'peaceful'],
    'hard': ['hard', 'difficult', 'challenging', 'complex', 'expert', 'hardcore'],
    'medium': ['medium', 'moderate', 'balanced', 'normal']
  };

  for (const [diff, keywords] of Object.entries(difficultyKeywords)) {
    if (keywords.some(kw => promptLower.includes(kw))) {
      return diff;
    }
  }

  return 'medium'; // default
}

/**
 * Detect obstacles from prompt
 */
function detectObstacles(promptLower, theme) {
  const obstacles = [];

  if (promptLower.includes('obstacle') || promptLower.includes('avoid')) {
    if (theme === 'runner' || theme === 'side_scroller') {
      obstacles.push('rock', 'tree', 'pit');
    }
  }

  return obstacles.length > 0 ? obstacles : ['rock']; // default
}

/**
 * Main function: Analyze text and generate game data
 * Extracted from: generate_intelligent_world_data() in TTG_MAIN_SERVER.py
 */
function analyzePromptIntelligently(prompt, options = {}) {
  const promptLower = prompt.toLowerCase();
  const words = promptLower.split(/\s+/);

  // Analyze theme
  const themeAnalysis = analyzeTheme(promptLower, words);

  // Generate world name
  const worldName = generateWorldName(prompt, themeAnalysis.type);

  const worldData = {
    id: `world_${Date.now()}`,
    name: worldName,
    description: prompt,
    theme: themeAnalysis.type,
    created_at: new Date().toISOString(),
    environment: themeAnalysis,
    params: {
      movement_speed: detectSpeed(promptLower),
      difficulty: detectDifficulty(promptLower),
      obstacles: detectObstacles(promptLower, themeAnalysis.type)
    }
  };

  console.log(`✅ Analyzed prompt: ${worldData.theme} theme, ${worldData.params.difficulty} difficulty`);
  return worldData;
}

/**
 * Generate world name from prompt
 * Extracted from: generate_world_name() in TTG_MAIN_SERVER.py
 */
function generateWorldName(prompt, theme) {
  const words = prompt.split(/\s+/).slice(0, 4);
  const nameWords = words
    .filter(word => /^[a-zA-Z]+$/.test(word))
    .map(word => word.charAt(0).toUpperCase() + word.slice(1));

  if (nameWords.length > 0) {
    return nameWords.join(' ');
  }

  const themeNames = {
    'runner': 'Endless Runner',
    'side_scroller': 'Platform Adventure',
    'alien': 'Alien World',
    'horror': 'Dark Realm',
    'medieval': 'Ancient Kingdom',
    'fantasy': 'Magical Forest'
  };

  return themeNames[theme] || 'Generated World';
}

module.exports = {
  analyzeTheme,
  detectSpeed,
  detectDifficulty,
  detectObstacles,
  analyzePromptIntelligently,
  generateWorldName
};
