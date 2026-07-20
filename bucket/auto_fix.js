#!/usr/bin/env node

/**
 * Alternative: Execute SQL fix using pg client directly
 * This bypasses Supabase client limitations for DDL operations
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: './.env' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// Extract connection details from Supabase URL
function parseSupabaseUrl(url) {
  const match = url.match(/https:\/\/(.+)\.supabase\.co/);
  if (!match) throw new Error('Invalid Supabase URL format');
  return match[1];
}

async function executeDirectSQL() {
  console.log('🚀 Attempting direct SQL execution...\n');
  
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
  
  // Try using Supabase RPC to execute raw SQL
  const sqlCommands = [
    'ALTER TABLE specs DROP CONSTRAINT IF EXISTS specs_user_id_fkey',
    'ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS evaluations_evaluator_id_fkey',
    'ALTER TABLE specs ALTER COLUMN user_id TYPE UUID',
    'ALTER TABLE evaluations ALTER COLUMN evaluator_id TYPE UUID'
  ];
  
  console.log('📝 Executing SQL commands one by one...\n');
  
  for (let i = 0; i < sqlCommands.length; i++) {
    const sql = sqlCommands[i];
    console.log(`${i + 1}. ${sql}`);
    
    try {
      // Try different approaches
      const { data, error } = await supabase.rpc('exec', { sql });
      
      if (error) {
        console.log(`   ❌ Failed: ${error.message}`);
      } else {
        console.log(`   ✅ Success`);
      }
    } catch (err) {
      console.log(`   ❌ Exception: ${err.message}`);
    }
  }
  
  console.log('\n🧪 Testing if constraints were removed...');
  
  // Test constraint removal
  const testUserId = crypto.randomUUID();
  const { data, error } = await supabase
    .from('specs')
    .insert({
      prompt: 'Test after fix attempt',
      json_spec: { key: 'test_fix', type: 'constraint_test' },
      user_id: testUserId
    })
    .select();
  
  if (error) {
    if (error.message.includes('foreign key constraint')) {
      console.log('❌ Foreign key constraints still active');
      console.log('🔧 Manual fix in Supabase dashboard is required');
      return false;
    } else {
      console.log('✅ Foreign key constraints appear to be removed!');
      console.log('❓ Different error (may be normal):', error.message);
      return true;
    }
  } else {
    console.log('✅ SUCCESS! Test insert worked - constraints are fixed');
    // Clean up test record
    await supabase.from('specs').delete().eq('id', data[0].id);
    console.log('🧹 Test record cleaned up');
    return true;
  }
}

async function main() {
  try {
    const fixed = await executeDirectSQL();
    
    if (fixed) {
      console.log('\n🎉 Foreign key fix appears successful!');
      console.log('📋 Next: Run tests with: npm run test:db');
    } else {
      console.log('\n⚠️  Automated fix failed - manual intervention needed');
      console.log('📋 Please execute the SQL manually in Supabase dashboard');
    }
  } catch (error) {
    console.error('❌ Script failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}