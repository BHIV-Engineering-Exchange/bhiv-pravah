
const fs = require('fs');
const path = require('path');

const TELEMETRY_PATH = path.join(process.cwd(), 'telemetry_samples.json');
const BACKUP_PATH = path.join(process.cwd(), 'telemetry_samples.backup.json');

console.log('=== TELEMETRY MIGRATION ===\n');

if (!fs.existsSync(TELEMETRY_PATH)) {
  console.log('No telemetry file found. Nothing to migrate.\n');
  process.exit(0);
}

// Backup existing file
console.log('Creating backup...');
fs.copyFileSync(TELEMETRY_PATH, BACKUP_PATH);
console.log(`✅ Backup created: ${BACKUP_PATH}\n`);

// Load and analyze
try {
  const lines = fs.readFileSync(TELEMETRY_PATH, 'utf-8').split('\n').filter(Boolean);
  const events = lines.map(line => JSON.parse(line));

  console.log(`Total events: ${events.length}`);
  const withSeq = events.filter(e => e.seq !== undefined).length;
  const withoutSeq = events.length - withSeq;
  console.log(`  With seq: ${withSeq}`);
  console.log(`  Without seq (legacy): ${withoutSeq}\n`);
} catch (err) {
  console.error('Failed to read or parse telemetry file:', err.message);
  console.log('Migration aborted.\n');
  process.exit(1);
}

// Clear and start fresh
console.log('Clearing telemetry log...');
fs.unlinkSync(TELEMETRY_PATH);
console.log('✅ Telemetry log cleared\n');

console.log('=== MIGRATION COMPLETE ===');
console.log('New telemetry events will use proper seq numbering.');
console.log(`Legacy backup available at: ${BACKUP_PATH}\n`);
