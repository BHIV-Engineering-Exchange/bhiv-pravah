import Decimal from 'decimal.js';
import Payment from '../models/Payment.js';
import JournalEntry from '../models/JournalEntry.js';
import Invoice from '../models/Invoice.js';
import Expense from '../models/Expense.js';
import BankStatement from '../models/BankStatement.js';
import ChartOfAccounts from '../models/ChartOfAccounts.js';
import LedgerEntry from '../models/LedgerEntry.js';
import logger from '../config/logger.js';
import { withTransaction } from '../config/database.js';

class BankingService {
  constructor() {
    this.ledgerService = null;
    this.traceabilityService = null;
    this.auditService = null;
  }

  async init() {
    try {
      const ledgerMod = await import('./ledger.service.js');
      this.ledgerService = ledgerMod.default;
    } catch { logger.warn('Ledger service not available for banking'); }
    try {
      const traceMod = await import('./traceability.service.js');
      this.traceabilityService = traceMod.default;
    } catch { logger.warn('Traceability service not available for banking'); }
    try {
      const auditMod = await import('./audit.service.js');
      this.auditService = auditMod.default;
    } catch { logger.warn('Audit service not available for banking'); }
  }

  // Payment initiation with validation
  async initiatePayment(data, userId) {
    const { entityType, entityId, amount, paymentMethod, payer, payee, bankDetails, traceId } = data;

    if (!['Invoice', 'Expense', 'TDSEntry', 'Manual'].includes(entityType)) {
      throw new Error('Invalid entity type');
    }

    const amountDecimal = new Decimal(amount);
    if (amountDecimal.lte(0)) throw new Error('Payment amount must be positive');

    // Validate payment method specifics
    this.validatePaymentMethod(paymentMethod, bankDetails);

    const payment = new Payment({
      entityType, entityId, amount: amountDecimal.toString(),
      paymentMethod, payer, payee, bankDetails,
      traceId, initiatedBy: userId, status: 'initiated',
    });

    // Set retry schedule for online payments
    if (paymentMethod !== 'Cash' && paymentMethod !== 'Cheque') {
      payment.nextRetryAt = new Date(Date.now() + 60000);
    }

    await payment.save();

    // Record trace stage
    if (this.traceabilityService && traceId) {
      await this.traceabilityService.addStage(traceId, {
        stage: 'PAYMENT_INITIATED', entity_type: 'Payment', entity_id: String(payment._id),
        status: 'SUCCESS', timestamp: new Date(),
        metadata: { paymentId: payment.paymentId, amount: payment.amount, method: paymentMethod },
      });
    }

    // Audit event
    if (this.auditService) {
      await this.auditService.recordEvent({
        eventType: 'USER_ACTION', category: 'financial', severity: 'info',
        entityType: 'Payment', entityId: String(payment._id),
        action: 'PAYMENT_INITIATED', description: `Payment initiated: ${payment.amount} via ${paymentMethod}`,
        actor: { userId }, traceId,
        after: payment.toObject(),
      });
    }

    return payment;
  }

  validatePaymentMethod(method, bankDetails) {
    const validations = {
      NEFT: () => {
        if (!bankDetails?.ifscCode) throw new Error('IFSC code required for NEFT');
        if (!bankDetails?.accountNumber) throw new Error('Account number required for NEFT');
      },
      RTGS: () => {
        if (!bankDetails?.ifscCode) throw new Error('IFSC code required for RTGS');
        if (!bankDetails?.accountNumber) throw new Error('Account number required for RTGS');
        const amt = new Decimal(bankDetails?.amount || 0);
        if (amt.lt(200000)) throw new Error('RTGS minimum is ₹2,00,000');
      },
      UPI: () => {
        if (!bankDetails?.upiId) throw new Error('UPI ID required for UPI');
      },
      IMPS: () => {
        if (!bankDetails?.ifscCode) throw new Error('IFSC code required for IMPS');
        if (!bankDetails?.accountNumber) throw new Error('Account number required for IMPS');
      },
      Cheque: () => {
        if (!bankDetails?.chequeNumber) throw new Error('Cheque number required');
      },
    };

    if (validations[method]) validations[method]();
  }

