const { validateTemplate } = require('./game-templates/templateValidator');
const fs = require('fs');
const path = require('path');

console.log('=== TESTING TEMPLATE VALIDATOR ===\n');

const templatesDir = path.join(__dirname, 'game-templates', 'templates');
const templateFiles = ['runner_template.json', 'platformer_template.json', 'arena_template.json'];

templateFiles.forEach(file => {
  console.log(`Validating: ${file}`);
  const templatePath = path.join(templatesDir, file);
  const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));
  
  const result = validateTemplate(template);
  
  if (result.valid) {
    console.log('✅ Valid');
    console.log(`   - template_id: ${template.template_id}`);
    console.log(`   - entities: ${template.entities.length}`);
    console.log(`   - jobs: ${template.jobs.join(', ')}`);
  } else {
    console.log('❌ Invalid');
    result.errors.forEach(err => console.log(`   - ${err}`));
  }
  console.log('');
});

// Test invalid template
console.log('Testing invalid template:');
const invalidTemplate = {
  template_id: 'test',
  entities: ['player']
  // Missing components and jobs
};

const invalidResult = validateTemplate(invalidTemplate);
console.log(invalidResult.valid ? '❌ Should be invalid' : '✅ Correctly rejected');
invalidResult.errors.forEach(err => console.log(`   - ${err}`));

console.log('\n✅ Validator test completed!');
