# Task Logger Module

A reusable Node.js module for structured AIM and PROGRESS logging as per team mandatory requirements. Designed for project management automation and progress tracking.

## 🚀 Features

- **Structured Logging**: AIM and PROGRESS notes in JSONL format
- **File Management**: Automatic log directory creation and append mode
- **Error Resilience**: Retry logic with comprehensive error handling
- **Input Validation**: Strict validation of AIM notes and PROGRESS details
- **Winston Integration**: Professional logging with console and file outputs
- **Day Tracking**: Automatic day number inference and summary generation

## 📦 Installation

```bash
npm install
# Dependencies: winston@^3.11.0
```

## 🛠️ Usage

### Basic Usage

```javascript
const { startDay, endDay } = require('./task_logger');

// Start of day - log AIM
await startDay('Setting up database schema and security policies', 1);

// End of day - log PROGRESS
await endDay({
  done: ['table_creation', 'rls_policies', 'test_queries'],
  failed: [],
  grateful: 'Successfully automated the entire setup process'
});
```

### Advanced Usage

```javascript
const { startDay, endDay, generateDaySummary, readLogs } = require('./task_logger');

// Log AIM for current day
await startDay('Implementing user authentication and authorization', 2);

// Log PROGRESS (day number auto-inferred from recent AIM)
await endDay({
  done: ['auth_setup', 'user_management'],
  failed: ['email_integration'],
  grateful: 'Learned valuable lessons about auth best practices'
});

// Generate summary
const summary = await generateDaySummary(2);
console.log('Day 2 Summary:', summary);

// Read all logs
const allLogs = await readLogs();
console.log('Total log entries:', allLogs.length);
```

## 📁 File Structure

```
./logs/
└── task_manager.log    # JSONL format log file
```

**Log Entry Format:**
```json
{"timestamp":"2025-01-15T10:30:00.000Z","type":"AIM","day":1,"note":"Starting database setup"}
{"timestamp":"2025-01-15T11:45:00.000Z","type":"PROGRESS","day":1,"note":{"done":["setup_complete"],"failed":[],"grateful":"Great progress made"}}
```

## 🔧 API Reference

### `startDay(aimNote, dayNumber)`

Logs an AIM note at the start of a work day.

**Parameters:**
- `aimNote` (string): Non-empty string describing the day's objectives
- `dayNumber` (number): Positive integer representing the day number

**Throws:**
- `Error` if aimNote is invalid (empty, not string, too long)
- `Error` if dayNumber is invalid

### `endDay(progressDetails[, dayNumber])`

Logs a PROGRESS note at the end of a work day.

**Parameters:**
- `progressDetails` (object): Progress summary with required keys
  - `done` (string[]): Array of completed tasks
  - `failed` (string[]): Array of failed tasks
  - `grateful` (string): Gratitude/reflection note
- `dayNumber` (number, optional): Day number (auto-inferred if not provided)

**Throws:**
- `Error` if progressDetails structure is invalid

### `generateDaySummary(dayNumber)`

Generates a summary of all logs for a specific day.

**Parameters:**
- `dayNumber` (number): The day number to summarize

**Returns:**
- Object with day summary including AIM, PROGRESS, and metadata

### `readLogs()`

Reads and parses all log entries from the log file.

**Returns:**
- Array of parsed log entry objects

### `getCurrentDayNumber()`

Attempts to determine the current day number from recent AIM logs.

**Returns:**
- Number: Current day number (defaults to 1 if unable to determine)

## 🧪 Testing & Validation

### Run Sample Demo

```bash
npm run log-demo
```

This will:
1. Log an AIM note for Day 1
2. Log a PROGRESS note with sample data
3. Display a summary
4. Show integration examples

### Manual Testing

```bash
# Generate summary for Day 1
npm run log-summary

# Check log file
cat ./logs/task_manager.log
```

## 🔄 Integration Examples

### Integrating into Supabase Setup Script

```javascript
// In supabase_setup.js
const { startDay, endDay } = require('./task_logger');

async function main() {
  // Start logging
  await startDay('Setting up Supabase database with tables and security', 1);

  try {
    // Your existing setup code...

    // Track progress
    const progress = { done: [], failed: [], grateful: '' };

    // On success
    progress.done.push('database_setup_complete');

    // On failure
    progress.failed.push('connection_failed');

    // End of day
    progress.grateful = 'Successfully automated database setup with comprehensive error handling';
    await endDay(progress);

  } catch (error) {
    await endDay({
      done: [],
      failed: ['setup_failed'],
      grateful: 'Learned about error handling and retry mechanisms'
    });
    throw error;
  }
}
```

### Integrating into Any Node.js Script

```javascript
const { startDay, endDay } = require('./path/to/task_logger');

async function myTask() {
  await startDay('Implementing new feature X', 3);

  // Your task logic here...

  await endDay({
    done: ['feature_implemented', 'tests_passed'],
    failed: ['documentation_pending'],
    grateful: 'Excited about the new capabilities added'
  });
}
```

## 🚨 Error Handling

### Automatic Retries
- **Max Retries**: 2 additional attempts after initial failure
- **Retry Delay**: Progressive delay (100ms, 200ms)
- **Failure Logging**: All failures logged to stderr
- **Non-blocking**: Errors don't crash the application

