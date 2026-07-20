const fs = require('fs');
const path = require('path');

const TEMPLATES_DIR = path.join(__dirname, 'templates');

const TEMPLATE_MAP = {
  runner: 'runner_template.json',
  platformer: 'platformer_template.json',
  arena: 'arena_template.json'
};

function selectTemplate(intent) {
  const intentLower = intent.toLowerCase();
  
  // Match keywords to templates
  if (intentLower.includes('runner') || intentLower.includes('run') || intentLower.includes('obstacle')) {
    return loadTemplate('runner');
  }
  
  if (intentLower.includes('platformer') || intentLower.includes('platform') || intentLower.includes('jump')) {
    return loadTemplate('platformer');
  }
  
  if (intentLower.includes('arena') || intentLower.includes('survival') || intentLower.includes('combat') || intentLower.includes('enemy')) {
    return loadTemplate('arena');
  }
  
  // Default fallback
  return loadTemplate('runner');
}

function loadTemplate(templateKey) {
  const filename = TEMPLATE_MAP[templateKey];
  if (!filename) {
    throw new Error(`Unknown template: ${templateKey}`);
  }
  
  const templatePath = path.join(TEMPLATES_DIR, filename);
  const templateData = fs.readFileSync(templatePath, 'utf8');
  return JSON.parse(templateData);
}

module.exports = { selectTemplate };
