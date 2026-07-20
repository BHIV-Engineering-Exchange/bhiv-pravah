import mongoose from 'mongoose';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, '../.env') });

async function run() {
  const mongoUri = process.env.MONGODB_URI;
  console.log('Connecting to:', mongoUri);
  await mongoose.connect(mongoUri);
  
  // Find User schema if already registered, otherwise define it
  let User;
  try {
    User = mongoose.model('User');
  } catch {
    User = mongoose.model('User', new mongoose.Schema({
      email: String,
      role: String
    }, { collection: 'users' }));
  }
  
  const users = await User.find({});
  console.log('Users found:', users);
  
  await mongoose.disconnect();
}

run().catch(console.error);
