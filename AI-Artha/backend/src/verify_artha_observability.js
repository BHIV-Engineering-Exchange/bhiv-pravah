import tantraService from './services/tantra.service.js';
import { randomUUID } from 'crypto';

async function test() {
  console.log("Triggering transaction event via reportTransactionLifecycle...");
  const traceId = `trace-${randomUUID()}`;
  
  await tantraService.reportTransactionLifecycle(
    traceId,
    'INVOICE_CREATED',
    'SUCCESS',
    { durationMs: 150, customerId: 'cust-123', invoiceAmount: 5000 }
  );
  
  console.log("Successfully triggered telemetry for trace:", traceId);
  
  // Wait to allow background network requests to complete
  await new Promise(resolve => setTimeout(resolve, 3000));
  process.exit(0);
}

test().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
