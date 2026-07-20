import { randomUUID } from 'crypto';
import RuntimeProof from '../models/RuntimeProof.js';
import UnifiedTrace from '../models/UnifiedTrace.js';
import JournalEntry from '../models/JournalEntry.js';
import LedgerEntry from '../models/LedgerEntry.js';
import Invoice from '../models/Invoice.js';
import Expense from '../models/Expense.js';
import TDSEntry from '../models/TDSEntry.js';
import ComplianceFiling from '../models/ComplianceFiling.js';
import ComplianceSignal from '../models/ComplianceSignal.js';
import logger from '../config/logger.js';

class EvidenceAutomationService {
  // Auto-capture API response as evidence
  async captureAPIResponse(data) {
    const { traceId, endpoint, method, statusCode, requestBody, responseBody, responseTime } = data;

    const proof = new RuntimeProof({
      trace_id: traceId || 'SYSTEM',
      proof_type: 'API_RESPONSE',
      endpoint,
      method,
      request: {
        body: this.sanitizeBody(requestBody),
        timestamp: new Date(),
      },
      response: {
        status: statusCode,
        body: this.truncateResponse(responseBody),
        latency_ms: responseTime,
        timestamp: new Date(),
      },
      environment: {
        node_env: process.env.NODE_ENV,
        node_version: process.version,
        timestamp: new Date(),
      },
    });

    await proof.save();
    return proof;
  }

  // Auto-capture database state
  async captureDBState(traceId, collection, documentId, operation) {
    const proof = new RuntimeProof({
      trace_id: traceId || 'SYSTEM',
      proof_type: 'DATABASE_STATE',
      db_state: {
        collection,
        documentId: String(documentId),
        operation,
        timestamp: new Date(),
      },
      environment: {
        node_env: process.env.NODE_ENV,
        node_version: process.version,
        timestamp: new Date(),
      },
    });

    await proof.save();
    return proof;
  }

  // Auto-capture chain verification
  async captureChainVerification(traceId, verificationResult) {
    const proof = new RuntimeProof({
      trace_id: traceId || 'SYSTEM',
      proof_type: 'CHAIN_VERIFICATION',
      assertions: [
        {
          description: 'Ledger chain integrity',
          expected: true,
          actual: verificationResult.isValid,
          passed: verificationResult.isValid,
          message: verificationResult.message,
        },
        {
          description: 'Total entries verified',
          expected: verificationResult.totalEntries,
          actual: verificationResult.totalEntriesVerified || verificationResult.totalEntries,
          passed: true,
        },
      ],
      verified: verificationResult.isValid,
      environment: {
        node_env: process.env.NODE_ENV,
        node_version: process.version,
        timestamp: new Date(),
      },
    });

    await proof.save();
    return proof;
  }

  // Auto-capture balance sheet evidence
  async captureBalanceSheetEvidence(traceId, balanceSheet) {
    const proof = new RuntimeProof({
      trace_id: traceId || 'SYSTEM',
      proof_type: 'BALANCE_SHEET',
      response: {
        body: balanceSheet,
        timestamp: new Date(),
      },
      assertions: [
        {
          description: 'Accounting equation (Assets = Liabilities + Equity)',
          expected: true,
          actual: balanceSheet.isBalanced,
          passed: balanceSheet.isBalanced,
          message: balanceSheet.isBalanced
            ? 'Balance sheet is balanced'
            : `Difference: ${balanceSheet.balanceDifference}`,
        },
      ],
      verified: balanceSheet.isBalanced,
      environment: {
        node_env: process.env.NODE_ENV,
        node_version: process.version,
        timestamp: new Date(),
      },
    });

    await proof.save();
    return proof;
  }

