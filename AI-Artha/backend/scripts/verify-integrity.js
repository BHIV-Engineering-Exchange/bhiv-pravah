import mongoose from 'mongoose';
import dotenv from 'dotenv';
import Invoice from '../src/models/Invoice.js';
import JournalEntry from '../src/models/JournalEntry.js';
import ChartOfAccounts from '../src/models/ChartOfAccounts.js';
import Decimal from 'decimal.js';

dotenv.config();

async function verifyIntegrity() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB\n');

    // 1. Check Invoices
    console.log('=== INVOICE VERIFICATION ===');
    const invoices = await Invoice.find({});
    console.log(`Total Invoices: ${invoices.length}`);
    
    const sentInvoices = invoices.filter(inv => inv.status === 'sent');
    const paidInvoices = invoices.filter(inv => inv.status === 'paid');
    
    console.log(`- Sent: ${sentInvoices.length}`);
    console.log(`- Paid: ${paidInvoices.length}`);
    
    let totalRevenue = new Decimal(0);
    let totalReceivable = new Decimal(0);
    
    invoices.forEach(inv => {
      if (inv.status === 'sent' || inv.status === 'paid' || inv.status === 'partial') {
        totalRevenue = totalRevenue.plus(inv.totalAmount || 0);
        const due = new Decimal(inv.totalAmount || 0).minus(inv.amountPaid || 0);
        if (due.greaterThan(0)) {
          totalReceivable = totalReceivable.plus(due);
        }
      }
    });
    
    console.log(`Total Revenue: ₹${totalRevenue.toFixed(2)}`);
    console.log(`Total Receivable: ₹${totalReceivable.toFixed(2)}\n`);

    // 2. Check Journal Entries
    console.log('=== JOURNAL ENTRY VERIFICATION ===');
    const journalEntries = await JournalEntry.find({ status: 'posted' });
    console.log(`Total Posted Entries: ${journalEntries.length}`);
    
    const invoiceEntries = journalEntries.filter(je => 
      je.description?.toLowerCase().includes('invoice') || 
      je.reference?.startsWith('INV-')
    );
    console.log(`Invoice-related Entries: ${invoiceEntries.length}\n`);

    // 3. Check Account Balances
    console.log('=== ACCOUNT BALANCE VERIFICATION ===');
    const accounts = await ChartOfAccounts.find({ isActive: true });
    
    const accountBalances = {};
    
    journalEntries.forEach(entry => {
      entry.lines.forEach(line => {
        const accountId = line.account.toString();
        if (!accountBalances[accountId]) {
          accountBalances[accountId] = {
            debit: new Decimal(0),
            credit: new Decimal(0),
          };
        }
        accountBalances[accountId].debit = accountBalances[accountId].debit.plus(line.debit || 0);
        accountBalances[accountId].credit = accountBalances[accountId].credit.plus(line.credit || 0);
      });
    });

    // Find key accounts
    const arAccount = accounts.find(acc => acc.code === '1100');
    const revenueAccount = accounts.find(acc => acc.code === '4000');
    const cashAccount = accounts.find(acc => acc.code === '1010');
    
    if (arAccount && accountBalances[arAccount._id.toString()]) {
      const arBalance = accountBalances[arAccount._id.toString()];
      const arNet = arBalance.debit.minus(arBalance.credit);
      console.log(`Accounts Receivable (1100): ₹${arNet.toFixed(2)}`);
    } else {
      console.log('Accounts Receivable (1100): ₹0.00');
    }
    
    if (revenueAccount && accountBalances[revenueAccount._id.toString()]) {
      const revBalance = accountBalances[revenueAccount._id.toString()];
      const revNet = revBalance.credit.minus(revBalance.debit);
      console.log(`Revenue (4000): ₹${revNet.toFixed(2)}`);
    } else {
      console.log('Revenue (4000): ₹0.00');
    }
    
    if (cashAccount && accountBalances[cashAccount._id.toString()]) {
      const cashBalance = accountBalances[cashAccount._id.toString()];
      const cashNet = cashBalance.debit.minus(cashBalance.credit);
      console.log(`Cash (1010): ₹${cashNet.toFixed(2)}\n`);
    } else {
      console.log('Cash (1010): ₹0.00\n');
    }

    // 4. Verify Accounting Equation
    console.log('=== ACCOUNTING EQUATION VERIFICATION ===');
    let totalDebits = new Decimal(0);
    let totalCredits = new Decimal(0);
    
    Object.values(accountBalances).forEach(bal => {
      totalDebits = totalDebits.plus(bal.debit);
      totalCredits = totalCredits.plus(bal.credit);
    });
    
    console.log(`Total Debits: ₹${totalDebits.toFixed(2)}`);
    console.log(`Total Credits: ₹${totalCredits.toFixed(2)}`);
    console.log(`Balanced: ${totalDebits.equals(totalCredits) ? '✓ YES' : '✗ NO'}\n`);

    // 5. GST Verification
    console.log('=== GST VERIFICATION ===');
    let totalGST = new Decimal(0);
    
    invoices.forEach(inv => {
      if (inv.status === 'sent' || inv.status === 'paid' || inv.status === 'partial') {
        totalGST = totalGST.plus(inv.taxAmount || 0);
      }
    });
    
    console.log(`Total GST Collected: ₹${totalGST.toFixed(2)}\n`);

    // 6. Integration Check
    console.log('=== INTEGRATION STATUS ===');
    const issues = [];
    
    // Check if sent invoices have journal entries
    for (const invoice of sentInvoices) {
      const hasEntry = journalEntries.some(je => 
        je.reference === invoice.invoiceNumber || 
        je.description?.includes(invoice.invoiceNumber)
      );
      if (!hasEntry) {
        issues.push(`Invoice ${invoice.invoiceNumber} (sent) has no journal entry`);
      }
    }
    
    // Check if paid invoices have payment entries
    for (const invoice of paidInvoices) {
      const hasPaymentEntry = journalEntries.some(je => 
        je.description?.includes(invoice.invoiceNumber) && 
        je.description?.toLowerCase().includes('payment')
      );
      if (!hasPaymentEntry) {
        issues.push(`Invoice ${invoice.invoiceNumber} (paid) has no payment entry`);
      }
    }
    
    if (issues.length === 0) {
      console.log('✓ All integrations working correctly');
    } else {
      console.log('✗ Issues found:');
      issues.forEach(issue => console.log(`  - ${issue}`));
    }
    
    console.log('\n=== SUMMARY ===');
    console.log(`Invoices: ${invoices.length}`);
    console.log(`Journal Entries: ${journalEntries.length}`);
    console.log(`Accounts: ${accounts.length}`);
    console.log(`Integrity: ${issues.length === 0 && totalDebits.equals(totalCredits) ? '✓ PASS' : '✗ FAIL'}`);

    process.exit(0);
  } catch (error) {
    console.error('Verification error:', error);
    process.exit(1);
  }
}

verifyIntegrity();
