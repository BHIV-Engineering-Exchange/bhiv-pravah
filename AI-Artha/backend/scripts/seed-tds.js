import mongoose from 'mongoose';
import dotenv from 'dotenv';
import TDSEntry from '../src/models/TDSEntry.js';
import User from '../src/models/User.js';

dotenv.config();

const sampleTDSEntries = [
  {
    transactionDate: new Date('2026-02-05'),
    deductee: {
      name: 'ABC Consultants',
      pan: 'ABCDE1234F',
      address: 'Mumbai, Maharashtra',
    },
    section: '194J',
    nature: 'Professional Fees',
    paymentAmount: '100000',
    tdsRate: 10,
    tdsAmount: '10000',
    status: 'pending',
    quarter: 'Q4',
    financialYear: 'FY2025-26',
  },
  {
    transactionDate: new Date('2026-02-10'),
    deductee: {
      name: 'XYZ Contractors',
      pan: 'XYZAB5678C',
      address: 'Delhi',
    },
    section: '194C',
    nature: 'Contractor Payment',
    paymentAmount: '250000',
    tdsRate: 2,
    tdsAmount: '5000',
    status: 'pending',
    quarter: 'Q4',
    financialYear: 'FY2025-26',
  },
  {
    transactionDate: new Date('2026-02-01'),
    deductee: {
      name: 'Metro Properties',
      pan: 'METRO9012P',
      address: 'Bangalore, Karnataka',
    },
    section: '194I',
    nature: 'Rent',
    paymentAmount: '100000',
    tdsRate: 10,
    tdsAmount: '10000',
    status: 'pending',
    quarter: 'Q4',
    financialYear: 'FY2025-26',
  },
  {
    transactionDate: new Date('2026-02-08'),
    deductee: {
      name: 'Sales Agent Co.',
      pan: 'SALES3456A',
      address: 'Pune, Maharashtra',
    },
    section: '194H',
    nature: 'Commission',
    paymentAmount: '75000',
    tdsRate: 5,
    tdsAmount: '3750',
    status: 'pending',
    quarter: 'Q4',
    financialYear: 'FY2025-26',
  },
  {
    transactionDate: new Date('2026-01-15'),
    deductee: {
      name: 'Finance Corp',
      pan: 'FINCO7890F',
      address: 'Chennai, Tamil Nadu',
    },
    section: '194A',
    nature: 'Interest Payment',
    paymentAmount: '200000',
    tdsRate: 10,
    tdsAmount: '20000',
    status: 'deposited',
    challanNumber: 'CHL202602050001',
    challanDate: new Date('2026-02-05'),
    quarter: 'Q4',
    financialYear: 'FY2025-26',
  },
  {
    transactionDate: new Date('2026-01-20'),
    deductee: {
      name: 'Tech Solutions Ltd',
      pan: 'TECHS1234T',
      address: 'Hyderabad, Telangana',
    },
    section: '194J',
    nature: 'Technical Services',
    paymentAmount: '150000',
    tdsRate: 10,
    tdsAmount: '15000',
    status: 'deposited',
    challanNumber: 'CHL202602060001',
    challanDate: new Date('2026-02-06'),
    quarter: 'Q4',
    financialYear: 'FY2025-26',
  },
];

async function seedTDS() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB');

    // Get admin user
    const adminUser = await User.findOne({ role: 'admin' });
    if (!adminUser) {
      console.error('Admin user not found. Please run seed script first.');
      process.exit(1);
    }

    // Clear existing TDS entries
    await TDSEntry.deleteMany({});
    console.log('Cleared existing TDS entries');

    // Insert TDS entries one by one to trigger pre-save hook
    let count = 0;
    for (const entryData of sampleTDSEntries) {
      await TDSEntry.create({
        ...entryData,
        createdBy: adminUser._id,
      });
      count++;
    }

    console.log(`✓ Inserted ${count} TDS entries`);
    console.log('\n✓ TDS seeding completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('Seeding error:', error);
    process.exit(1);
  }
}

seedTDS();
