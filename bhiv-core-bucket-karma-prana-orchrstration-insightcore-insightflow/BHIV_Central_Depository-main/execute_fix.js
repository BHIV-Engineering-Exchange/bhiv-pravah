#!/usr/bin/env node

/**
 * Execute the foreign key fix in Supabase
 * This script applies SQL fixes to enable testing without auth users
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs').promises;
require('dotenv').config({ path: './.env' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function executeFix() {
  console.log('🔧 Executing Supabase foreign key fix...\n');
  
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
  
  // Read the fix SQL file
  const fixSQL = await fs.readFile('fix_foreign_keys.sql', 'utf8');
  console.log('📄 SQL Fix Content:');
  console.log(fixSQL);
  console.log('\n' + '='.repeat(50) + '\n');
  
  // Since direct SQL execution via JS is limited, we'll provide manual instructions
  console.log('🚨 MANUAL EXECUTION REQUIRED:');
  console.log('\n📋 Steps to apply the fix:');
  console.log('1. Go to https://app.supabase.com/projects');
  console.log('2. Select your project');
  console.log('3. Go to SQL Editor');
  console.log('4. Copy and paste the following SQL:\n');
  
  console.log('-- Copy from here --');
  console.log(fixSQL);
  console.log('-- Copy to here --\n');
  
  console.log('5. Click "Run" to execute the SQL');
  console.log('6. After execution, run: npm run test:db\n');
  
  // Test current constraint status
  console.log('🔍 Testing current database constraint status...');
  
  try {
    // Try to insert a test record to see what constraints exist
    const testUserId = crypto.randomUUID();
    const { data, error } = await supabase
      .from('specs')
      .insert({
        prompt: 'Test constraint check',
        json_spec: { key: 'test', type: 'constraint_test' },
        user_id: testUserId
      })
      .select();
    
    if (error) {
      console.log('❌ Current constraint status:', error.message);
      if (error.message.includes('foreign key constraint')) {
        console.log('🔧 Foreign key constraints are still active - fix needed');
      } else if (error.message.includes('violates check constraint')) {
        console.log('✅ Foreign key constraints may already be removed');
      }
    } else {
      console.log('✅ Test insert successful - constraints appear to be fixed');
      // Clean up test record
      await supabase.from('specs').delete().eq('id', data[0].id);
      console.log('🧹 Test record cleaned up');
    }
  } catch (err) {
    console.log('❌ Database test failed:', err.message);
  }
  
  console.log('\n🎯 Next step: Execute the SQL fix manually, then run tests');
}

async function main() {
  try {
    await executeFix();
  } catch (error) {
    console.error('❌ Script failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}