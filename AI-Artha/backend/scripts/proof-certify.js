/**
 * PHASE 4 — CERTIFICATION GENERATION
 * 
 * Reads evidence from Phases 1-3 and generates:
 *   - ARTHA_INTEGRITY_CERTIFICATE.json
 *   - ARTHA_PRODUCTION_CERTIFICATE.json
 *   - DEPLOYMENT_READINESS_CHECKLIST.json
 * 
 * All values derived from actual execution evidence.
 * Usage: node scripts/proof-certify.js
 */

import 'dotenv/config';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const BASE = path.resolve(__dirname, '..');

// Ensure .env is loaded
const envPath = path.join(BASE, '.env');
if (!process.env.MONGODB_URI) {
  const envContent = await fs.readFile(envPath, 'utf8');
  for (const line of envContent.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx > 0) {
      const key = trimmed.slice(0, eqIdx).trim();
      const val = trimmed.slice(eqIdx + 1).trim();
      if (!process.env[key]) process.env[key] = val;
    }
  }
}
const EVIDENCE_DIR = path.join(BASE, 'docs/evidence');
const HANDOVER_DIR = path.join(BASE, 'docs/handover');
const REPORT_DIR = path.join(BASE, 'docs/reports');

function ensureDir(dir) { return fs.mkdir(dir, { recursive: true }); }
function timestamp() { return new Date().toISOString(); }
function writeJSON(f, d) { return fs.writeFile(f, JSON.stringify(d, null, 2)); }

async function readEvidence(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (e) {
    return null;
  }
}

