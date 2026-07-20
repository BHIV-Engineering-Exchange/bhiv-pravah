import Decimal from 'decimal.js';
import ChartOfAccounts from '../models/ChartOfAccounts.js';
import LedgerEntry from '../models/LedgerEntry.js';

class StatutoryReportsService {
  async sumLedgerForAccounts(accountIds, startDate = null, endDate = null) {
    if (!accountIds.length) {
      return { debit: new Decimal(0), credit: new Decimal(0) };
    }

    const query = {
      account_id: { $in: accountIds },
    };

    if (startDate || endDate) {
      query.timestamp = {};
      if (startDate) query.timestamp.$gte = new Date(startDate);
      if (endDate) query.timestamp.$lte = new Date(endDate);
    }

    const entries = await LedgerEntry.find(query).select('type amount');

    return entries.reduce((acc, entry) => {
      const amount = new Decimal(entry.amount || 0);
      if (entry.type === 'DEBIT') {
        acc.debit = acc.debit.plus(amount);
      } else {
        acc.credit = acc.credit.plus(amount);
      }
      return acc;
    }, { debit: new Decimal(0), credit: new Decimal(0) });
  }

  async getAccountIdsByName(name) {
    const accounts = await ChartOfAccounts.find({
      name: { $regex: `^${name}$`, $options: 'i' },
      isActive: true,
    }).select('_id');

    return accounts.map((account) => String(account._id));
  }

  async getGSTSummary({ startDate = null, endDate = null } = {}) {
    const outputCGSTIds = await this.getAccountIdsByName('Output CGST');
    const outputSGSTIds = await this.getAccountIdsByName('Output SGST');
    const outputIGSTIds = await this.getAccountIdsByName('Output IGST');
    const inputCGSTIds = await this.getAccountIdsByName('Input CGST');
    const inputSGSTIds = await this.getAccountIdsByName('Input SGST');
    const inputIGSTIds = await this.getAccountIdsByName('Input IGST');

    const outputCGST = await this.sumLedgerForAccounts(outputCGSTIds, startDate, endDate);
    const outputSGST = await this.sumLedgerForAccounts(outputSGSTIds, startDate, endDate);
    const outputIGST = await this.sumLedgerForAccounts(outputIGSTIds, startDate, endDate);
    const inputCGST = await this.sumLedgerForAccounts(inputCGSTIds, startDate, endDate);
    const inputSGST = await this.sumLedgerForAccounts(inputSGSTIds, startDate, endDate);
    const inputIGST = await this.sumLedgerForAccounts(inputIGSTIds, startDate, endDate);

    const totalOutput = outputCGST.credit.plus(outputSGST.credit).plus(outputIGST.credit);
    const totalInput = inputCGST.debit.plus(inputSGST.debit).plus(inputIGST.debit);
    const netPayable = totalOutput.minus(totalInput);

    const breakdown = {
      cgst: outputCGST.credit.minus(inputCGST.debit).toString(),
      sgst: outputSGST.credit.minus(inputSGST.debit).toString(),
      igst: outputIGST.credit.minus(inputIGST.debit).toString(),
    };

    return {
      total_output_tax: totalOutput.toString(),
      total_input_credit: totalInput.toString(),
      net_payable: netPayable.toString(),
      breakdown,
    };
  }

  async getTDSSummary({ startDate = null, endDate = null } = {}) {
    const tdsPayableIds = await this.getAccountIdsByName('TDS Payable');
    const totals = await this.sumLedgerForAccounts(tdsPayableIds, startDate, endDate);

    const totalDeducted = totals.credit;
    const totalPayable = totals.credit.minus(totals.debit);

    return {
      total_tds_deducted: totalDeducted.toString(),
      total_tds_payable: totalPayable.toString(),
    };
  }
}

export default new StatutoryReportsService();