### Input Validation
- **AIM Notes**: Must be non-empty string, max 1000 characters
- **PROGRESS Details**: Must have `done`, `failed`, `grateful` keys
- **Arrays**: Must contain only strings
- **Day Numbers**: Must be positive integers

### File System Errors
- **Directory Creation**: Automatic `./logs/` directory creation
- **File Access**: Handles permission issues and missing files
- **Concurrent Access**: Append mode prevents data corruption

## 📊 Log Analysis

### Parsing Logs

```javascript
const { readLogs } = require('./task_logger');

// Get all logs
const logs = await readLogs();

// Filter by type
const aimLogs = logs.filter(log => log.type === 'AIM');
const progressLogs = logs.filter(log => log.type === 'PROGRESS');

// Group by day
const logsByDay = logs.reduce((acc, log) => {
  if (!acc[log.day]) acc[log.day] = [];
  acc[log.day].push(log);
  return acc;
}, {});
```

### Generating Reports

```javascript
const { generateDaySummary } = require('./task_logger');

// Get summary for each day
for (let day = 1; day <= 7; day++) {
  const summary = await generateDaySummary(day);
  if (summary.aim) {
    console.log(`Day ${day}: ${summary.aim}`);
    console.log(`Completed: ${summary.progress?.done?.length || 0} tasks`);
  }
}
```

## 🔗 Integration with Lead Reports

### For Anmol's Report Compilation

The logs are designed to be easily parsed for generating `/reports/lead_log.txt`:

```javascript
const { readLogs } = require('./task_logger');
const fs = require('fs').promises;

async function generateLeadReport() {
  const logs = await readLogs();

  let report = '# Team Progress Report\n\n';

  // Group by day
  const days = {};
  logs.forEach(log => {
    if (!days[log.day]) days[log.day] = { aim: null, progress: null };
    if (log.type === 'AIM') days[log.day].aim = log;
    if (log.type === 'PROGRESS') days[log.day].progress = log;
  });

  // Generate report
  Object.keys(days).sort().forEach(day => {
    const { aim, progress } = days[day];

    report += `## Day ${day}\n\n`;

    if (aim) {
      report += `**AIM:** ${aim.note}\n\n`;
    }

    if (progress) {
      report += `**DONE:**\n`;
      progress.note.done.forEach(item => report += `- ${item}\n`);

      if (progress.note.failed.length > 0) {
        report += `\n**FAILED:**\n`;
        progress.note.failed.forEach(item => report += `- ${item}\n`);
      }

      report += `\n**GRATEFUL:** ${progress.note.grateful}\n\n`;
    }
  });

  await fs.writeFile('./reports/lead_log.txt', report);
  console.log('Lead report generated: ./reports/lead_log.txt');
}

generateLeadReport();
```

## 📋 Best Practices

### Logging Guidelines
1. **AIM Notes**: Be specific about daily objectives
2. **PROGRESS Tracking**: Update `done` array as tasks complete
3. **Failure Logging**: Document what failed and why
4. **Gratitude Notes**: Include learnings and reflections

### Error Handling
1. **Wrap in try-catch**: Always handle logging errors gracefully
2. **Validate Input**: Check data before calling logging functions
3. **Monitor Logs**: Regularly review log files for issues

### Performance
1. **Batch Operations**: Log multiple completions together
2. **Async Handling**: Use await for all logging operations
3. **File Rotation**: Consider log rotation for long-term use

## 🔧 Troubleshooting

### Common Issues

**"Log directory creation failed"**
- Check write permissions in project directory
- Ensure parent directory exists

**"Invalid AIM note"**
- Ensure aimNote is a non-empty string
- Check for special characters or encoding issues

**"PROGRESS details missing required key"**
- Verify progressDetails object has `done`, `failed`, `grateful` keys
- Ensure arrays contain only strings

**"Log write failed after retries"**
- Check disk space
- Verify file system permissions
- Check for concurrent file access issues

### Debug Mode

Enable debug logging:
```javascript
process.env.DEBUG = 'task-logger';
```

## 📈 Monitoring & Analytics

### Log Statistics

```javascript
const { readLogs } = require('./task_logger');

async function generateStats() {
  const logs = await readLogs();

  const stats = {
    totalLogs: logs.length,
    aimLogs: logs.filter(l => l.type === 'AIM').length,
    progressLogs: logs.filter(l => l.type === 'PROGRESS').length,
    daysCovered: new Set(logs.map(l => l.day)).size,
    dateRange: {
      start: logs[0]?.timestamp,
      end: logs[logs.length - 1]?.timestamp
    }
  };

  console.log('Log Statistics:', stats);
  return stats;
}
```

## 🎯 Next Steps

1. **Integrate into existing scripts** by adding AIM/PROGRESS logging
2. **Set up automated report generation** for lead reviews
3. **Add log rotation** for long-term maintenance
4. **Create dashboard** for visualizing progress over time
5. **Add alerting** for failed tasks or missed deadlines

---

**Ready to start logging your project progress? Run `npm run log-demo` to see it in action!** 🚀