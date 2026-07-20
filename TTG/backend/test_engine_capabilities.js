const { validateTemplate, getEngineCapabilities } = require('./game-templates/templateValidator');
const fs = require('fs');
const path = require('path');

console.log('=== TESTING ENGINE CAPABILITY VALIDATION ===\n');

// Show engine capabilities
const capabilities = getEngineCapabilities();
console.log('Engine Capabilities:');
console.log('  Entities:', capabilities.entities.join(', '));
console.log('  Components:', capabilities.components.join(', '));
console.log('  Jobs:', capabilities.jobs.join(', '));
console.log('\n---\n');

// Test valid templates
const templatesDir = path.join(__dirname, 'game-templates', 'templates');
const templateFiles = ['runner_template.json', 'platformer_template.json', 'arena_template.json'];

console.log('Testing Valid Templates:\n');
templateFiles.forEach(file => {
  const templatePath = path.join(templatesDir, file);
  const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));
  const result = validateTemplate(template);
  
  console.log(`${file}: ${result.valid ? '✅ Valid' : '❌ Invalid'}`);
  if (!result.valid) {
    result.errors.forEach(err => console.log(`  - ${err}`));
  }
});

console.log('\n---\n');

// Test template with unsupported capabilities
console.log('Testing Template with Unsupported Capabilities:\n');
const invalidTemplate = {
  template_id: 'invalid_v1',
  entities: ['player', 'dragon', 'alien'],  // dragon and alien not supported
  components: {
    player: ['super_power', 'collider'],  // super_power not supported
    dragon: ['fire_breath']  // fire_breath not supported
  },
  jobs: ['BUILD_SCENE', 'SPAWN_DRAGON', 'TELEPORT']  // SPAWN_DRAGON and TELEPORT not supported
};

const invalidResult = validateTemplate(invalidTemplate);
console.log(invalidResult.valid ? '❌ Should be invalid' : '✅ Correctly rejected');
console.log('\nErrors found:');
invalidResult.errors.forEach(err => console.log(`  - ${err}`));

console.log('\n✅ Engine capability validation test completed!');
