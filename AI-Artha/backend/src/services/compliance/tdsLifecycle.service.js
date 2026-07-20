import Decimal from 'decimal.js';
import TDSEntry from '../../models/TDSEntry.js';
import TDSChallan from '../../models/TDSChallan.js';
import TDSQuarterlyGroup from '../../models/TDSQuarterlyGroup.js';
import { parseQuarterPeriod } from './period.util.js';

class TDSLifecycleService {
  async createChallan(data, userId) {
    const challan = await TDSChallan.create({
      ...data,
      createdBy: userId,
    });
    return challan;
  }

  async linkChallanToEntries(challanId, entryIds = []) {
    const challan = await TDSChallan.findById(challanId);
    if (!challan) throw new Error('Challan not found');

    await TDSEntry.updateMany({ _id: { $in: entryIds } }, {
      challanNumber: challan.challanNumber,
      challanDate: challan.challanDate,
      bankBSR: challan.bankBSR,
      status: 'deposited',
    });

    challan.tdsEntries = [...new Set([...(challan.tdsEntries || []), ...entryIds])];
    challan.status = 'linked';
    await challan.save();

    return challan;
  }

  async groupQuarter(quarter, financialYear) {
    const { startDate, endDate } = parseQuarterPeriod(quarter, financialYear);
    const entries = await TDSEntry.find({
      transactionDate: { $gte: startDate, $lte: endDate },
    }).lean();

    const totalDeducted = entries.reduce((sum, entry) => sum.plus(entry.tdsAmount || 0), new Decimal(0));
    const totalDeposited = entries
      .filter((entry) => entry.status === 'deposited' || entry.status === 'filed')
      .reduce((sum, entry) => sum.plus(entry.tdsAmount || 0), new Decimal(0));

    const sectionSummary = entries.reduce((acc, entry) => {
      if (!acc[entry.section]) {
        acc[entry.section] = { deducted: new Decimal(0), entries: 0 };
      }
      acc[entry.section].deducted = acc[entry.section].deducted.plus(entry.tdsAmount || 0);
      acc[entry.section].entries += 1;
      return acc;
    }, {});

    const group = await TDSQuarterlyGroup.findOneAndUpdate({
      quarter,
      financialYear,
    }, {
      quarter,
      financialYear,
      totalDeducted: totalDeducted.toString(),
      totalDeposited: totalDeposited.toString(),
      sectionSummary: Object.fromEntries(Object.entries(sectionSummary).map(([key, value]) => [
        key,
        { deducted: value.deducted.toString(), entries: value.entries },
      ])),
      entries: entries.map((entry) => entry._id),
      status: 'grouped',
    }, {
      upsert: true,
      new: true,
    });

    return group;
  }
}

export default new TDSLifecycleService();
