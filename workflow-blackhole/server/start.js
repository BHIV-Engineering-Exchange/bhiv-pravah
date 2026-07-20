// Polyfill for SlowBuffer removed in Node.js v25
if (!Buffer.SlowBuffer) {
  Buffer.SlowBuffer = Buffer;
  Buffer.SlowBuffer.prototype.equal = Buffer.prototype.equals;
}

// Now require the main application
require('./index.js');
