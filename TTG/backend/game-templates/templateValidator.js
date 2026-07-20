const fs = require('fs');
const path = require('path');

const REQUIRED_FIELDS = ['template_id', 'entities', 'components', 'jobs'];

// Load engine capabilities
let ENGINE_CAPABILITIES = null;
try {
  const capabilitiesPath = path.join(__dirname, 'engineCapabilities.json');
  ENGINE_CAPABILITIES = JSON.parse(fs.readFileSync(capabilitiesPath, 'utf8'));
} catch (err) {
  console.warn('[VALIDATOR] Could not load engine capabilities:', err.message);
  ENGINE_CAPABILITIES = {
    entities: [],
    components: [],
    jobs: []
  };
}

function validateTemplate(template) {
  const errors = [];
  
  // Check required fields
  REQUIRED_FIELDS.forEach(field => {
    if (!template[field]) {
      errors.push(`Missing required field: ${field}`);
    }
  });
  
  // Validate template_id format
  if (template.template_id && typeof template.template_id !== 'string') {
    errors.push('template_id must be a string');
  }
  
  // Validate entities is array
  if (template.entities && !Array.isArray(template.entities)) {
    errors.push('entities must be an array');
  }
  
  // Validate components is object
  if (template.components && typeof template.components !== 'object') {
    errors.push('components must be an object');
  }
  
  // Validate jobs is array
  if (template.jobs && !Array.isArray(template.jobs)) {
    errors.push('jobs must be an array');
  }
  
  // Validate job types are supported by engine
  if (template.jobs && Array.isArray(template.jobs) && ENGINE_CAPABILITIES) {
    template.jobs.forEach(job => {
      if (!ENGINE_CAPABILITIES.jobs.includes(job)) {
        errors.push(`Unsupported job type: ${job} (not in engine capabilities)`);
      }
    });
  }
  
  // Validate entities are supported by engine
  if (template.entities && Array.isArray(template.entities) && ENGINE_CAPABILITIES) {
    template.entities.forEach(entity => {
      if (!ENGINE_CAPABILITIES.entities.includes(entity)) {
        errors.push(`Unsupported entity type: ${entity} (not in engine capabilities)`);
      }
    });
  }
  
  // Validate components are supported by engine
  if (template.components && typeof template.components === 'object' && ENGINE_CAPABILITIES) {
    Object.values(template.components).forEach(componentList => {
      if (Array.isArray(componentList)) {
        componentList.forEach(component => {
          if (!ENGINE_CAPABILITIES.components.includes(component)) {
            errors.push(`Unsupported component: ${component} (not in engine capabilities)`);
          }
        });
      }
    });
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

function validateAllTemplates(templates) {
  const results = {};
  
  Object.keys(templates).forEach(key => {
    results[key] = validateTemplate(templates[key]);
  });
  
  return results;
}

function getEngineCapabilities() {
  return ENGINE_CAPABILITIES;
}

module.exports = { validateTemplate, validateAllTemplates, getEngineCapabilities };
