const mongoose = require('mongoose');
const User = require('../models/User');
const Salary = require('../models/Salary');
require('dotenv').config();

const setDefaultSalaries = async () => {
  try {
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/infiverse');
    console.log('Connected to MongoDB');

    // Get all users
    const users = await User.find({});
    console.log(`Found ${users.length} users`);

    let created = 0;
    let updated = 0;
    let skipped = 0;

    for (const user of users) {
      try {
        // Check if salary record already exists
        const existingSalary = await Salary.findOne({ user: user._id });

        if (existingSalary) {
          console.log(`Salary already exists for ${user.name} (${user.email})`);
          skipped++;
          continue;
        }

        // Create new salary record
        const newSalary = new Salary({
          user: user._id,
          baseSalary: 8000,
          currency: 'INR',
          salaryType: 'Monthly',
          payGrade: 'B1', // Default pay grade
          joiningDate: user.createdAt || new Date(), // Use user creation date or current date
          allowances: [
            {
              type: 'Basic',
              amount: 8000,
              percentage: 100,
              description: 'Base salary',
              isRecurring: true
            }
          ],
          deductions: [
            {
              type: 'Tax',
              amount: 800,
              percentage: 10,
              description: 'Income tax',
              isRecurring: true
            }
          ],
          effectiveDate: new Date(),
          isActive: true,
          createdBy: user._id, // Self-created for initial setup
          approvedBy: user._id,
          approvalDate: new Date(),
          approvalStatus: 'Approved'
        });

        await newSalary.save();
        console.log(`✅ Created salary record for ${user.name} (${user.email}) - ₹8,000/month`);
        created++;

      } catch (userError) {
        console.error(`❌ Error creating salary for ${user.name}:`, userError.message);
      }
    }

    console.log('\n📊 Summary:');
    console.log(`✅ Created: ${created} salary records`);
    console.log(`⏭️  Skipped: ${skipped} existing records`);
    console.log(`📝 Updated: ${updated} records`);
    console.log(`👥 Total users: ${users.length}`);

    console.log('\n🎉 Default salaries setup completed!');

  } catch (error) {
    console.error('❌ Error setting up default salaries:', error);
  } finally {
    await mongoose.disconnect();
    console.log('Disconnected from MongoDB');
    process.exit(0);
  }
};

// Run the script
if (require.main === module) {
  console.log('🚀 Setting up default salaries for all users...\n');
  setDefaultSalaries();
}

module.exports = setDefaultSalaries;
