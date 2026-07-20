import mongoose from 'mongoose';
import dotenv from 'dotenv';
import User from '../src/models/User.js';
import Invoice from '../src/models/Invoice.js';
import Expense from '../src/models/Expense.js';
import ChartOfAccounts from '../src/models/ChartOfAccounts.js';
import JournalEntry from '../src/models/JournalEntry.js';
import AccountBalance from '../src/models/AccountBalance.js';
import ledgerService from '../src/services/ledger.service.js';

dotenv.config();

async function verifySeedData() {
  try {
    console.log('🔍 Verifying seed data...');
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Database connected');

    // Verify users
    console.log('\n👥 Checking users...');
    const users = await User.find({});
    console.log(`   Found ${users.length} users`);
    
    const admin = await User.findOne({ role: 'admin' });
    const accountant = await User.findOne({ role: 'accountant' });
    const viewer = await User.findOne({ role: 'viewer' });
    
    console.log(`   ✅ Admin: ${admin ? admin.email : 'Not found'}`);
    console.log(`   ✅ Accountant: ${accountant ? accountant.email : 'Not found'}`);
    console.log(`   ✅ Viewer: ${viewer ? viewer.email : 'Not found'}`);

    // Verify chart of accounts
    console.log('\n📊 Checking chart of accounts...');
    const accounts = await ChartOfAccounts.find({});
    console.log(`   Found ${accounts.length} accounts`);
    
    const accountsByType = await ChartOfAccounts.aggregate([
      { $group: { _id: '$type', count: { $sum: 1 } } },
      { $sort: { _id: 1 } }
    ]);
    
    accountsByType.forEach(({ _id, count }) => {
      console.log(`   ${_id}: ${count} accounts`);
    });

    // Verify journal entries
    console.log('\n📝 Checking journal entries...');
    const entries = await JournalEntry.find({});
    console.log(`   Found ${entries.length} journal entries`);
    
    const entriesByStatus = await JournalEntry.aggregate([
      { $group: { _id: '$status', count: { $sum: 1 } } },
      { $sort: { _id: 1 } }
    ]);
    
    entriesByStatus.forEach(({ _id, count }) => {
      console.log(`   ${_id}: ${count} entries`);
    });

    // Verify invoices
    console.log('\n🧾 Checking invoices...');
    const invoices = await Invoice.find({});
    console.log(`   Found ${invoices.length} invoices`);
    
    if (invoices.length > 0) {
      const sampleInvoice = invoices[0];
      console.log(`   Sample invoice: ${sampleInvoice.invoiceNumber}`);
      console.log(`   Customer: ${sampleInvoice.customerName}`);
      console.log(`   Status: ${sampleInvoice.status}`);
      console.log(`   Total: ${sampleInvoice.totalAmount}`);
    }

    // Verify expenses
    console.log('\n💰 Checking expenses...');
    const expenses = await Expense.find({});
    console.log(`   Found ${expenses.length} expenses`);
    
    if (expenses.length > 0) {
      const sampleExpense = expenses[0];
      console.log(`   Sample expense: ${sampleExpense.expenseNumber}`);
      console.log(`   Vendor: ${sampleExpense.vendor}`);
      console.log(`   Status: ${sampleExpense.status}`);
      console.log(`   Total: ${sampleExpense.totalAmount}`);
    }

    // Verify account balances
    console.log('\n💳 Checking account balances...');
    const balances = await AccountBalance.find({})
      .populate('account', 'code name type');
    
    console.log(`   Found ${balances.length} account balances`);
    
    const significantBalances = balances.filter(b => 
      Math.abs(parseFloat(b.balance)) > 0
    );
    
    console.log('\n   Significant balances:');
    significantBalances.forEach(balance => {
      console.log(`   ${balance.account.code} - ${balance.account.name}: ${balance.balance}`);
    });

    // Verify ledger integrity
    console.log('\n🔐 Verifying ledger integrity...');
    const verification = await ledgerService.verifyLedgerChain();
    
    if (verification.isValid) {
      console.log('   ✅ Ledger chain is valid');
      console.log(`   Total entries verified: ${verification.totalEntries}`);
    } else {
      console.log('   ❌ Ledger chain has issues:');
      verification.errors.forEach(error => {
        console.log(`   - ${error.entryNumber}: ${error.error}`);
      });
    }

    // Get ledger summary
    console.log('\n📈 Ledger summary...');
    const summary = await ledgerService.getLedgerSummary();
    
    console.log(`   Assets: ${summary.assets}`);
    console.log(`   Liabilities: ${summary.liabilities}`);
    console.log(`   Equity: ${summary.equity}`);
    console.log(`   Income: ${summary.income}`);
    console.log(`   Expenses: ${summary.expenses}`);
    console.log(`   Net Income: ${summary.netIncome}`);
    console.log(`   Balanced: ${summary.isBalanced ? '✅' : '❌'}`);
    
    if (!summary.isBalanced) {
      console.log(`   Balance Difference: ${summary.balanceDifference}`);
    }

    // Check data relationships
    console.log('\n🔗 Checking data relationships...');
    
    // Invoice to journal entry relationship
    const invoiceWithJournal = await Invoice.findOne({})
      .populate('createdBy');
    
    if (invoiceWithJournal) {
      const relatedJournalEntry = await JournalEntry.findOne({
        reference: invoiceWithJournal.invoiceNumber
      });
      
      if (relatedJournalEntry) {
        console.log('   ✅ Invoice to journal entry relationship verified');
      } else {
        console.log('   ❌ Invoice to journal entry relationship missing');
      }
    }
    
    // Expense to journal entry relationship
    const expenseWithJournal = await Expense.findOne({ status: 'recorded' })
      .populate('journalEntryId');
    
    if (expenseWithJournal && expenseWithJournal.journalEntryId) {
      console.log('   ✅ Expense to journal entry relationship verified');
    } else {
      console.log('   ❌ Expense to journal entry relationship missing');
    }

    console.log('\n🎉 Seed data verification completed!');
    console.log('\n📊 Summary:');
    console.log(`   Users: ${users.length}`);
    console.log(`   Accounts: ${accounts.length}`);
    console.log(`   Journal Entries: ${entries.length}`);
    console.log(`   Invoices: ${invoices.length}`);
    console.log(`   Expenses: ${expenses.length}`);
    console.log(`   Account Balances: ${balances.length}`);
    console.log(`   Ledger Integrity: ${verification.isValid ? 'Valid' : 'Invalid'}`);
    console.log(`   Books Balanced: ${summary.isBalanced ? 'Yes' : 'No'}`);

  } catch (error) {
    console.error('❌ Verification failed:', error.message);
    console.error(error.stack);
  } finally {
    await mongoose.connection.close();
    console.log('\n🔌 Database connection closed');
    process.exit(0);
  }
}

verifySeedData();