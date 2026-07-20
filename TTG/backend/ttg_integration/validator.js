/**
 * TTG Input Validator
 * Comprehensive validation for text-to-game inputs
 */

function validateTTGInput(text) {
  const MAX_TEXT_LENGTH = 500;
  const MIN_TEXT_LENGTH = 3;
  const ALLOWED_CHARS = /^[a-zA-Z0-9\s,.'"\-!?]+$/;
  
  // Type check
  if (!text || typeof text !== 'string') {
    return { valid: false, error: 'Text input is required and must be a string' };
  }

  const trimmedText = text.trim();

  // Empty check
  if (!trimmedText) {
    return { valid: false, error: 'Text input cannot be empty' };
  }

  // Min length
  if (trimmedText.length < MIN_TEXT_LENGTH) {
    return { valid: false, error: `Text too short (min ${MIN_TEXT_LENGTH} characters)` };
  }

  // Max length
  if (trimmedText.length > MAX_TEXT_LENGTH) {
    return { valid: false, error: `Text too long (max ${MAX_TEXT_LENGTH} characters)` };
  }

  // Character whitelist
  if (!ALLOWED_CHARS.test(trimmedText)) {
    return { valid: false, error: 'Text contains invalid characters. Only letters, numbers, spaces, and basic punctuation allowed' };
  }

  // Reserved words
  const reservedWords = ['null', 'undefined', 'nan', 'infinity'];
  if (reservedWords.includes(trimmedText.toLowerCase())) {
    return { valid: false, error: 'Invalid input: reserved word' };
  }

  // Must contain alphanumeric
  const hasAlphanumeric = /[a-zA-Z0-9]/.test(trimmedText);
  if (!hasAlphanumeric) {
    return { valid: false, error: 'Text must contain at least one letter or number' };
  }

  // Check for HTML/script tags
  if (/<[^>]*>/g.test(trimmedText)) {
    return { valid: false, error: 'HTML tags are not allowed' };
  }

  // Check for JSON-like input
  if ((trimmedText.startsWith('{') && trimmedText.endsWith('}')) || 
      (trimmedText.startsWith('[') && trimmedText.endsWith(']'))) {
    return { valid: false, error: 'JSON input is not allowed' };
  }

  return { valid: true, sanitized: trimmedText };
}

module.exports = { validateTTGInput };
