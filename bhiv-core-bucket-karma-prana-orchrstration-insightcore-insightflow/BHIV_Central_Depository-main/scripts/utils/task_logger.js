/**
 * Task Logger Module
 * Reusable logging system for AIM and PROGRESS notes
 *
 * Features:
 * - JSONL format logging to ./logs/task_manager.log
 * - AIM and PROGRESS note types
 * - Error handling with retries
 * - Input validation
 * - File creation and append mode
 */

const fs = require('fs').promises;
const path = require('path');
const winston = require('winston');

// Constants
const LOG_FILE_PATH = './logs/task_manager.log';
const MAX_RETRIES = 2;
const RETRY_DELAY = 100; // ms

// Ensure logs directory exists
async function ensureLogDirectory() {
  const logDir = path.dirname(LOG_FILE_PATH);
  try {
    await fs.access(logDir);
  } catch {
    await fs.mkdir(logDir, { recursive: true });
  }
}

// Winston logger for internal logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

/**
 * Validates AIM note input
 * @param {string} aimNote - The AIM note to validate
 * @throws {Error} If validation fails
 */
function validateAimNote(aimNote) {
  if (typeof aimNote !== 'string') {
    throw new Error('AIM note must be a string');
  }
  if (aimNote.trim().length === 0) {
    throw new Error('AIM note cannot be empty');
  }
  if (aimNote.length > 1000) {
    throw new Error('AIM note cannot exceed 1000 characters');
  }
}

/**
 * Validates PROGRESS details input
 * @param {Object} progressDetails - The progress details to validate
 * @throws {Error} If validation fails
 */
function validateProgressDetails(progressDetails) {
  if (!progressDetails || typeof progressDetails !== 'object') {
    throw new Error('Progress details must be an object');
  }

  const requiredKeys = ['done', 'failed', 'grateful'];
  for (const key of requiredKeys) {
    if (!(key in progressDetails)) {
      throw new Error(`Progress details missing required key: ${key}`);
    }
  }

  // Validate array types
  if (!Array.isArray(progressDetails.done)) {
    throw new Error('Progress details "done" must be an array');
  }
  if (!Array.isArray(progressDetails.failed)) {
    throw new Error('Progress details "failed" must be an array');
  }

  // Validate string type for grateful
  if (typeof progressDetails.grateful !== 'string') {
    throw new Error('Progress details "grateful" must be a string');
  }

  // Validate array contents are strings
  const validateStringArray = (arr, fieldName) => {
    for (const item of arr) {
      if (typeof item !== 'string') {
        throw new Error(`Progress details "${fieldName}" array must contain only strings`);
      }
    }
  };

  validateStringArray(progressDetails.done, 'done');
  validateStringArray(progressDetails.failed, 'failed');
}

/**
 * Writes a log entry to the file with retry logic
 * @param {Object} logEntry - The log entry to write
 * @returns {Promise<void>}
 */
async function writeLogEntry(logEntry) {
  let lastError;

  for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
    try {
      await ensureLogDirectory();

      const logLine = JSON.stringify(logEntry) + '\n';

      // Use append mode with exclusive flag to prevent conflicts
      await fs.appendFile(LOG_FILE_PATH, logLine, { flag: 'a' });

      logger.debug(`Log entry written successfully (attempt ${attempt})`);
      return;

    } catch (error) {
      lastError = error;
      logger.warn(`Log write attempt ${attempt} failed: ${error.message}`);

      if (attempt <= MAX_RETRIES) {
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * attempt));
      }
    }
  }

  // If all retries failed, log to stderr and throw
  const errorMsg = `Failed to write log entry after ${MAX_RETRIES + 1} attempts: ${lastError.message}`;
  console.error(errorMsg);
  throw new Error(errorMsg);
}

/**
 * Logs an AIM note at the start of a day
 * @param {string} aimNote - The AIM note for the day
 * @param {number} dayNumber - The day number
 * @returns {Promise<void>}
 */
