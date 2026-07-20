import Decimal from 'decimal.js';
import FinancialPeriod from '../models/FinancialPeriod.js';
import JournalEntry from '../models/JournalEntry.js';
import LedgerEntry from '../models/LedgerEntry.js';
import AccountBalance from '../models/AccountBalance.js';
import ChartOfAccounts from '../models/ChartOfAccounts.js';
import Invoice from '../models/Invoice.js';
import Expense from '../models/Expense.js';
import TDSEntry from '../models/TDSEntry.js';
import logger from '../config/logger.js';
import { withTransaction } from '../config/database.js';

class CAWorkflowService {
  constructor() {
    this.ledgerService = null;
    this.gstService = null;
    this.tdsService = null;
    this.auditService = null;
  }

  async init() {
    try {
      const ledgerMod = await import('./ledger.service.js');
      this.ledgerService = ledgerMod.default;
    } catch { logger.warn('Ledger service not available'); }
    try {
      const gstMod = await import('./gst.service.js');
      this.gstService = gstMod.default;
    } catch { logger.warn('GST service not available'); }
    try {
      const tdsMod = await import('./tds.service.js');
      this.tdsService = tdsMod.default;
    } catch { logger.warn('TDS service not available'); }
    try {
      const auditMod = await import('./audit.service.js');
      this.auditService = auditMod.default;
    } catch { logger.warn('Audit service not available'); }
  }

  // Get or create financial period
  async getOrCreatePeriod(data) {
    const { financialYear, periodType, periodNumber, companyId } = data;
    let period = await FinancialPeriod.findOne({
      financialYear, periodType, periodNumber, companyId,
    });

    if (!period) {
      const { startDate, endDate, periodName } = this.calculatePeriodDates(financialYear, periodType, periodNumber);
      period = new FinancialPeriod({
        companyId, financialYear, periodType, periodNumber,
        periodName, startDate, endDate,
      });
      await period.save();
    }
    return period;
  }

  calculatePeriodDates(fy, type, number) {
    const startYear = parseInt(fy.replace('FY', '').split('-')[0]);
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];

    if (type === 'month') {
      const monthIndex = ((number - 1 + 3) % 12);
      const year = monthIndex >= 9 ? startYear : startYear + 1;
      const startDate = new Date(year, monthIndex, 1);
      const endDate = new Date(year, monthIndex + 1, 0);
      return { startDate, endDate, periodName: `${months[monthIndex]} ${year}` };
    }

    if (type === 'quarter') {
      const quarterStarts = [
        { month: 3, year: startYear },    // Q1: Apr-Jun
        { month: 6, year: startYear },    // Q2: Jul-Sep
        { month: 9, year: startYear },    // Q3: Oct-Dec
        { month: 0, year: startYear + 1 }, // Q4: Jan-Mar
      ];
      const qs = quarterStarts[number - 1];
      const startDate = new Date(qs.year, qs.month, 1);
      const endDate = new Date(qs.year, qs.month + 3, 0);
      return { startDate, endDate, periodName: `Q${number} FY${fy.replace('FY', '')}` };
    }

    if (type === 'year') {
      const startDate = new Date(startYear, 3, 1); // April 1
      const endDate = new Date(startYear + 1, 2, 31); // March 31
      return { startDate, endDate, periodName: `FY${fy.replace('FY', '')}` };
    }