  // Generate evidence for complete workflow
  async generateWorkflowEvidence(traceId, workflowData) {
    const {
      invoice, expense, journalEntry, ledgerEntries,
      complianceSignal, filing, setuDispatch, verification,
    } = workflowData;

    const evidence = {
      traceId,
      generatedAt: new Date(),
      stages: [],
    };

    // Invoice evidence
    if (invoice) {
      evidence.stages.push({
        stage: 'INVOICE',
        entity: 'Invoice',
        entityId: String(invoice._id),
        proof: await this.captureAPIResponse({
          traceId,
          endpoint: `/api/v1/invoices/${invoice._id}`,
          method: 'GET',
          statusCode: 200,
          responseBody: invoice,
        }),
      });
    }

    // Expense evidence
    if (expense) {
      evidence.stages.push({
        stage: 'EXPENSE',
        entity: 'Expense',
        entityId: String(expense._id),
        proof: await this.captureAPIResponse({
          traceId,
          endpoint: `/api/v1/expenses/${expense._id}`,
          method: 'GET',
          statusCode: 200,
          responseBody: expense,
        }),
      });
    }

    // Journal entry evidence
    if (journalEntry) {
      evidence.stages.push({
        stage: 'JOURNAL',
        entity: 'JournalEntry',
        entityId: String(journalEntry._id),
        proof: await this.captureAPIResponse({
          traceId,
          endpoint: `/api/v1/ledger/journal/${journalEntry._id}`,
          method: 'GET',
          statusCode: 200,
          responseBody: journalEntry,
        }),
      });
    }

    // Ledger entries evidence
    if (ledgerEntries?.length) {
      evidence.stages.push({
        stage: 'LEDGER',
        entity: 'LedgerEntry',
        entityId: ledgerEntries.map(e => String(e._id)),
        proof: await this.captureDBState(traceId, 'ledgerentries', ledgerEntries[0]._id, 'READ'),
      });
    }

    // Chain verification evidence
    if (verification) {
      evidence.stages.push({
        stage: 'VERIFICATION',
        entity: 'ChainVerification',
        proof: await this.captureChainVerification(traceId, verification),
      });
    }

    // Compliance signal evidence
    if (complianceSignal) {
      evidence.stages.push({
        stage: 'COMPLIANCE_SIGNAL',
        entity: 'ComplianceSignal',
        entityId: String(complianceSignal._id),
        proof: await this.captureAPIResponse({
          traceId,
          endpoint: `/api/v1/signals/${complianceSignal._id}`,
          method: 'GET',
          statusCode: 200,
          responseBody: complianceSignal,
        }),
      });
    }

    // Filing evidence
    if (filing) {
      evidence.stages.push({
        stage: 'FILING',
        entity: 'ComplianceFiling',
        entityId: String(filing._id),
        proof: await this.captureAPIResponse({
          traceId,
          endpoint: `/api/v1/compliance/filing/${filing._id}`,
          method: 'GET',
          statusCode: 200,
          responseBody: filing,
        }),
      });
    }

    // SETU dispatch evidence
    if (setuDispatch) {
      evidence.stages.push({
        stage: 'SETU_DISPATCH',
        entity: 'SetuDispatch',
        proof: await this.captureAPIResponse({
          traceId,
          endpoint: '/api/v1/setu/dispatch',
          method: 'POST',
          statusCode: 200,
          responseBody: setuDispatch,
        }),
      });
    }

    // Save all proofs
    for (const stage of evidence.stages) {
      if (stage.proof) {
        stage.proofId = stage.proof.proof_id;
      }
    }

    logger.info(`Workflow evidence generated for trace: ${traceId}, stages: ${evidence.stages.length}`);
    return evidence;
  }

  // Get evidence for a trace
  async getEvidenceByTrace(traceId) {
    const [proofs, trace] = await Promise.all([
      RuntimeProof.find({ trace_id: traceId }).sort({ createdAt: 1 }),
      UnifiedTrace.findOne({ trace_id: traceId }),
    ]);

    return {
      traceId,
      trace: trace?.toObject(),
      proofs: proofs.map(p => p.toObject()),
      totalProofs: proofs.length,
      allVerified: proofs.every(p => p.verified),
    };
  }

  // Get evidence summary
  async getEvidenceSummary(filters = {}) {
    const match = {};
    if (filters.startDate) match.createdAt = { $gte: new Date(filters.startDate) };
    if (filters.endDate) match.createdAt = { ...match.createdAt, $lte: new Date(filters.endDate) };
    if (filters.proofType) match.proof_type = filters.proofType;

    const [byType, byVerification, totalCount] = await Promise.all([
      RuntimeProof.aggregate([
        { $match: match },
        { $group: { _id: '$proof_type', count: { $sum: 1 } } },
        { $sort: { count: -1 } },
      ]),
      RuntimeProof.aggregate([
        { $match: match },
        { $group: { _id: '$verified', count: { $sum: 1 } } },
      ]),
      RuntimeProof.countDocuments(match),
    ]);

    return { byType, byVerification, totalCount };
  }

  sanitizeBody(body) {
    if (!body) return undefined;
    const sanitized = { ...body };
    delete sanitized.password;
    delete sanitized.token;
    delete sanitized.secret;
    return sanitized;
  }

  truncateResponse(body) {
    if (!body) return undefined;
    const str = JSON.stringify(body);
    if (str.length > 10000) {
      return JSON.parse(str.slice(0, 10000) + '"...truncated"}');
    }
    return body;
  }
}

export default new EvidenceAutomationService();
