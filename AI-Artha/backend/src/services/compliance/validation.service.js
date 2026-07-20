import Decimal from 'decimal.js';
import ComplianceValidationLog from '../../models/ComplianceValidationLog.js';
import TDSValidationLog from '../../models/TDSValidationLog.js';
import { GST_ENGINE } from '../gstEngine.service.js';

const INVALID_GST_RATE = 'INVALID_GST_RATE';
const MISSING_GSTIN = 'MISSING_GSTIN';
const PERIOD_MISMATCH = 'PERIOD_MISMATCH';
const NEGATIVE_LIABILITY = 'NEGATIVE_LIABILITY';
const UNMAPPED_LEDGER = 'UNMAPPED_LEDGER';
const MISSING_CHALLAN = 'MISSING_CHALLAN';
const INVALID_TDS_SECTION = 'INVALID_TDS_SECTION';
const DUPLICATE_REFERENCE = 'DUPLICATE_FILING_REFERENCE';
const INVALID_TAX_CLASSIFICATION = 'INVALID_TAX_CLASSIFICATION';

const ALLOWED_TDS_SECTIONS = ['194A', '194C', '194H', '194I', '194J', '192', '194Q', 'other'];

const addError = (errors, code, severity, reference_id, message) => {
  errors.push({ code, severity, reference_id, message });
};

const inPeriod = (date, period) => {
  if (!date || !period?.startDate || !period?.endDate) return true;
  const dt = new Date(date);
  return dt >= period.startDate && dt <= period.endDate;
};

class ComplianceValidationService {
  async validateGSTR1({ filing, period, filingId, traceId }) {
    const errors = [];
    const seen = new Set();
    const allSections = Object.values(filing.sections || {}).flat();

    allSections.forEach((item) => {
      const key = `${item.invoice_number}-${item.supply_type}`;
      if (seen.has(key)) {
        addError(errors, DUPLICATE_REFERENCE, 'HIGH', item.invoice_number, 'Duplicate invoice reference');
      }
      seen.add(key);

      if (['B2B', 'CDNR'].includes(item.supply_type) && !item.gstin) {
        addError(errors, MISSING_GSTIN, 'HIGH', item.invoice_number, 'Missing GSTIN for registered supply');
      }

      if (!GST_ENGINE.isAllowedRate(item.tax_rate)) {
        addError(errors, INVALID_GST_RATE, 'HIGH', item.invoice_number, 'Invalid GST rate');
      }

      if (!inPeriod(item.invoice_date, period)) {
        addError(errors, PERIOD_MISMATCH, 'MEDIUM', item.invoice_number, 'Invoice date outside filing period');
      }

      const igst = new Decimal(item.igst || 0);
      const cgst = new Decimal(item.cgst || 0);
      const sgst = new Decimal(item.sgst || 0);
      if (igst.greaterThan(0) && (cgst.greaterThan(0) || sgst.greaterThan(0))) {
        addError(errors, INVALID_TAX_CLASSIFICATION, 'HIGH', item.invoice_number, 'IGST cannot be mixed with CGST/SGST');
      }
    });

    const filing_ready = errors.length === 0;

    await ComplianceValidationLog.create({
      filingId,
      filingType: 'GSTR-1',
      period,
      traceId,
      filing_ready,
      errors,
    });

    return { filing_ready, errors };
  }

  async validateGSTR3B({ filing, period, filingId, traceId }) {
    const errors = [];
    const liability = new Decimal(filing.taxLiability?.total || 0);
    if (liability.isNegative()) {
      addError(errors, NEGATIVE_LIABILITY, 'HIGH', 'GSTR-3B', 'Net tax liability cannot be negative');
    }

    const filing_ready = errors.length === 0;

    await ComplianceValidationLog.create({
      filingId,
      filingType: 'GSTR-3B',
      period,
      traceId,
      filing_ready,
      errors,
    });

    return { filing_ready, errors };
  }

  async validateForm26Q({ filing, period, filingId, traceId }) {
    const errors = [];
    (filing.deductees || []).forEach((deductee) => {
      if (!deductee.pan) {
        addError(errors, UNMAPPED_LEDGER, 'HIGH', deductee.name, 'Missing deductee PAN');
      }
      if (!ALLOWED_TDS_SECTIONS.includes(deductee.section)) {
        addError(errors, INVALID_TDS_SECTION, 'HIGH', deductee.pan, 'Invalid TDS section');
      }
      (deductee.entries || []).forEach((entry) => {
        if (!entry.challan_number) {
          addError(errors, MISSING_CHALLAN, 'HIGH', entry.entry_number, 'Missing challan linkage');
        }
      });
    });

    const filing_ready = errors.length === 0;

    await ComplianceValidationLog.create({
      filingId,
      filingType: 'FORM-26Q',
      period,
      traceId,
      filing_ready,
      errors,
    });

    await TDSValidationLog.create({
      quarter: period.quarter,
      financialYear: period.financialYear,
      filing_ready,
      errors,
    });

    return { filing_ready, errors };
  }

  async validateForm24Q({ filing, period, filingId, traceId }) {
    const errors = [];
    (filing.employees || []).forEach((employee) => {
      if (!employee.employee_pan) {
        addError(errors, UNMAPPED_LEDGER, 'HIGH', employee.employee_id, 'Missing employee PAN');
      }
      if (!employee.challan_number) {
        addError(errors, MISSING_CHALLAN, 'HIGH', employee.employee_id, 'Missing challan linkage');
      }
    });

    const filing_ready = errors.length === 0;

    await ComplianceValidationLog.create({
      filingId,
      filingType: 'FORM-24Q',
      period,
      traceId,
      filing_ready,
      errors,
    });

    await TDSValidationLog.create({
      quarter: period.quarter,
      financialYear: period.financialYear,
      filing_ready,
      errors,
    });

    return { filing_ready, errors };
  }
}

export default new ComplianceValidationService();