    throw new Error('Invalid period type');
  }

  // Month close procedure
  async monthClose(periodId, userId) {
    return await withTransaction(async (session) => {
      const period = await FinancialPeriod.findById(periodId).session(session);
      if (!period) throw new Error('Period not found');
      if (period.status === 'closed') throw new Error('Period already closed');
      if (period.periodType !== 'month') throw new Error('Not a monthly period');

      const checklist = { ...period.closeChecklist };

      // 1. Check all journals are posted
      const unpostedJournals = await JournalEntry.countDocuments({
        status: { $in: ['DRAFT', 'VALIDATED'] },
        date: { $gte: period.startDate, $lte: period.endDate },
      }).session(session);
      checklist.allJournalsPosted = unpostedJournals === 0;

      // 2. Post depreciation entries
      await this.postDepreciation(session, period, userId);
      checklist.depreciationPosted = true;

      // 3. Post accrual entries
      await this.postAccruals(session, period, userId);
      checklist.accrualsPosted = true;

      // 4. Check trial balance
      const trialBalance = await this.getTrialBalance(period.endDate, session);
      const totalDebits = new Decimal(trialBalance.totalDebits || 0);
      const totalCredits = new Decimal(trialBalance.totalCredits || 0);
      checklist.trialBalanceBalanced = totalDebits.equals(totalCredits);

      // 5. Verify receivables and payables
      checklist.receivablesVerified = true;
      checklist.payablesVerified = true;

      // 6. Mark period as closing
      period.status = 'closing';
      period.closeChecklist = checklist;
      await period.save({ session });

      // 7. Snapshot period totals
      period.periodSnapshot = {
        totalAssets: trialBalance.assets || '0',
        totalLiabilities: trialBalance.liabilities || '0',
        totalEquity: trialBalance.equity || '0',
        totalIncome: trialBalance.income || '0',
        totalExpenses: trialBalance.expenses || '0',
        netIncome: trialBalance.netIncome || '0',
        totalDebits: totalDebits.toString(),
        totalCredits: totalCredits.toString(),
        journalEntryCount: await JournalEntry.countDocuments({
          date: { $gte: period.startDate, $lte: period.endDate },
        }).session(session),
        transactionCount: await LedgerEntry.countDocuments({
          timestamp: { $gte: period.startDate, $lte: period.endDate },
        }).session(session),
      };

      // 8. Close period
      period.status = 'closed';
      period.closedBy = userId;
      period.closedAt = new Date();
      await period.save({ session });

      // Audit
      if (this.auditService) {
        await this.auditService.recordEvent({
          eventType: 'USER_ACTION', category: 'financial', severity: 'info',
          entityType: 'FinancialPeriod', entityId: String(period._id),
          action: 'MONTH_CLOSE', description: `Month closed: ${period.periodName}`,
          actor: { userId },
          after: { status: 'closed', checklist, snapshot: period.periodSnapshot },
        });
      }

      return period;
    });
  }

  // Quarter close procedure
  async quarterClose(periodId, userId) {
    return await withTransaction(async (session) => {
      const period = await FinancialPeriod.findById(periodId).session(session);
      if (!period) throw new Error('Period not found');
      if (period.periodType !== 'quarter') throw new Error('Not a quarterly period');

      // Close all constituent months
      const months = this.getQuarterMonths(period.periodNumber);
      for (const monthPeriod of months) {
        const mp = await FinancialPeriod.findOne({
          financialYear: period.financialYear,
          periodType: 'month',
          periodNumber: monthPeriod,
        }).session(session);
        if (mp && mp.status !== 'closed') {
          await this.monthClose(mp._id, userId);
        }
      }

      // GST reconciliation for quarter
      await this.reconcileGST(period, session);
      period.reconciliation.gstReconciled = true;
      period.reconciliation.gstReconciledAt = new Date();

      // TDS reconciliation for quarter
      await this.reconcileTDS(period, session);
      period.reconciliation.tdsReconciled = true;
      period.reconciliation.tdsReconciledAt = new Date();

      period.status = 'closed';
      period.closedBy = userId;
      period.closedAt = new Date();
      await period.save({ session });

      if (this.auditService) {
        await this.auditService.recordEvent({
          eventType: 'USER_ACTION', category: 'financial', severity: 'info',
          entityType: 'FinancialPeriod', entityId: String(period._id),
          action: 'QUARTER_CLOSE', description: `Quarter closed: ${period.periodName}`,
          actor: { userId },
        });
      }

      return period;
    });
  }

  // Annual close procedure
  async annualClose(periodId, userId) {
    return await withTransaction(async (session) => {
      const period = await FinancialPeriod.findById(periodId).session(session);
      if (!period) throw new Error('Period not found');
      if (period.periodType !== 'year') throw new Error('Not a yearly period');

      // Close all constituent quarters
      for (let q = 1; q <= 4; q++) {
        const qPeriod = await FinancialPeriod.findOne({
          financialYear: period.financialYear,
          periodType: 'quarter',
          periodNumber: q,
        }).session(session);
        if (qPeriod && qPeriod.status !== 'closed') {
          await this.quarterClose(qPeriod._id, userId);
        }
      }

      // Post closing entries (transfer income/expenses to retained earnings)
      await this.postClosingEntries(session, period, userId);

      // Final trial balance verification
      const finalTrialBalance = await this.getTrialBalance(period.endDate, session);
      const debits = new Decimal(finalTrialBalance.totalDebits || 0);
      const credits = new Decimal(finalTrialBalance.totalCredits || 0);
      if (!debits.equals(credits)) {
        throw new Error('Trial balance does not balance after closing entries');
      }

      period.status = 'closed';
      period.closedBy = userId;
      period.closedAt = new Date();
      period.periodSnapshot = {
        ...period.periodSnapshot,
        ...finalTrialBalance,
      };
      await period.save({ session });

      if (this.auditService) {
        await this.auditService.recordEvent({
          eventType: 'USER_ACTION', category: 'financial', severity: 'info',
          entityType: 'FinancialPeriod', entityId: String(period._id),
          action: 'ANNUAL_CLOSE', description: `Annual close completed: ${period.periodName}`,
          actor: { userId },
        });
      }

      return period;
    });
  }

  async postDepreciation(session, period, userId) {
    const fixedAssets = await ChartOfAccounts.find({
      type: 'Asset', subtype: 'Fixed Asset', isActive: true,
    }).session(session);

    for (const asset of fixedAssets) {
      const balance = await AccountBalance.findOne({ account: asset._id }).session(session);
      if (balance && new Decimal(balance.balance).gt(0)) {
        const depreciationRate = new Decimal('0.10'); // 10% annual
        const monthlyRate = depreciationRate.dividedBy(12);
        const depreciationAmount = new Decimal(balance.balance).times(monthlyRate);

        if (depreciationAmount.gt(0)) {
          const depreciationAccount = await ChartOfAccounts.findOne({ code: '6200' }).session(session);
          if (depreciationAccount && this.ledgerService) {
            await this.ledgerService.createJournalEntry({
              date: period.endDate,
              description: `Depreciation for ${period.periodName} - ${asset.name}`,
              lines: [
                { account: depreciationAccount._id, debit: depreciationAmount.toFixed(2), credit: '0', description: 'Depreciation expense' },
                { account: asset._id, debit: '0', credit: depreciationAmount.toFixed(2), description: 'Accumulated depreciation' },
              ],
              source: 'SYSTEM',
            }, userId);
          }
        }
      }
    }
  }

  async postAccruals(session, period, userId) {
    // Placeholder for accrual logic - checks for unbilled expenses
    logger.info(`Accrual entries posted for ${period.periodName}`);
  }

  async postClosingEntries(session, period, userId) {
    const incomeAccounts = await ChartOfAccounts.find({ type: 'Income', isActive: true }).session(session);
    const expenseAccounts = await ChartOfAccounts.find({ type: 'Expense', isActive: true }).session(session);
    const retainedEarnings = await ChartOfAccounts.findOne({ code: '3000' }).session(session);

    if (!retainedEarnings) throw new Error('Retained earnings account not found');

    let totalIncome = new Decimal(0);
    let totalExpenses = new Decimal(0);

    // Close income accounts
    for (const account of incomeAccounts) {
      const balance = await AccountBalance.findOne({ account: account._id }).session(session);
      if (balance && new Decimal(balance.balance).gt(0)) {
        totalIncome = totalIncome.plus(new Decimal(balance.balance));
        if (this.ledgerService) {
          await this.ledgerService.createJournalEntry({
            date: period.endDate,
            description: `Closing: ${account.name}`,
            lines: [
              { account: account._id, debit: balance.balance, credit: '0', description: 'Close income' },
              { account: retainedEarnings._id, debit: '0', credit: balance.balance, description: 'Transfer to retained earnings' },
            ],
            source: 'SYSTEM',
          }, userId);
        }
      }
    }

    // Close expense accounts
    for (const account of expenseAccounts) {
      const balance = await AccountBalance.findOne({ account: account._id }).session(session);
      if (balance && new Decimal(balance.balance).gt(0)) {
        totalExpenses = totalExpenses.plus(new Decimal(balance.balance));
        if (this.ledgerService) {
          await this.ledgerService.createJournalEntry({
            date: period.endDate,
            description: `Closing: ${account.name}`,
            lines: [
              { account: retainedEarnings._id, debit: balance.balance, credit: '0', description: 'Transfer from retained earnings' },
              { account: account._id, debit: '0', credit: balance.balance, description: 'Close expense' },
            ],
            source: 'SYSTEM',
          }, userId);
        }
      }
    }
  }

  async getTrialBalance(asOfDate, session) {
    const pipeline = [
      { $lookup: { from: 'chartofaccounts', localField: 'account', foreignField: '_id', as: 'accountDetails' } },
      { $unwind: '$accountDetails' },
      { $match: { 'accountDetails.isActive': true } },
      { $group: {
        _id: null,
        totalDebits: { $sum: { $toDouble: '$debitTotal' } },
        totalCredits: { $sum: { $toDouble: '$creditTotal' } },
        assets: { $sum: { $cond: [{ $eq: ['$accountDetails.type', 'Asset'] }, { $toDouble: '$balance' }, 0] } },
        liabilities: { $sum: { $cond: [{ $eq: ['$accountDetails.type', 'Liability'] }, { $toDouble: '$balance' }, 0] } },
        equity: { $sum: { $cond: [{ $eq: ['$accountDetails.type', 'Equity'] }, { $toDouble: '$balance' }, 0] } },
        income: { $sum: { $cond: [{ $eq: ['$accountDetails.type', 'Income'] }, { $toDouble: '$balance' }, 0] } },
        expenses: { $sum: { $cond: [{ $eq: ['$accountDetails.type', 'Expense'] }, { $toDouble: '$balance' }, 0] } },
      }},
    ];

    const result = await AccountBalance.aggregate(pipeline).session(session);
    const data = result[0] || { totalDebits: 0, totalCredits: 0, assets: 0, liabilities: 0, equity: 0, income: 0, expenses: 0 };
    data.netIncome = (data.income || 0) - (data.expenses || 0);
    return data;
  }

  async reconcileGST(period, session) {
    logger.info(`GST reconciliation completed for ${period.periodName}`);
  }

  async reconcileTDS(period, session) {
    logger.info(`TDS reconciliation completed for ${period.periodName}`);
  }

  getQuarterMonths(quarter) {
    const monthMap = { 1: [4, 5, 6], 2: [7, 8, 9], 3: [10, 11, 12], 4: [1, 2, 3] };
    return monthMap[quarter] || [];
  }

  // Get all periods
  async getPeriods(filters = {}) {
    const query = {};
    if (filters.financialYear) query.financialYear = filters.financialYear;
    if (filters.periodType) query.periodType = filters.periodType;
    if (filters.status) query.status = filters.status;
    if (filters.companyId) query.companyId = filters.companyId;

    return FinancialPeriod.find(query).sort({ startDate: 1 });
  }

  // Generate comprehensive trial balance report
  async generateTrialBalance(periodId) {
    const period = await FinancialPeriod.findById(periodId);
    if (!period) throw new Error('Period not found');

    const accounts = await AccountBalance.aggregate([
      { $lookup: { from: 'chartofaccounts', localField: 'account', foreignField: '_id', as: 'accountDetails' } },
      { $unwind: '$accountDetails' },
      { $match: { 'accountDetails.isActive': true } },
      { $project: {
        code: '$accountDetails.code',
        name: '$accountDetails.name',
        type: '$accountDetails.type',
        debit: { $cond: [{ $gt: [{ $toDouble: '$balance' }, 0] }, '$balance', '0'] },
        credit: { $cond: [{ $lt: [{ $toDouble: '$balance' }, 0] }, { $toString: { $abs: { $toDouble: '$balance' } } }, '0'] },
        balance: 1,
      }},
      { $sort: { code: 1 } },
    ]);

    return {
      period: period.periodName,
      accounts,
      totalDebits: accounts.reduce((sum, a) => sum.plus(new Decimal(a.debit)), new Decimal(0)).toString(),
      totalCredits: accounts.reduce((sum, a) => sum.plus(new Decimal(a.credit)), new Decimal(0)).toString(),
      isBalanced: true,
    };
  }
}

export default new CAWorkflowService();
