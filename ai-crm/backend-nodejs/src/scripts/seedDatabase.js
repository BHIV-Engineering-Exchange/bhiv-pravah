import mongoose from 'mongoose';
import dotenv from 'dotenv';
import User from '../models/User.js';
import Product from '../models/Product.js';
import { USER_ROLES } from '../config/constants.js';

dotenv.config();

const seedDatabase = async () => {
  try {
    console.log('🌱 Starting database seed...');

    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URL);
    console.log('✅ Connected to MongoDB');

    // Clear existing data (optional - comment out if you want to keep existing data)
    // await User.deleteMany({});
    // await Product.deleteMany({});
    // console.log('🗑️  Cleared existing data');

    // Check if admin already exists
    const existingAdmin = await User.findOne({ role: USER_ROLES.ADMIN });
    
    let adminUser;
    if (!existingAdmin) {
      // Create admin user
      adminUser = await User.create({
        name: process.env.ADMIN_NAME || 'System Administrator',
        email: process.env.ADMIN_EMAIL || 'admin@company.com',
        password: process.env.ADMIN_PASSWORD || 'Admin@123456',
        role: USER_ROLES.ADMIN,
        isActive: true
      });
      console.log('✅ Admin user created');
      console.log(`📧 Email: ${adminUser.email}`);
      console.log(`🔑 Password: ${process.env.ADMIN_PASSWORD || 'Admin@123456'}`);
    } else {
      adminUser = existingAdmin;
      console.log('ℹ️  Admin user already exists');
    }

    // Create sample manager
    const existingManager = await User.findOne({ role: USER_ROLES.MANAGER });
    if (!existingManager) {
      await User.create({
        name: 'John Manager',
        email: 'manager@company.com',
        password: 'Manager@123',
        role: USER_ROLES.MANAGER,
        isActive: true,
        createdBy: adminUser._id
      });
      console.log('✅ Sample manager created (manager@company.com / Manager@123)');
    }

    // Create sample customers
    const existingCustomer = await User.findOne({ role: USER_ROLES.CUSTOMER });
    if (!existingCustomer) {
      await User.create([
        {
          name: 'Raj Store',
          email: 'customer1@example.com',
          password: 'Customer@123',
          role: USER_ROLES.CUSTOMER,
          shopDetails: {
            shopName: 'Raj General Store',
            address: '123 Main Street, Mumbai',
            phone: '+91 98765 43210',
            gstNumber: 'GST123456789'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Sharma Traders',
          email: 'customer2@example.com',
          password: 'Customer@123',
          role: USER_ROLES.CUSTOMER,
          shopDetails: {
            shopName: 'Sharma Wholesale',
            address: '456 Market Road, Delhi',
            phone: '+91 98765 43211',
            gstNumber: 'GST987654321'
          },
          isActive: true,
          createdBy: adminUser._id
        }
      ]);
      console.log('✅ Sample customers created');
    }

    // Create sample products
    const existingProducts = await Product.countDocuments();
    if (existingProducts === 0) {
      await Product.create([
        {
          name: 'Rice - Basmati Premium',
          sku: 'RICE-001',
          description: 'Premium quality Basmati rice',
          category: 'Grains',
          costPrice: 80,
          sellingPrice: 100,
          stockQuantity: 500,
          minThreshold: 100,
          unit: 'kg',
          supplier: {
            name: 'Rice Supplies India',
            email: 'supplier@ricesupplies.com',
            phone: '+91 98765 00001',
            address: 'Punjab, India'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Wheat Flour',
          sku: 'FLOUR-001',
          description: 'Whole wheat flour',
          category: 'Grains',
          costPrice: 30,
          sellingPrice: 40,
          stockQuantity: 300,
          minThreshold: 50,
          unit: 'kg',
          supplier: {
            name: 'Flour Mill Co',
            email: 'supplier@flourmill.com',
            phone: '+91 98765 00002'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Cooking Oil - Sunflower',
          sku: 'OIL-001',
          description: 'Refined sunflower cooking oil',
          category: 'Oils',
          costPrice: 120,
          sellingPrice: 150,
          stockQuantity: 200,
          minThreshold: 40,
          unit: 'liters',
          supplier: {
            name: 'Oil Refineries Ltd',
            email: 'supplier@oilrefineries.com',
            phone: '+91 98765 00003'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Sugar',
          sku: 'SUGAR-001',
          description: 'White refined sugar',
          category: 'Sweeteners',
          costPrice: 35,
          sellingPrice: 45,
          stockQuantity: 400,
          minThreshold: 80,
          unit: 'kg',
          supplier: {
            name: 'Sugar Mills India',
            email: 'supplier@sugarmills.com',
            phone: '+91 98765 00004'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Tea Leaves - Premium',
          sku: 'TEA-001',
          description: 'Premium Assam tea leaves',
          category: 'Beverages',
          costPrice: 250,
          sellingPrice: 300,
          stockQuantity: 8,
          minThreshold: 20,
          unit: 'kg',
          supplier: {
            name: 'Tea Estates Assam',
            email: 'supplier@teaestates.com',
            phone: '+91 98765 00005'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Coffee Powder',
          sku: 'COFFEE-001',
          description: 'Fresh ground coffee powder',
          category: 'Beverages',
          costPrice: 400,
          sellingPrice: 500,
          stockQuantity: 5,
          minThreshold: 15,
          unit: 'kg',
          supplier: {
            name: 'Coffee Plantations',
            email: 'supplier@coffeeplantations.com',
            phone: '+91 98765 00006'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Pulses - Toor Dal',
          sku: 'PULSE-001',
          description: 'Yellow pigeon peas',
          category: 'Pulses',
          costPrice: 90,
          sellingPrice: 110,
          stockQuantity: 250,
          minThreshold: 50,
          unit: 'kg',
          supplier: {
            name: 'Pulse Traders',
            email: 'supplier@pulsetraders.com',
            phone: '+91 98765 00007'
          },
          isActive: true,
          createdBy: adminUser._id
        },
        {
          name: 'Salt - Iodized',
          sku: 'SALT-001',
          description: 'Iodized table salt',
          category: 'Spices',
          costPrice: 15,
          sellingPrice: 20,
          stockQuantity: 600,
          minThreshold: 100,
          unit: 'kg',
          supplier: {
            name: 'Salt Works',
            email: 'supplier@saltworks.com',
            phone: '+91 98765 00008'
          },
          isActive: true,
          createdBy: adminUser._id
        }
      ]);
      console.log('✅ Sample products created');
    }

    console.log('========================================');
    console.log('✅ Database seeding completed!');
    console.log('========================================');
    console.log('📝 Login Credentials:');
    console.log('');
    console.log('Admin:');
    console.log(`  Email: ${process.env.ADMIN_EMAIL || 'admin@company.com'}`);
    console.log(`  Password: ${process.env.ADMIN_PASSWORD || 'Admin@123456'}`);
    console.log('');
    console.log('Manager:');
    console.log('  Email: manager@company.com');
    console.log('  Password: Manager@123');
    console.log('');
    console.log('Customer:');
    console.log('  Email: customer1@example.com');
    console.log('  Password: Customer@123');
    console.log('========================================');

    process.exit(0);
  } catch (error) {
    console.error('❌ Seeding error:', error);
    process.exit(1);
  }
};

seedDatabase();