  // Process payment (simulate gateway callback)
  async processPayment(paymentId, result, userId) {
    return await withTransaction(async (session) => {
      const payment = await Payment.findById(paymentId).session(session);
      if (!payment) throw new Error('Payment not found');
      if (payment.status === 'completed') throw new Error('Payment already completed');

      const { success, transactionId, utrNumber, bankReference, failureReason } = result;

      if (success) {
        payment.status = 'completed';
        payment.bankDetails.transactionId = transactionId;
        payment.bankDetails.utrNumber = utrNumber;
        payment.bankDetails.bankReference = bankReference;
        payment.verifiedBy = userId;
        payment.verifiedAt = new Date();

        // Create journal entry for the payment
        await this.createPaymentJournalEntry(payment, session);

        // Update linked entity
        await this.updateLinkedEntity(payment, session);

      } else {
        payment.markFailed(failureReason || 'Payment gateway rejection');
      }

      await payment.save({ session });

      // Audit
      if (this.auditService) {
        await this.auditService.recordEvent({
          eventType: success ? 'USER_ACTION' : 'SYSTEM_EVENT',
          category: 'financial',
          severity: success ? 'info' : 'warning',
          entityType: 'Payment', entityId: String(payment._id),
          action: success ? 'PAYMENT_COMPLETED' : 'PAYMENT_FAILED',
          description: success
            ? `Payment completed: ${payment.amount} via ${payment.paymentMethod}`
            : `Payment failed: ${failureReason}`,
          actor: { userId },
          before: { status: 'processing' },
          after: { status: payment.status, failureReason },
          traceId: payment.traceId,
        });
      }

      return payment;
    });
  }

  async createPaymentJournalEntry(payment, session) {
    const bankAccount = await ChartOfAccounts.findOne({ code: '1100' }).session(session);
    if (!bankAccount) throw new Error('Bank account not found');

    let receivableAccount, expenseAccount;
    let journalDescription;

    switch (payment.entityType) {
      case 'Invoice':
        receivableAccount = await ChartOfAccounts.findOne({ code: '1200' }).session(session);
        journalDescription = `Payment received for invoice ${payment.entityId}`;
        break;
      case 'Expense':
        expenseAccount = await ChartOfAccounts.findOne({ code: '2100' }).session(session);
        journalDescription = `Payment made for expense ${payment.entityId}`;
        break;
      default:
        receivableAccount = await ChartOfAccounts.findOne({ code: '1200' }).session(session);
        journalDescription = `Payment ${payment.paymentId}`;
    }

    const lines = [];
    if (payment.entityType === 'Invoice') {
      lines.push(
        { account: bankAccount._id, debit: payment.amount, credit: '0', description: journalDescription },
        { account: receivableAccount._id, debit: '0', credit: payment.amount, description: journalDescription }
      );
    } else {
      lines.push(
        { account: expenseAccount?._id || bankAccount._id, debit: payment.amount, credit: '0', description: journalDescription },
        { account: bankAccount._id, debit: '0', credit: payment.amount, description: journalDescription }
      );
    }

    if (this.ledgerService) {
      const journal = await this.ledgerService.createJournalEntry({
        date: new Date(), description: journalDescription, lines,
        source: 'SYSTEM', trace_id: payment.traceId,
      }, payment.initiatedBy);

      await this.ledgerService.validateJournalEntry(journal._id, payment.initiatedBy);
      await this.ledgerService.postJournalEntry(journal._id, payment.initiatedBy);

      payment.journalEntryId = journal._id;
    }
  }

  async updateLinkedEntity(payment, session) {
    if (payment.entityType === 'Invoice') {
      const invoice = await Invoice.findById(payment.entityId).session(session);
      if (invoice) {
        const paid = new Decimal(invoice.amountPaid || 0).plus(new Decimal(payment.amount));
        invoice.amountPaid = paid.toString();
        invoice.payments.push({
          amount: payment.amount, paymentDate: new Date(),
          paymentMethod: payment.paymentMethod, reference: payment.paymentReference,
          journalEntryId: payment.journalEntryId,
        });
        const total = new Decimal(invoice.totalAmount || 0);
        if (paid.gte(total)) invoice.status = 'paid';
        else if (paid.gt(0)) invoice.status = 'partial';
        await invoice.save({ session });
      }
    } else if (payment.entityType === 'Expense') {
      const expense = await Expense.findById(payment.entityId).session(session);
      if (expense) {
        expense.status = 'recorded';
        await expense.save({ session });
      }
    }
  }

