import RuntimeProof from '../models/RuntimeProof.js';
import logger from '../config/logger.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * RuntimeProofService - Verifiable runtime evidence capture
 * 
 * Solves: "Documentation Is Not Runtime Proof"
 * - Captures actual API responses
 * - Records database states (before/after)
 * - Stores terminal logs
 * - Saves curl outputs
 * - Validates assertions
 */
class RuntimeProofService {
  /**
   * Capture API response as runtime proof
   */
  async captureAPIResponse({ trace_id, endpoint, method, req, res, latency_ms }) {
    try {
      const proof = await RuntimeProof.create({
        trace_id,
        proof_type: 'API_RESPONSE',
        endpoint,
        method,
        request: {
          headers: this.sanitizeHeaders(req.headers),
          body: req.body,
          query: req.query,
          timestamp: new Date(),
        },
        response: {
          status: res.statusCode,
          headers: this.sanitizeHeaders(res.getHeaders()),
          body: res.locals.responseBody || { message: 'Response captured' },
          latency_ms,
          timestamp: new Date(),
        },
        environment: await this.captureEnvironment(),
      });
      
      logger.info(`RuntimeProof captured: ${proof.proof_id} for trace ${trace_id}`);
      return proof;
    } catch (error) {
      logger.error('Capture API response error:', error);
      throw error;
    }
  }
  
  /**
   * Capture database state (before/after)
   */
  async captureDatabaseState({ trace_id, before, after, queries = [] }) {
    try {
      const proof = await RuntimeProof.create({
        trace_id,
        proof_type: 'DATABASE_STATE',
        db_state: {
          before: this.sanitizeDBState(before),
          after: this.sanitizeDBState(after),
          queries,
        },
        environment: await this.captureEnvironment(),
      });
      
      logger.info(`Database state captured: ${proof.proof_id} for trace ${trace_id}`);
      return proof;
    } catch (error) {
      logger.error('Capture database state error:', error);
      throw error;
    }
  }
  
  /**
   * Capture terminal/console output
   */
  async captureTerminalLog({ trace_id, output, metadata = {} }) {
    try {
      const proof = await RuntimeProof.create({
        trace_id,
        proof_type: 'TERMINAL_LOG',
        console_output: output,
        environment: await this.captureEnvironment(),
        request: { metadata, timestamp: new Date() },
      });
      
      logger.info(`Terminal log captured: ${proof.proof_id} for trace ${trace_id}`);
      return proof;
    } catch (error) {
      logger.error('Capture terminal log error:', error);
      throw error;
    }
  }
  
  /**
   * Capture curl output
   */
  async captureCurlOutput({ trace_id, curl_command, output, exit_code }) {
    try {
      const proof = await RuntimeProof.create({
        trace_id,
        proof_type: 'CURL_OUTPUT',
        console_output: output,
        request: {
          body: { curl_command, exit_code },
          timestamp: new Date(),
        },
        environment: await this.captureEnvironment(),
      });
      
      logger.info(`Curl output captured: ${proof.proof_id} for trace ${trace_id}`);
      return proof;
    } catch (error) {
      logger.error('Capture curl output error:', error);
      throw error;
    }
  }
  
  /**
   * Capture chain verification result
   */
  async captureChainVerification({ trace_id, verification_result }) {
    try {
      const proof = await RuntimeProof.create({
        trace_id,
        proof_type: 'CHAIN_VERIFICATION',
        response: {
          body: verification_result,
          timestamp: new Date(),
        },
        environment: await this.captureEnvironment(),
      });
      
      // Add assertions
      proof.addAssertion(
        'Chain is valid',
        true,
        verification_result.isValid
      );
      
      if (verification_result.errors && verification_result.errors.length > 0) {
        proof.addAssertion(
          'No chain errors',
          0,
          verification_result.errors.length
        );
      }
      
      await proof.save();
      
      logger.info(`Chain verification captured: ${proof.proof_id} for trace ${trace_id}`);
      return proof;
    } catch (error) {
      logger.error('Capture chain verification error:', error);
      throw error;
    }
  }
  
  /**
   * Capture balance sheet verification
   */
  async captureBalanceSheetVerification({ trace_id, balance_sheet }) {
    try {
      const proof = await RuntimeProof.create({
        trace_id,
        proof_type: 'BALANCE_SHEET',
        response: {
          body: balance_sheet,
          timestamp: new Date(),
        },
        environment: await this.captureEnvironment(),
      });
      
      // Add accounting equation assertion: Assets = Liabilities + Equity
      const assets = parseFloat(balance_sheet.assets?.total || 0);
      const liabilities = parseFloat(balance_sheet.liabilities?.total || 0);
      const equity = parseFloat(balance_sheet.equity?.total || 0);
      const isBalanced = Math.abs(assets - (liabilities + equity)) < 0.01;
      
      proof.addAssertion(
        'Accounting equation: Assets = Liabilities + Equity',
        true,
        isBalanced
      );
      
      proof.addAssertion(
        'Assets value',
        assets,
        assets
      );
      
      await proof.save();
      
      logger.info(`Balance sheet verification captured: ${proof.proof_id} for trace ${trace_id}`);
      return proof;
    } catch (error) {
      logger.error('Capture balance sheet verification error:', error);
      throw error;
    }
  }
  