async function startDay(aimNote, dayNumber) {
  try {
    // Validate inputs
    validateAimNote(aimNote);

    if (typeof dayNumber !== 'number' || dayNumber < 1) {
      throw new Error('Day number must be a positive number');
    }

    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'AIM',
      day: dayNumber,
      note: aimNote.trim()
    };

    await writeLogEntry(logEntry);
    logger.info(`AIM logged for Day ${dayNumber}: ${aimNote.substring(0, 50)}...`);

  } catch (error) {
    logger.error(`Failed to log AIM: ${error.message}`);
    console.error(`AIM logging failed: ${error.message}`);
    throw error; // Re-throw to allow caller to handle
  }
}

/**
 * Logs a PROGRESS note at the end of a day
 * @param {Object} progressDetails - Progress details object
 * @param {string[]} progressDetails.done - Array of completed tasks
 * @param {string[]} progressDetails.failed - Array of failed tasks
 * @param {string} progressDetails.grateful - Gratitude note
 * @param {number} [dayNumber] - Optional day number override
 * @returns {Promise<void>}
 */
async function endDay(progressDetails, dayNumber = null) {
  try {
    // Validate inputs
    validateProgressDetails(progressDetails);

    // If no day number provided, try to infer from recent AIM logs
    if (dayNumber === null) {
      dayNumber = await getCurrentDayNumber();
    }

    if (typeof dayNumber !== 'number' || dayNumber < 1) {
      throw new Error('Day number must be a positive number');
    }

    const logEntry = {
      timestamp: new Date().toISOString(),
      type: 'PROGRESS',
      day: dayNumber,
      note: {
        done: progressDetails.done,
        failed: progressDetails.failed,
        grateful: progressDetails.grateful.trim()
      }
    };

    await writeLogEntry(logEntry);

    const completedCount = progressDetails.done.length;
    const failedCount = progressDetails.failed.length;
    logger.info(`PROGRESS logged for Day ${dayNumber}: ${completedCount} done, ${failedCount} failed`);

  } catch (error) {
    logger.error(`Failed to log PROGRESS: ${error.message}`);
    console.error(`PROGRESS logging failed: ${error.message}`);
    throw error; // Re-throw to allow caller to handle
  }
}

/**
 * Attempts to get the current day number from recent AIM logs
 * @returns {Promise<number>} The current day number
 */
async function getCurrentDayNumber() {
  try {
    const logContent = await fs.readFile(LOG_FILE_PATH, 'utf8');
    const lines = logContent.trim().split('\n').filter(line => line.trim());

    // Parse lines in reverse order to find the most recent AIM
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const entry = JSON.parse(lines[i]);
        if (entry.type === 'AIM') {
          return entry.day;
        }
      } catch {
        // Skip malformed lines
        continue;
      }
    }
  } catch {
    // If file doesn't exist or can't be read, default to day 1
  }

  return 1; // Default fallback
}

/**
 * Reads and parses the log file
 * @returns {Promise<Array>} Array of parsed log entries
 */
async function readLogs() {
  try {
    const logContent = await fs.readFile(LOG_FILE_PATH, 'utf8');
    const lines = logContent.trim().split('\n').filter(line => line.trim());

    return lines.map(line => {
      try {
        return JSON.parse(line);
      } catch (error) {
        logger.warn(`Failed to parse log line: ${error.message}`);
        return null;
      }
    }).filter(entry => entry !== null);

  } catch (error) {
    logger.error(`Failed to read logs: ${error.message}`);
    return [];
  }
}

/**
 * Generates a summary report for a specific day
 * @param {number} dayNumber - The day number to summarize
 * @returns {Promise<Object>} Summary object
 */
async function generateDaySummary(dayNumber) {
  try {
    const logs = await readLogs();
    const dayLogs = logs.filter(entry => entry.day === dayNumber);

    const aimEntry = dayLogs.find(entry => entry.type === 'AIM');
    const progressEntry = dayLogs.find(entry => entry.type === 'PROGRESS');

    return {
      day: dayNumber,
      aim: aimEntry ? aimEntry.note : null,
      progress: progressEntry ? progressEntry.note : null,
      logCount: dayLogs.length,
      dateRange: dayLogs.length > 0 ? {
        start: dayLogs[0].timestamp,
        end: dayLogs[dayLogs.length - 1].timestamp
      } : null
    };

  } catch (error) {
    logger.error(`Failed to generate day summary: ${error.message}`);
    return { day: dayNumber, error: error.message };
  }
}

module.exports = {
  startDay,
  endDay,
  readLogs,
  generateDaySummary,
  getCurrentDayNumber
};