  // Payment retry with exponential backoff
  async retryPayment(paymentId, userId) {
    const payment = await Payment.findById(paymentId);
    if (!payment) throw new Error('Payment not found');
    if (!payment.canRetry()) throw new Error('Payment cannot be retried');

    payment.status = 'initiated';
    payment.retryCount += 1;
    payment.lastRetryAt = new Date();
    const delay = Math.pow(2, payment.retryCount) * 60000;
    payment.nextRetryAt = new Date(Date.now() + delay);

    await payment.save();

    if (this.auditService) {
      await this.auditService.recordEvent({
        eventType: 'USER_ACTION', category: 'financial', severity: 'info',
        entityType: 'Payment', entityId: String(payment._id),
        action: 'PAYMENT_RETRY', description: `Payment retry #${payment.retryCount} for ${payment.paymentId}`,
        actor: { userId }, traceId: payment.traceId,
      });
    }

    return payment;
  }

  // Payment reversal
  async reversePayment(paymentId, reason, userId) {
    return await withTransaction(async (session) => {
      const payment = await Payment.findById(paymentId).session(session);
      if (!payment) throw new Error('Payment not found');
      if (payment.status !== 'completed') throw new Error('Only completed payments can be reversed');

      const beforeState = payment.toObject();
      payment.status = 'reversed';
      payment.metadata.reversalReason = reason;
      payment.metadata.reversedBy = userId;
      payment.metadata.reversedAt = new Date();
      await payment.save({ session });

      // Create reversal journal entry
      if (this.ledgerService && payment.journalEntryId) {
        await this.ledgerService.createReversalEntry(payment.journalEntryId, userId, reason);
      }

      // Update linked entity
      if (payment.entityType === 'Invoice') {
        const invoice = await Invoice.findById(payment.entityId).session(session);
        if (invoice) {
          const paid = new Decimal(invoice.amountPaid || 0).minus(new Decimal(payment.amount));
          invoice.amountPaid = paid.toString();
          invoice.payments = invoice.payments.filter(p =>
            String(p.journalEntryId) !== String(payment.journalEntryId)
          );
          if (paid.lte(0)) invoice.status = 'sent';
          else invoice.status = 'partial';
          await invoice.save({ session });
        }
      }

      if (this.auditService) {
        await this.auditService.recordEvent({
          eventType: 'REVERSAL', category: 'financial', severity: 'warning',
          entityType: 'Payment', entityId: String(payment._id),
          action: 'PAYMENT_REVERSED', description: `Payment reversed: ${reason}`,
          actor: { userId }, before: beforeState, after: payment.toObject(),
          traceId: payment.traceId,
        });
      }

      return payment;
    });
  }

  // Bank reconciliation with matching
  async reconcileBankStatement(statementId, matches, userId) {
    return await withTransaction(async (session) => {
      const statement = await BankStatement.findById(statementId).session(session);
      if (!statement) throw new Error('Bank statement not found');

      let matchedCount = 0;
      let unmatchedCount = 0;

      for (const transaction of statement.transactions) {
        const match = matches.find(m => m.transactionIndex === statement.transactions.indexOf(transaction));

        if (match && match.matched) {
          transaction.matched = true;
          if (match.entityType === 'Invoice') {
            transaction.matchedInvoiceId = match.entityId;
          } else if (match.entityType === 'Expense') {
            transaction.matchedExpenseId = match.entityId;
          }
          matchedCount++;
        } else {
          unmatchedCount++;
        }
      }

      statement.reconciliation = {
        matchedExpenses: statement.transactions.filter(t => t.matchedExpenseId).length,
        matchedInvoices: statement.transactions.filter(t => t.matchedInvoiceId).length,
        autoCreatedExpenses: 0,
        journalEntriesCreated: 0,
        reconciledAt: new Date(),
      };
      statement.status = 'completed';

      await statement.save({ session });

      if (this.auditService) {
        await this.auditService.recordEvent({
          eventType: 'RECONCILIATION', category: 'financial', severity: 'info',
          entityType: 'BankStatement', entityId: String(statement._id),
          action: 'BANK_RECONCILIATION', description: `Bank reconciliation: ${matchedCount} matched, ${unmatchedCount} unmatched`,
          actor: { userId },
          after: statement.reconciliation,
        });
      }

      return { statement, matchedCount, unmatchedCount };
    });
  }