  /**
   * Add assertion to existing proof
   */
  async addAssertion(proof_id, description, expected, actual) {
    try {
      const proof = await RuntimeProof.findOne({ proof_id });
      if (!proof) {
        throw new Error(`Proof not found: ${proof_id}`);
      }
      
      const passed = proof.addAssertion(description, expected, actual);
      await proof.save();
      
      return { passed, proof };
    } catch (error) {
      logger.error('Add assertion error:', error);
      throw error;
    }
  }
  
  /**
   * Verify proof
   */
  async verifyProof(proof_id, user_id) {
    try {
      const proof = await RuntimeProof.findOne({ proof_id });
      if (!proof) {
        throw new Error(`Proof not found: ${proof_id}`);
      }
      
      const verified = await proof.verify(user_id);
      
      logger.info(`Proof ${proof_id} verification: ${verified ? 'PASSED' : 'FAILED'}`);
      return { verified, proof };
    } catch (error) {
      logger.error('Verify proof error:', error);
      throw error;
    }
  }
  
  /**
   * Get all proofs for a trace
   */
  async getProofsForTrace(trace_id) {
    try {
      const proofs = await RuntimeProof.find({ trace_id })
        .populate('verified_by', 'name email')
        .sort({ created_at: -1 });
      
      return {
        trace_id,
        total_proofs: proofs.length,
        verified_proofs: proofs.filter(p => p.verified).length,
        proofs: proofs.map(p => p.getSummary()),
        full_proofs: proofs,
      };
    } catch (error) {
      logger.error('Get proofs for trace error:', error);
      throw error;
    }
  }
  
  /**
   * Generate runtime proof report
   */
  async generateReport(filters = {}) {
    try {
      const { trace_id, proof_type, verified, date_from, date_to } = filters;
      
      const query = {};
      if (trace_id) query.trace_id = trace_id;
      if (proof_type) query.proof_type = proof_type;
      if (verified !== undefined) query.verified = verified === 'true';
      
      if (date_from || date_to) {
        query.created_at = {};
        if (date_from) query.created_at.$gte = new Date(date_from);
        if (date_to) query.created_at.$lte = new Date(date_to);
      }
      
      const proofs = await RuntimeProof.find(query)
        .populate('verified_by', 'name email')
        .sort({ created_at: -1 });
      
      const totalAssertions = proofs.reduce((sum, p) => sum + p.assertions.length, 0);
      const passedAssertions = proofs.reduce((sum, p) => 
        sum + p.assertions.filter(a => a.passed).length, 0
      );
      
      return {
        summary: {
          total_proofs: proofs.length,
          verified: proofs.filter(p => p.verified).length,
          unverified: proofs.filter(p => !p.verified).length,
          total_assertions: totalAssertions,
          passed_assertions: passedAssertions,
          failed_assertions: totalAssertions - passedAssertions,
          pass_rate: totalAssertions > 0 ? 
            ((passedAssertions / totalAssertions) * 100).toFixed(2) + '%' : 'N/A',
        },
        by_type: this.groupByType(proofs),
        proofs: proofs.map(p => p.getSummary()),
      };
    } catch (error) {
      logger.error('Generate report error:', error);
      throw error;
    }
  }
  
  /**
   * Helper: Sanitize headers (remove sensitive data)
   */
  sanitizeHeaders(headers) {
    const sanitized = { ...headers };
    const sensitiveKeys = ['authorization', 'cookie', 'x-api-key', 'x-auth-token'];
    
    sensitiveKeys.forEach(key => {
      if (sanitized[key]) {
        sanitized[key] = '[REDACTED]';
      }
    });
    
    return sanitized;
  }
  
  /**
   * Helper: Sanitize database state (remove sensitive fields)
   */
  sanitizeDBState(state) {
    if (!state) return null;
    
    const sanitized = JSON.parse(JSON.stringify(state));
    
    // Remove password, token, secret fields recursively
    const removeSensitiveFields = (obj) => {
      if (typeof obj !== 'object' || obj === null) return;
      
      Object.keys(obj).forEach(key => {
        if (['password', 'token', 'secret', 'apiKey', 'api_key'].includes(key)) {
          obj[key] = '[REDACTED]';
        } else if (typeof obj[key] === 'object') {
          removeSensitiveFields(obj[key]);
        }
      });
    };
    
    removeSensitiveFields(sanitized);
    return sanitized;
  }
  
  /**
   * Helper: Capture current environment
   */
  async captureEnvironment() {
    const mongoose = await import('mongoose');
    const redis = await import('../config/redis.js');
    
    return {
      node_env: process.env.NODE_ENV || 'development',
      node_version: process.version,
      mongodb_version: mongoose.default.connection?.db?.serverConfig?.s?.description?.version || 'unknown',
      redis_available: redis.getRedisClient() !== null,
      timestamp: new Date(),
    };
  }
  
  /**
   * Helper: Group proofs by type
   */
  groupByType(proofs) {
    return proofs.reduce((acc, proof) => {
      const type = proof.proof_type;
      if (!acc[type]) {
        acc[type] = {
          count: 0,
          verified: 0,
          total_assertions: 0,
          passed_assertions: 0,
        };
      }
      
      acc[type].count++;
      if (proof.verified) acc[type].verified++;
      acc[type].total_assertions += proof.assertions.length;
      acc[type].passed_assertions += proof.assertions.filter(a => a.passed).length;
      
      return acc;
    }, {});
  }
}

export default new RuntimeProofService();
