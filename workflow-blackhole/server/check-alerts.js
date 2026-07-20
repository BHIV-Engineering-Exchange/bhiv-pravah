require('dotenv').config();
const mongoose = require('mongoose');
const MonitoringAlert = require('./models/MonitoringAlert');

async function checkAlerts() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ Connected to MongoDB\n');

    const total = await MonitoringAlert.countDocuments();
    console.log(`Total alerts in database: ${total}\n`);

    // Get alert type breakdown
    const alertTypes = await MonitoringAlert.aggregate([
      { $group: { _id: '$alert_type', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]);

    console.log('Alert types breakdown:');
    alertTypes.forEach(type => {
      console.log(`  - ${type._id}: ${type.count} alerts`);
    });

    console.log('\n--- Recent 5 Alerts ---');
    const recentAlerts = await MonitoringAlert.find()
      .sort({ timestamp: -1 })
      .limit(5);

    recentAlerts.forEach((alert, i) => {
      console.log(`\n${i + 1}. ${alert.alert_type.toUpperCase()}`);
      console.log(`   Title: ${alert.title}`);
      console.log(`   Severity: ${alert.severity}`);
      console.log(`   Status: ${alert.status}`);
      console.log(`   Employee ID: ${alert.employee}`);
      console.log(`   Timestamp: ${alert.timestamp}`);
      if (alert.data && alert.data.website_url) {
        console.log(`   Website: ${alert.data.website_url}`);
      }
    });

    await mongoose.connection.close();
    console.log('\n✅ Done');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

checkAlerts();