async function run() {
  console.log('═══════════════════════════════════════════════════════');
  console.log('  PHASE 4 — CERTIFICATION GENERATION');
  console.log('═══════════════════════════════════════════════════════\n');

  await ensureDir(HANDOVER_DIR);
  await ensureDir(REPORT_DIR);

  // ── Read all evidence ──────────────────────────────────────────────────
  console.log('[Step 1] Reading evidence from Phases 1-3...');

  const replayEvidence = await readEvidence(path.join(EVIDENCE_DIR, 'phase4/replay_verification_results.json'));
  const complianceEvidence = await readEvidence(path.join(EVIDENCE_DIR, 'phase4/full_compliance_trace_evidence.json'));
  const auditEvidence = await readEvidence(path.join(EVIDENCE_DIR, 'phase5/production_audit_results.json'));

  console.log('  Replay evidence:', replayEvidence ? `${replayEvidence.status}` : 'NOT FOUND');
  console.log('  Compliance evidence:', complianceEvidence ? `${complianceEvidence.status}` : 'NOT FOUND');
  console.log('  Audit evidence:', auditEvidence ? `Score: ${auditEvidence.summary?.overall_score}` : 'NOT FOUND');

  // ── Determine statuses ─────────────────────────────────────────────────
  // Replay: check structural match, not just status field
  const replayStep7 = replayEvidence?.steps?.find(s => s.step === 7)?.data;
  const replayStep9 = replayEvidence?.steps?.find(s => s.step === 9)?.data;
  const replayFinancialMatch = replayStep7?.financial_equivalence === true;
  const replayStructuralMatch = replayStep7?.overall_match === true;
  const replayChainIntact = replayStep9?.statistics?.hasGaps === false && replayStep9?.status !== 'WARNING';
  const replayPassed = replayEvidence?.status === 'PASS' && replayFinancialMatch && replayStructuralMatch && replayChainIntact;

  // Compliance: check actual continuity, not just status field
  const complianceContinuity = complianceEvidence?.summary?.continuity === true;
  const complianceMissingStages = complianceEvidence?.summary?.missing_stages?.length || 0;
  const compliancePassed = complianceEvidence?.status === 'PASS' && complianceContinuity && complianceMissingStages === 0;

  // Audit: use corrected overall_score from audit evidence (after contradiction fixes)
  // PDF rule: certificate score MUST match evidence score exactly
  const actualAuditScore = auditEvidence?.summary?.overall_score || 0;
  const allAuditChecks = auditEvidence?.audits?.flatMap(a => a.checks) || [];
  const totalChecks = allAuditChecks.length;
  const passedChecks = allAuditChecks.filter(c => c.passed === true).length;
  const auditPassed = actualAuditScore >= 60;

  const phasesCompleted = [
    replayEvidence ? 1 : null,
    complianceEvidence ? 2 : null,
    auditEvidence ? 3 : null,
  ].filter(Boolean);

  const allPhasesComplete = phasesCompleted.length === 3;

  // ── ARTHA_INTEGRITY_CERTIFICATE ────────────────────────────────────────
  console.log('\n[Step 2] Generating Integrity Certificate...');

  // Build failure reasons for verdict
  const integrityFailures = [];
  if (!replayPassed) {
    if (!replayFinancialMatch) integrityFailures.push('replay financial equivalence failed');
    if (!replayStructuralMatch) integrityFailures.push('replay structural match failed');
    if (!replayChainIntact) integrityFailures.push('replay chain integrity broken');
  }
  if (!compliancePassed) {
    if (!complianceContinuity) integrityFailures.push('trace continuity broken');
    if (complianceMissingStages > 0) integrityFailures.push(`${complianceMissingStages} compliance stages missing`);
  }
  if (!auditPassed) integrityFailures.push(`audit score ${actualAuditScore}/100`);

  const integrityCert = {
    certificate_id: `CERT-INT-${Date.now()}`,
    certificate_type: 'ARTHA_INTEGRITY_CERTIFICATE',
    issued_at: timestamp(),
    valid_until: new Date(Date.now() + 365 * 86400000).toISOString(),
    issuer: 'ARTHA Certification System',
    subject: {
      system: 'ARTHA v0.1',
      description: 'India-Compliant Double-Entry Accounting System',
      repository: 'AI-Artha-main',
    },
    integrity_status: {
      deterministic_replay: {
        status: replayPassed ? 'VERIFIED' : 'FAILED',
        evidence_file: 'docs/evidence/phase4/replay_verification_results.json',
        details: replayPassed
          ? 'DETERMINISTIC REPLAY PROVEN — All outputs match, structure identical, chain intact'
          : `REPLAY FAILED — ${integrityFailures.filter(f => f.includes('replay')).join('; ')}`,
        original_entry: replayEvidence?.steps?.find(s => s.step === 2)?.data?.journal?.entry_number || null,
        replay_entry: replayEvidence?.steps?.find(s => s.step === 6)?.data?.replay_entry_number || null,
        outputs_match: replayFinancialMatch,
        structure_match: replayStructuralMatch,
        chain_intact: replayChainIntact,
      },
      compliance_continuity: {
        status: compliancePassed ? 'VERIFIED' : 'FAILED',
        evidence_file: 'docs/evidence/phase4/full_compliance_trace_evidence.json',
        details: compliancePassed
          ? 'COMPLIANCE CONTINUITY PROVEN — All stages captured, trace continuous'
          : `CONTINUITY FAILED — ${integrityFailures.filter(f => !f.includes('replay') && !f.includes('audit')).join('; ')}`,
        stages_captured: complianceEvidence?.summary?.stages_captured || [],
        missing_stages: complianceEvidence?.summary?.missing_stages || [],
        trace_continuous: complianceContinuity,
      },
      ledger_integrity: {
        status: (replayChainIntact && auditEvidence?.audits?.[2]?.checks?.every(c => c.passed)) ? 'VERIFIED' : 'FAILED',
        double_entry_balanced: auditEvidence?.audits?.[2]?.checks?.[0]?.passed || false,
        hash_chain_valid: auditEvidence?.audits?.[2]?.checks?.[1]?.passed || false,
        account_balances_consistent: auditEvidence?.audits?.[2]?.checks?.[2]?.passed || false,
      },
    },
    overall_integrity: replayPassed && compliancePassed && auditPassed,
    score: {
      replay: replayPassed ? 100 : 0,
      compliance: compliancePassed ? 100 : 0,
      audit: actualAuditScore,
      overall: Math.round(((replayPassed ? 100 : 0) + (compliancePassed ? 100 : 0) + actualAuditScore) / 3),
    },
    failed_checks: integrityFailures,
    verdict: replayPassed && compliancePassed && auditPassed
      ? 'ARTHA INTEGRITY CERTIFIED — Deterministic replay proven, compliance continuity verified, ledger integrity confirmed'
      : `ARTHA INTEGRITY FAILED — Contradictions found: ${integrityFailures.join('; ')}`,
  };

  await writeJSON(path.join(HANDOVER_DIR, 'ARTHA_INTEGRITY_CERTIFICATE.json'), integrityCert);
  console.log('  ✓ Integrity certificate generated');

  // ── ARTHA_PRODUCTION_CERTIFICATE ───────────────────────────────────────
  console.log('\n[Step 3] Generating Production Certificate...');

  // Check SETU dispatch status from compliance evidence
  // PDF rule: If evidence says dispatched=false, certificate MUST say NOT_CERTIFIED
  const setuDispatch = complianceEvidence?.stages_captured?.find(s => s.stage === 'SETU_DISPATCHED');
  const setuSimulated = setuDispatch?.simulation === true || setuDispatch?.dispatched === false;
  const setuVerified = setuDispatch?.dispatched === true && setuDispatch?.simulation !== true;

  const prodCert = {
    certificate_id: `CERT-PROD-${Date.now()}`,
    certificate_type: 'ARTHA_PRODUCTION_CERTIFICATE',
    issued_at: timestamp(),
    valid_until: new Date(Date.now() + 180 * 86400000).toISOString(),
    issuer: 'ARTHA Certification System',
    subject: {
      system: 'ARTHA v0.1',
      description: 'India-Compliant Double-Entry Accounting System',
      repository: 'AI-Artha-main',
    },
    production_readiness: {
      audit_score: actualAuditScore,
      audit_verdict: auditPassed ? 'PRODUCTION READY' : `AUDIT FAILED — ${passedChecks}/${totalChecks} checks passed`,
      phases_completed: phasesCompleted,
      total_phases: 3,
      all_phases_complete: allPhasesComplete,
      security_score: auditEvidence?.summary?.audits?.[1]?.percentage || 0,
      security_max: 100,
      database_integrity_score: auditEvidence?.summary?.audits?.[2]?.percentage || 0,
      database_integrity_max: 100,
      api_compliance_score: auditEvidence?.summary?.audits?.[3]?.percentage || 0,
      api_compliance_max: 100,
      configuration_score: auditEvidence?.summary?.audits?.[4]?.percentage || 0,
      configuration_max: 100,
      system_health_score: auditEvidence?.summary?.audits?.[0]?.percentage || 0,
      system_health_max: 100,
    },
    certifications: {
      integrity: integrityCert.overall_integrity ? 'CERTIFIED' : 'FAILED',
      replay: replayPassed ? 'CERTIFIED' : 'FAILED',
      compliance: compliancePassed ? 'CERTIFIED' : 'FAILED',
      audit: auditPassed ? 'CERTIFIED' : 'FAILED',
      setu: setuVerified ? 'CERTIFIED' : 'NOT_CERTIFIED',
    },
    setu_status: {
      simulated: setuSimulated,
      dispatched: setuDispatch?.dispatched || false,
      reason: setuDispatch?.reason || 'Unknown',
    },
    deployment_ready: allPhasesComplete && auditPassed && replayPassed && compliancePassed && setuVerified,
    conditions: [],
    verdict: allPhasesComplete && auditPassed && replayPassed && compliancePassed && setuVerified
      ? 'ARTHA PRODUCTION CERTIFIED — All phases complete, all audits passed, SETU verified, ready for deployment'
      : 'ARTHA PRODUCTION FAILED — Contradictions must be eliminated before certification',
  };

  // Add conditions if not fully certified
  if (!replayPassed) prodCert.conditions.push('Deterministic replay proof failed — structural mismatch between original and replay');
  if (!compliancePassed) prodCert.conditions.push('Compliance continuity proof failed — trace not continuous');
  if (!auditPassed) prodCert.conditions.push(`Audit score ${actualAuditScore}/100 — ${totalChecks - passedChecks} checks failed`);
  if (!allPhasesComplete) prodCert.conditions.push(`Only ${phasesCompleted.length}/3 phases completed`);
  if (setuSimulated) prodCert.conditions.push('SETU dispatch is simulated — SETU_BASE_URL not configured, no actual dispatch proven');

  await writeJSON(path.join(HANDOVER_DIR, 'ARTHA_PRODUCTION_CERTIFICATE.json'), prodCert);
  console.log('  ✓ Production certificate generated');

  // ── DEPLOYMENT_READINESS_CHECKLIST ─────────────────────────────────────
  console.log('\n[Step 4] Generating Deployment Readiness Checklist...');

  const checklist = {
    checklist_id: `CHECKLIST-${Date.now()}`,
    generated_at: timestamp(),
    system: 'ARTHA v0.1',
    items: [
      {
        category: 'Replay Proof',
        item: 'Deterministic replay verified',
        status: replayPassed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/replay_verification_results.json',
      },
      {
        category: 'Replay Proof',
        item: 'Journal hashes match on replay',
        status: replayEvidence?.steps?.find(s => s.step === 7)?.data?.hash_chain_integrity ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/replay_verification_results.json',
      },
      {
        category: 'Replay Proof',
        item: 'Chain integrity maintained after replay',
        status: replayChainIntact ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/replay_verification_results.json',
      },
      {
        category: 'Compliance',
        item: 'Full compliance chain (Transaction → Journal → Signal → Filing → Validation → Dispatch)',
        status: compliancePassed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/full_compliance_trace_evidence.json',
      },
      {
        category: 'Compliance',
        item: 'No missing compliance stages',
        status: (complianceEvidence?.summary?.missing_stages?.length || 0) === 0 ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/full_compliance_trace_evidence.json',
      },
      {
        category: 'Compliance',
        item: 'Trace continuity verified',
        status: complianceEvidence?.summary?.continuity ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/full_compliance_trace_evidence.json',
      },
      {
        category: 'Security',
        item: 'JWT authentication configured',
        status: auditEvidence?.audits?.[1]?.checks?.[0]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/security_audit.json',
      },
      {
        category: 'Security',
        item: 'HMAC secret configured',
        status: auditEvidence?.audits?.[1]?.checks?.[1]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/security_audit.json',
      },
      {
        category: 'Security',
        item: 'Rate limiting enabled',
        status: auditEvidence?.audits?.[1]?.checks?.[4]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/security_audit.json',
      },
      {
        category: 'Database',
        item: 'Double-entry balance verified',
        status: auditEvidence?.audits?.[2]?.checks?.[0]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/database_integrity_audit.json',
      },
      {
        category: 'Database',
        item: 'Hash chain integrity verified',
        status: auditEvidence?.audits?.[2]?.checks?.[1]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/database_integrity_audit.json',
      },
      {
        category: 'Database',
        item: 'Account balances consistent',
        status: auditEvidence?.audits?.[2]?.checks?.[2]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/database_integrity_audit.json',
      },
      {
        category: 'API',
        item: 'All route files present',
        status: auditEvidence?.audits?.[3]?.checks?.[0]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/api_compliance_audit.json',
      },
      {
        category: 'API',
        item: 'All controller files present',
        status: auditEvidence?.audits?.[3]?.checks?.[1]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/api_compliance_audit.json',
      },
      {
        category: 'Configuration',
        item: 'Environment file exists',
        status: auditEvidence?.audits?.[4]?.checks?.[0]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/configuration_audit.json',
      },
      {
        category: 'Configuration',
        item: 'Docker configuration present',
        status: auditEvidence?.audits?.[4]?.checks?.[2]?.passed ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase5/configuration_audit.json',
      },
      {
        category: 'SETU Integration',
        item: 'SETU dispatch verified (not simulated)',
        status: setuVerified ? 'PASS' : 'FAIL',
        evidence: 'docs/evidence/phase4/full_compliance_trace_evidence.json',
      },
    ],
    summary: {
      total: 16,
      passed: 0,
      failed: 0,
    },
  };

  checklist.summary.passed = checklist.items.filter(i => i.status === 'PASS').length;
  checklist.summary.failed = checklist.items.filter(i => i.status === 'FAIL').length;
  checklist.summary.total = checklist.items.length;

  await writeJSON(path.join(HANDOVER_DIR, 'DEPLOYMENT_READINESS_CHECKLIST.json'), checklist);
  console.log('  ✓ Deployment checklist generated');

  // ── Summary ────────────────────────────────────────────────────────────
  console.log('\n═══════════════════════════════════════════════════════');
  console.log('  CERTIFICATION SUMMARY');
  console.log('═══════════════════════════════════════════════════════');
  console.log(`  Integrity:   ${integrityCert.overall_integrity ? '✅ CERTIFIED' : '❌ FAILED'}`);
  console.log(`  Production:  ${prodCert.deployment_ready ? '✅ CERTIFIED' : '❌ FAILED'}`);
  console.log(`  SETU:        ${setuVerified ? '✅ CERTIFIED' : '❌ NOT_CERTIFIED'}`);
  console.log(`  Checklist:   ${checklist.summary.passed}/${checklist.summary.total} passed`);
  console.log(`  Verdict:     ${prodCert.verdict}`);
  console.log('═══════════════════════════════════════════════════════\n');

  console.log('✅ Phase 4 complete. Certifications generated.\n');
}

run().catch(err => { console.error('Unhandled:', err); process.exit(1); });
