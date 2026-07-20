const mongoose = require('mongoose');
const Aim = require('./models/Aim');
require('dotenv').config();

async function cleanupDefaultAims() {
  try {
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB');

    // Find and delete all default aims
    const result = await Aim.deleteMany({
      aims: { $regex: /Daily work objectives - to be updated|Daily objectives.*Please update/i }
    });

    console.log(`🧹 Cleaned up ${result.deletedCount} default aims`);

    // Also find aims with generic content that might be shared
    const genericAims = await Aim.find({
      aims: { $regex: /^(unidq|test|daily|work|objectives?)$/i }
    }).populate('user', 'name email');

    if (genericAims.length > 0) {
      console.log(`⚠️  Found ${genericAims.length} potentially generic aims:`);
      genericAims.forEach(aim => {
        console.log(`- User: ${aim.user?.name}, Aim: "${aim.aims}", Date: ${aim.date}`);
      });
      
      console.log('\n🔧 You may want to manually review these aims');
    }

    await mongoose.disconnect();
    console.log('✅ Cleanup completed');
  } catch (error) {
    console.error('❌ Cleanup error:', error);
    process.exit(1);
  }
}

cleanupDefaultAims();