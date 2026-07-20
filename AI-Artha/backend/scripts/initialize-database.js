import mongoose from 'mongoose';
import dotenv from 'dotenv';
import User from '../src/models/User.js';
import ChartOfAccounts from '../src/models/ChartOfAccounts.js';
import JournalEntry from '../src/models/JournalEntry.js';
import Invoice from '../src/models/Invoice.js';
import Expense from '../src/models/Expense.js';
import AccountBalance from '../src/models/AccountBalance.js';
import CompanySettings from '../src/models/CompanySettings.js';
import logger from '../src/config/logger.js';

dotenv.config();

const initializeDatabase = async () => {
  try {
    console.log('🚀 Initializing ARTHA Database...\n');

    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Connected to MongoDB Atlas\n');

    // Drop existing collections (CAUTION: Only for fresh setup)
    const shouldDrop = process.argv.includes('--drop');
    if (shouldDrop) {
      console.log('⚠️  Dropping existing collections...');
      await mongoose.connection.dropDatabase();
      console.log('✅ Database dropped\n');
    }

    // Create collections with indexes
    console.log('📝 Creating collections and indexes...\n');

    // 1. Users Collection
    console.log('1. Users collection...');
    try {
      await User.createIndexes();
      console.log('   ✅ Indexes created');
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }

    // 2. Chart of Accounts
    console.log('2. Chart of Accounts collection...');
    try {
      await ChartOfAccounts.createIndexes();
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }
    
    const defaultAccounts = [
      // Assets
      { code: '1000', name: 'Assets', type: 'Asset', normalBalance: 'debit', description: 'Parent asset account' },
      { code: '1010', name: 'Cash', type: 'Asset', normalBalance: 'debit', subtype: 'Current Asset' },
      { code: '1020', name: 'Bank Account', type: 'Asset', normalBalance: 'debit', subtype: 'Current Asset' },
      { code: '1100', name: 'Accounts Receivable', type: 'Asset', normalBalance: 'debit', subtype: 'Current Asset' },
      { code: '1500', name: 'Inventory', type: 'Asset', normalBalance: 'debit', subtype: 'Current Asset' },
      { code: '1800', name: 'Equipment', type: 'Asset', normalBalance: 'debit', subtype: 'Fixed Asset' },
      
      // Liabilities
      { code: '2000', name: 'Liabilities', type: 'Liability', normalBalance: 'credit', description: 'Parent liability account' },
      { code: '2100', name: 'Accounts Payable', type: 'Liability', normalBalance: 'credit', subtype: 'Current Liability' },
      { code: '2200', name: 'Tax Payable', type: 'Liability', normalBalance: 'credit', subtype: 'Current Liability' },
      { code: '2300', name: 'GST Payable', type: 'Liability', normalBalance: 'credit', subtype: 'Current Liability' },
      { code: '2400', name: 'TDS Payable', type: 'Liability', normalBalance: 'credit', subtype: 'Current Liability' },
      
      // Equity
      { code: '3000', name: 'Equity', type: 'Equity', normalBalance: 'credit', description: 'Parent equity account' },
      { code: '3100', name: "Owner's Capital", type: 'Equity', normalBalance: 'credit' },
      { code: '3200', name: 'Retained Earnings', type: 'Equity', normalBalance: 'credit' },
      
      // Income
      { code: '4000', name: 'Income', type: 'Income', normalBalance: 'credit', description: 'Parent income account' },
      { code: '4100', name: 'Sales Revenue', type: 'Income', normalBalance: 'credit' },
      { code: '4200', name: 'Service Revenue', type: 'Income', normalBalance: 'credit' },
      { code: '4900', name: 'Other Income', type: 'Income', normalBalance: 'credit' },
      
      // Expenses
      { code: '6000', name: 'Expenses', type: 'Expense', normalBalance: 'debit', description: 'Parent expense account' },
      { code: '6100', name: 'Rent Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6200', name: 'Utilities Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6300', name: 'Office Supplies', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6400', name: 'Salaries Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6500', name: 'Marketing Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6600', name: 'Insurance Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6700', name: 'Professional Services', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6800', name: 'Travel Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
      { code: '6900', name: 'Miscellaneous Expense', type: 'Expense', normalBalance: 'debit', subtype: 'Operating Expense' },
    ];

    for (const account of defaultAccounts) {
      await ChartOfAccounts.findOneAndUpdate(
        { code: account.code },
        account,
        { upsert: true, new: true }
      );
    }
    console.log(`   ✅ ${defaultAccounts.length} accounts created`);

    // 3. Journal Entries
    console.log('3. Journal Entries collection...');
    try {
      await JournalEntry.createIndexes();
      console.log('   ✅ Indexes created');
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }

    // 4. Invoices
    console.log('4. Invoices collection...');
    try {
      await Invoice.createIndexes();
      console.log('   ✅ Indexes created');
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }

    // 5. Expenses
    console.log('5. Expenses collection...');
    try {
      await Expense.createIndexes();
      console.log('   ✅ Indexes created');
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }

    // 6. Account Balances
    console.log('6. Account Balances collection...');
    try {
      await AccountBalance.createIndexes();
      console.log('   ✅ Indexes created');
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }

    // 7. Company Settings
    console.log('7. Company Settings collection...');
    try {
      await CompanySettings.createIndexes();
    } catch (error) {
      console.log('   ℹ️  Indexes already exist');
    }
    
    const defaultSettings = {
      companyName: 'ARTHA Finance',
      address: {
        street: '',
        city: '',
        state: '',
        zipCode: '',
        country: 'India'
      },
      gstin: '',
      pan: '',
      tan: '',
      financialYearStart: new Date(new Date().getFullYear(), 3, 1), // April 1st
      currency: 'INR',
      taxSettings: {
        defaultGSTRate: 18,
        enableGST: true,
        enableTDS: true
      }
    };

    await CompanySettings.findOneAndUpdate(
      {},
      defaultSettings,
      { upsert: true, new: true }
    );
    console.log('   ✅ Default settings created');

    // 8. Create Admin User
    console.log('\n8. Creating admin user...');
    const adminExists = await User.findOne({ email: process.env.ADMIN_EMAIL || 'admin@artha.local' });
    
    if (!adminExists) {
      await User.create({
        name: 'Admin User',
        email: process.env.ADMIN_EMAIL || 'admin@artha.local',
        password: process.env.ADMIN_PASSWORD || 'Admin@123456',
        role: 'admin'
      });
      console.log('   ✅ Admin user created');
      console.log(`   📧 Email: ${process.env.ADMIN_EMAIL || 'admin@artha.local'}`);
      console.log(`   🔑 Password: ${process.env.ADMIN_PASSWORD || 'Admin@123456'}`);
    } else {
      console.log('   ℹ️  Admin user already exists');
    }

    // Summary
    console.log('\n📊 Database Initialization Summary:');
    console.log('=====================================');
    const collections = await mongoose.connection.db.listCollections().toArray();
    console.log(`✅ Collections created: ${collections.length}`);
    collections.forEach(col => console.log(`   - ${col.name}`));

    console.log('\n✅ Database initialized successfully!');
    console.log('\n🚀 You can now start the application.');
    console.log('   Backend: npm run dev');
    console.log('   Frontend: npm run dev\n');

  } catch (error) {
    console.error('❌ Initialization failed:', error);
    process.exit(1);
  } finally {
    await mongoose.connection.close();
    console.log('✅ Database connection closed');
    process.exit(0);
  }
};

// Run initialization
console.log('ARTHA Database Initialization');
console.log('=============================\n');

if (process.argv.includes('--drop')) {
  console.log('⚠️  WARNING: This will DROP all existing data!');
  console.log('Press Ctrl+C to cancel, or wait 5 seconds to continue...\n');
  setTimeout(initializeDatabase, 5000);
} else {
  initializeDatabase();
}
