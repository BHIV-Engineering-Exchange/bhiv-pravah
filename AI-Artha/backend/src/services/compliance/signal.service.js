import ComplianceSignal from '../../models/ComplianceSignal.js';
import TDSEntry from '../../models/TDSEntry.js';
import ComplianceValidationLog from '../../models/ComplianceValidationLog.js';
import statutoryReportsService from '../statutoryReports.service.js';
import { buildTraceId, parseMonthPeriod, parseQuarterPeriod } from './period.util.js';

const GST_SPIKE_THRESHOLD = 100000;
const TDS_RISK_THRESHOLD = 50000;

class ComplianceSignalService {
  async generateSignals({ period, quarter, financialYear } = {}) {
    const signals = [];
    const traceId = buildTraceId();

    if (period) {
      const { startDate, endDate } = parseMonthPeriod(period);
      const gstSummary = await statutoryReportsService.getGSTSummary({ startDate, endDate });
      const netPayable = Number(gstSummary?.net_payable || 0);

      if (netPayable > GST_SPIKE_THRESHOLD) {
        signals.push({
          trace_id: traceId,
          type: 'GST_PAYABLE_SPIKE',
          severity: 'HIGH',
          context: { period, netPayable },
          recommendation: 'Review GST payable increase and validate outward supplies',
        });
      }

      const validationFailures = await ComplianceValidationLog.find({
        'period.month': parseInt(period.split('-')[1], 10),
        'period.year': parseInt(period.split('-')[0], 10),
        filing_ready: false,
      }).lean();

      if (validationFailures.length) {
        signals.push({
          trace_id: traceId,
          type: 'FILING_READINESS_FAILURE',
          severity: 'HIGH',
          context: { period, failures: validationFailures.length },
          recommendation: 'Resolve validation errors before filing',
        });
      }
    }

    if (quarter && financialYear) {
      const { startDate, endDate } = parseQuarterPeriod(quarter, financialYear);
      const tdsSummary = await statutoryReportsService.getTDSSummary({ startDate, endDate });
      const tdsPayable = Number(tdsSummary?.total_tds_payable || 0);

      if (tdsPayable > TDS_RISK_THRESHOLD) {
        signals.push({
          trace_id: traceId,
          type: 'TDS_LIABILITY_RISK',
          severity: 'MEDIUM',
          context: { quarter, financialYear, tdsPayable },
          recommendation: 'Review TDS liabilities and challan deposits',
        });
      }

      const missingChallan = await TDSEntry.countDocuments({
        transactionDate: { $gte: startDate, $lte: endDate },
        status: { $in: ['deducted', 'deposited'] },
        challanNumber: { $in: [null, ''] },
      });

      if (missingChallan > 0) {
        signals.push({
          trace_id: traceId,
          type: 'MISSING_CHALLANS',
          severity: 'HIGH',
          context: { quarter, financialYear, missingChallan },
          recommendation: 'Link challans to all deducted TDS entries',
        });
      }
    }

    if (!signals.length) return [];

    const saved = await ComplianceSignal.insertMany(signals.map((signal) => ({
      ...signal,
      source: 'ARTHA',
    })));

    return saved;
  }
}

export default new ComplianceSignalService();