  // Auto-match transactions
  async autoMatchTransactions(statementId, userId) {
    const statement = await BankStatement.findById(statementId);
    if (!statement) throw new Error('Bank statement not found');

    const invoices = await Invoice.find({ status: { $in: ['sent', 'partial'] } });
    const expenses = await Expense.find({ status: { $in: ['pending', 'approved'] } });

    const matches = [];

    for (const transaction of statement.transactions) {
      if (transaction.matched) continue;

      const txAmount = new Decimal(transaction.debit || 0).plus(new Decimal(transaction.credit || 0));
      const txDate = new Date(transaction.date);

      // Try to match with invoices
      for (const invoice of invoices) {
        const invoiceAmount = new Decimal(invoice.totalAmount || 0);
        const paid = new Decimal(invoice.amountPaid || 0);
        const outstanding = invoiceAmount.minus(paid);

        if (txAmount.equals(outstanding)) {
          const invoiceDate = new Date(invoice.invoiceDate);
          const daysDiff = Math.abs((txDate - invoiceDate) / (1000 * 60 * 60 * 24));
          if (daysDiff <= 30) {
            matches.push({
              transactionIndex: statement.transactions.indexOf(transaction),
              matched: true, entityType: 'Invoice', entityId: invoice._id,
            });
            break;
          }
        }
      }

      // Try to match with expenses
      if (!matches.find(m => m.transactionIndex === statement.transactions.indexOf(transaction))) {
        for (const expense of expenses) {
          const expenseAmount = new Decimal(expense.totalAmount || 0);
          if (txAmount.equals(expenseAmount)) {
            const expenseDate = new Date(expense.date);
            const daysDiff = Math.abs((txDate - expenseDate) / (1000 * 60 * 60 * 24));
            if (daysDiff <= 7) {
              matches.push({
                transactionIndex: statement.transactions.indexOf(transaction),
                matched: true, entityType: 'Expense', entityId: expense._id,
              });
              break;
            }
          }
        }
      }
    }

    return matches;
  }

  // Get payment status
  async getPaymentStatus(paymentId) {
    const payment = await Payment.findById(paymentId)
      .populate('journalEntryId', 'entryNumber status hash')
      .populate('initiatedBy', 'name email')
      .populate('verifiedBy', 'name email');
    if (!payment) throw new Error('Payment not found');
    return payment;
  }

  // Get all payments with filters
  async getPayments(filters = {}, pagination = {}) {
    const { status, paymentMethod, entityType, dateFrom, dateTo } = filters;
    const { page = 1, limit = 20 } = pagination;

    const query = {};
    if (status) query.status = status;
    if (paymentMethod) query.paymentMethod = paymentMethod;
    if (entityType) query.entityType = entityType;
    if (dateFrom || dateTo) {
      query.createdAt = {};
      if (dateFrom) query.createdAt.$gte = new Date(dateFrom);
      if (dateTo) query.createdAt.$lte = new Date(dateTo);
    }

    const skip = (page - 1) * limit;
    const [payments, total] = await Promise.all([
      Payment.find(query).sort({ createdAt: -1 }).skip(skip).limit(limit)
        .populate('initiatedBy', 'name email'),
      Payment.countDocuments(query),
    ]);

    return { payments, pagination: { page, limit, total, pages: Math.ceil(total / limit) } };
  }

  // Failed payment recovery
  async recoverFailedPayments() {
    const failedPayments = await Payment.find({
      status: 'failed',
      retryCount: { $lt: 3 },
      nextRetryAt: { $lte: new Date() },
    });

    const results = [];
    for (const payment of failedPayments) {
      try {
        await this.retryPayment(payment._id, payment.initiatedBy);
        results.push({ paymentId: payment.paymentId, status: 'retried' });
      } catch (err) {
        results.push({ paymentId: payment.paymentId, status: 'failed', error: err.message });
      }
    }
    return results;
  }
}

export default new BankingService();
