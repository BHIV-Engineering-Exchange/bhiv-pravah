import express from 'express';
import mongoose from 'mongoose';
import { protect } from '../middleware/auth.js';
import { getRedisClient } from '../config/redis.js';
import { areTransactionsAvailable } from '../config/database.js';
import ComplianceSignal from '../models/ComplianceSignal.js';
import LedgerEntry from '../models/LedgerEntry.js';
import JournalEntry from '../models/JournalEntry.js';
import Invoice from '../models/Invoice.js';
import Expense from '../models/Expense.js';
import logger from '../config/logger.js';

const router = express.Router();

/**
 * GET /api/v1/runtime/status
 *
 * Operational proof surface.
 * Returns the full deterministic runtime state in one call.
 * Used by: incoming developers, integration layer, deployment verification.
 *
 * Auth: required (Bearer token). Non-sensitive data only — no keys or secrets.
 */
router.get('/status', protect, async (req, res) => {
  const t0 = Date.now();

  try {
    const dbState = mongoose.connection.readyState;

    // Redis
    let redisStatus = 'disabled';
    const redisClient = getRedisClient();
    if (redisClient) {
      try {
        const pong = await redisClient.ping();
        redisStatus = pong === 'PONG' ? 'connected' : 'error';
      } catch {
        redisStatus = 'error';
      }
    }

    // Counts — all in parallel, individual failures degrade gracefully
    const [
      totalSignals,
      totalLedgerEntries,
      totalPostedJournals,
      totalSentInvoices,
      totalRecordedExpenses,
    ] = await Promise.all([
      ComplianceSignal.countDocuments().catch(() => -1),
      LedgerEntry.countDocuments().catch(() => -1),
      JournalEntry.countDocuments({ status: { $in: ['POSTED', 'posted'] } }).catch(() => -1),
      Invoice.countDocuments({ status: { $in: ['sent', 'partial', 'paid'] } }).catch(() => -1),
      Expense.countDocuments({ status: 'recorded' }).catch(() => -1),
    ]);

    // Chain tip (last ledger entry hash)
    let chainTip = null;
    try {
      const lastEntry = await LedgerEntry.findOne({})
        .sort({ timestamp: -1, _id: -1 })
        .select('hash timestamp')
        .lean();
      if (lastEntry) {
        chainTip = { hash: lastEntry.hash, timestamp: lastEntry.timestamp };
      }
    } catch {
      chainTip = null;
    }

    // Recent signals (last 3, no sensitive data)
    let recentSignals = [];
    try {
      recentSignals = await ComplianceSignal.find({})
        .sort({ created_at: -1 })
        .limit(3)
        .select('signal_id type severity trace_id created_at')
        .lean();
    } catch {
      recentSignals = [];
    }

    const setuEnabled = process.env.SETU_ENABLED === 'true';
    const setuConfigured = !!(process.env.SETU_BASE_URL && process.env.SETU_API_KEY);

    const runtime = {
      status: dbState === 1 ? 'operational' : 'degraded',
      checked_at: new Date().toISOString(),
      latency_ms: Date.now() - t0,
      version: '0.1.0',
      environment: process.env.NODE_ENV || 'development',

      infrastructure: {
        database: {
          status: dbState === 1 ? 'connected' : 'disconnected',
          transactions_available: areTransactionsAvailable(),
        },
        redis: { status: redisStatus },
      },

      ledger: {
        posted_journal_entries: totalPostedJournals,
        ledger_entries: totalLedgerEntries,
        chain_tip: chainTip,
      },

      compliance: {
        signals_in_db: totalSignals,
        recent_signals: recentSignals.map(s => ({
          signal_id: s.signal_id,
          type: s.type,
          severity: s.severity,
          trace_id: s.trace_id,
          created_at: s.created_at,
        })),
      },

      transactions: {
        sent_invoices: totalSentInvoices,
        recorded_expenses: totalRecordedExpenses,
      },

      setu: {
        enabled: setuEnabled,
        configured: setuConfigured,
        dispatch_surface: setuEnabled && setuConfigured ? 'live' : 'payload-proof-only',
      },

      endpoints: {
        signals:        'GET /api/v1/signals',
        snapshot:       'GET /api/v1/signals/snapshot',
        trace:          'GET /api/v1/signals/trace/:traceId',
        pipeline_check: 'GET /api/v1/signals/:signalId/pipeline-check',
        dispatch:       'POST /api/v1/signals/:signalId/dispatch',
        verify_chain:   'GET /api/v1/ledger/verify-chain',
        gst_summary:    'GET /api/v1/gst/summary?period=YYYY-MM',
        tds_dashboard:  'GET /api/v1/tds/dashboard?quarter=Q4&financialYear=FY2025-26',
        health:         'GET /health',
      },
    };

    res.json({ success: true, data: runtime });
  } catch (error) {
    logger.error('Runtime status error:', error);
    res.status(500).json({
      success: false,
      message: 'Runtime status check failed',
      error: error.message,
    });
  }
});

export default router;
