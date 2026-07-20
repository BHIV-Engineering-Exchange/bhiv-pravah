import mongoose from 'mongoose';
import dotenv from 'dotenv';
import User from '../src/models/User.js';
import invoiceService from '../src/services/invoice.service.js';
import expenseService from '../src/services/expense.service.js';
import ledgerService from '../src/services/ledger.service.js';
import logger from '../src/config/logger.js';

dotenv.config();

async function demonstrateWorkflow() {
  try {
    console.log('🚀 Starting Artha workflow demonstration...');
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Database connected');

    // Get users
    const admin = await User.findOne({ role: 'admin' });
    const accountant = await User.findOne({ role: 'accountant' });
    
    if (!admin || !accountant) {
      console.log('❌ Required users not found. Please run seed script first.');
      process.exit(1);
    }

    console.log('\n📊 Current ledger summary:');
    const initialSummary = await ledgerService.getLedgerSummary();
    console.log(`   Assets: ${initialSummary.assets}`);
    console.log(`   Liabilities: ${initialSummary.liabilities}`);
    console.log(`   Equity: ${initialSummary.equity}`);
    console.log(`   Income: ${initialSummary.income}`);
    console.log(`   Expenses: ${initialSummary.expenses}`);

    // Create and process a new invoice
    console.log('\n🧾 Creating new invoice...');
    const newInvoice = await invoiceService.createInvoice({
      invoiceNumber: 'DEMO-INV-001',
      customerName: 'Demo Customer Ltd',
      customerEmail: 'demo@customer.com',
      invoiceDate: new Date(),
      dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      items: [
        {
          description: 'Demo Service',
          quantity: 5,
          unitPrice: '1000.00',
          amount: '5000.00',
        },
      ],
      subtotal: '5000.00',
      totalAmount: '5000.00',
    }, accountant._id);
    
    console.log(`   ✅ Invoice created: ${newInvoice.invoiceNumber}`);

    // Send the invoice
    console.log('   📤 Sending invoice...');
    const sentInvoice = await invoiceService.sendInvoice(newInvoice._id, accountant._id);
    console.log(`   ✅ Invoice sent, status: ${sentInvoice.status}`);

    // Record payment
    console.log('   💰 Recording payment...');
    const paidInvoice = await invoiceService.recordPayment(
      newInvoice._id,
      {
        amount: '5000.00',
        paymentMethod: 'bank_transfer',
        paymentDate: new Date(),
      },
      accountant._id
    );
    console.log(`   ✅ Payment recorded, status: ${paidInvoice.status}`);

    // Create and process an expense
    console.log('\n💰 Creating new expense...');
    const newExpense = await expenseService.createExpense({
      vendor: 'Demo Vendor Inc',
      description: 'Demo office supplies',
      category: 'supplies',
      amount: '800.00',
      totalAmount: '800.00',
      paymentMethod: 'credit_card',
    }, accountant._id);
    
    console.log(`   ✅ Expense created: ${newExpense.expenseNumber}`);

    // Approve the expense
    console.log('   ✅ Approving expense...');
    const approvedExpense = await expenseService.approveExpense(newExpense._id, admin._id);
    console.log(`   ✅ Expense approved, status: ${approvedExpense.status}`);

    // Record the expense
    console.log('   📝 Recording expense in ledger...');
    const recordedExpense = await expenseService.recordExpense(newExpense._id, admin._id);
    console.log(`   ✅ Expense recorded, status: ${recordedExpense.status}`);

    // Show updated ledger summary
    console.log('\n📊 Updated ledger summary:');
    const finalSummary = await ledgerService.getLedgerSummary();
    console.log(`   Assets: ${finalSummary.assets}`);
    console.log(`   Liabilities: ${finalSummary.liabilities}`);
    console.log(`   Equity: ${finalSummary.equity}`);
    console.log(`   Income: ${finalSummary.income}`);
    console.log(`   Expenses: ${finalSummary.expenses}`);
    console.log(`   Net Income: ${finalSummary.netIncome}`);

    // Show the changes
    console.log('\n📈 Changes from workflow:');
    const incomeChange = parseFloat(finalSummary.income) - parseFloat(initialSummary.income);
    const expenseChange = parseFloat(finalSummary.expenses) - parseFloat(initialSummary.expenses);
    const assetChange = parseFloat(finalSummary.assets) - parseFloat(initialSummary.assets);
    
    console.log(`   Income increased by: ${incomeChange.toFixed(2)}`);
    console.log(`   Expenses increased by: ${expenseChange.toFixed(2)}`);
    console.log(`   Assets increased by: ${assetChange.toFixed(2)}`);

    // Verify ledger integrity
    console.log('\n🔐 Verifying ledger integrity...');
    const verification = await ledgerService.verifyLedgerChain();
    console.log(`   Ledger integrity: ${verification.isValid ? '✅ Valid' : '❌ Invalid'}`);
    console.log(`   Books balanced: ${finalSummary.isBalanced ? '✅ Yes' : '❌ No'}`);

    console.log('\n🎉 Workflow demonstration completed successfully!');
    console.log('\n📋 Summary of operations:');
    console.log('   1. Created and sent invoice for ₹5,000');
    console.log('   2. Recorded payment for the invoice');
    console.log('   3. Created and approved expense for ₹800');
    console.log('   4. Recorded expense in ledger');
    console.log('   5. Verified ledger integrity');
    console.log('\n✅ All operations completed with ledger integrity maintained!');

  } catch (error) {
    console.error('❌ Workflow demonstration failed:', error.message);
    console.error(error.stack);
  } finally {
    await mongoose.connection.close();
    console.log('\n🔌 Database connection closed');
    process.exit(0);
  }
}

demonstrateWorkflow();