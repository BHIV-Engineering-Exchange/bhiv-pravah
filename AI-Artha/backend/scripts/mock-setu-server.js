/**
 * MOCK SETU SERVER
 * 
 * Simulates a real SETU GST Network gateway for proof validation.
 * Accepts HTTP POST requests, validates payload, returns realistic response.
 * 
 * Usage: node scripts/mock-setu-server.js
 * Default: http://localhost:9876
 */

import http from 'http';
import { randomUUID } from 'crypto';

const PORT = process.env.SETU_MOCK_PORT || 9876;

const server = http.createServer((req, res) => {
  let body = '';

  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    const timestamp = new Date().toISOString();
    const requestId = randomUUID();

    console.log(`\n[${timestamp}] RECEIVED ${req.method} ${req.url}`);
    console.log(`  Request-ID: ${requestId}`);
    console.log(`  Content-Type: ${req.headers['content-type']}`);
    console.log(`  Authorization: ${req.headers['authorization'] ? 'Bearer ***' : 'MISSING'}`);

    try {
      const payload = JSON.parse(body);

      // Validate required fields
      const errors = [];
      if (!payload.signal_id) errors.push('signal_id is required');
      if (!payload.trace_id) errors.push('trace_id is required');
      if (!payload.signal_type) errors.push('signal_type is required');

      if (errors.length > 0) {
        console.log(`  ❌ VALIDATION FAILED: ${errors.join(', ')}`);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'REJECTED',
          request_id: requestId,
          errors,
          timestamp,
        }));
        return;
      }

      // Simulate processing delay
      const processingTime = Math.floor(Math.random() * 100) + 50;
      
      // Success response
      const response = {
        status: 'ACCEPTED',
        request_id: requestId,
        setu_reference: `SETU-${Date.now()}-${randomUUID().slice(0, 8)}`,
        signal_id: payload.signal_id,
        trace_id: payload.trace_id,
        filing_type: payload.filing_type || 'UNKNOWN',
        processing_time_ms: processingTime,
        timestamp,
        gateway: 'MOCK_SETU_v1.0',
      };

      console.log(`  ✅ ACCEPTED — SETU reference: ${response.setu_reference}`);
      console.log(`  Processing time: ${processingTime}ms`);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(response, null, 2));

    } catch (e) {
      console.log(`  ❌ PARSE ERROR: ${e.message}`);
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'REJECTED',
        request_id: requestId,
        errors: ['Invalid JSON payload'],
        timestamp,
      }));
    }
  });
});

server.listen(PORT, () => {
  console.log(`\n═══════════════════════════════════════════════════════`);
  console.log(`  MOCK SETU SERVER RUNNING`);
  console.log(`  URL: http://localhost:${PORT}`);
  console.log(`  Ready to accept dispatch requests`);
  console.log(`═══════════════════════════════════════════════════════\n`);
});
