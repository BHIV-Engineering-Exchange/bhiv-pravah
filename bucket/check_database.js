#!/usr/bin/env node

/**
 * Execute Supabase SQL files using REST API
 * Since RPC has limitations, we'll provide manual instructions and verification
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs').promises;
require('dotenv').config({ path: './.env' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function checkTableExists(supabase, tableName) {
  try {
    const { data, error } = await supabase
      .from(tableName)
      .select('*')
      .limit(1);
    
    if (error && error.code === 'PGRST116') {
      // Table does not exist
      return false;
    }
    return true;
  } catch (err) {
    return false;
  }
}

async function main() {
  console.log('🔍 Checking Supabase database status...\n');
  
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
  
  const tables = ['specs', 'evaluations', 'iterations'];
  const existingTables = [];
  const missingTables = [];
  
  for (const table of tables) {
    const exists = await checkTableExists(supabase, table);
    if (exists) {
      existingTables.push(table);
      console.log(`✅ Table '${table}' exists`);
    } else {
      missingTables.push(table);
      console.log(`❌ Table '${table}' missing`);
    }
  }
  
  console.log(`\n📊 Status: ${existingTables.length}/${tables.length} tables exist\n`);
  
  if (missingTables.length > 0) {
    console.log('🔧 **MANUAL ACTION REQUIRED:**\n');
    console.log('The database tables need to be created manually in Supabase.\n');
    console.log('**Steps to create tables:**\n');
    console.log('1. Go to your Supabase dashboard: https://app.supabase.com/');
    console.log('2. Select your project');
    console.log('3. Go to SQL Editor');
    console.log('4. Execute each SQL file in order:\n');
    
    const sqlFiles = [
      'create_specs_table.sql',
      'create_evaluations_table.sql', 
      'create_iterations_table.sql'
    ];
    
    for (let i = 0; i < sqlFiles.length; i++) {
      console.log(`   ${i + 1}. Execute: ${sqlFiles[i]}`);
    }
    
    console.log('\n5. After executing all SQL files, run the tests again with:');
    console.log('   npm run test:db\n');
    
    console.log('**Alternatively, you can copy and paste the SQL from these files:**\n');
    
    for (const file of sqlFiles) {
      try {
        const sql = await fs.readFile(file, 'utf8');
        console.log(`--- ${file} ---`);
        console.log(sql);
        console.log('\n');
      } catch (err) {
        console.log(`❌ Could not read ${file}: ${err.message}`);
      }
    }
  } else {
    console.log('✅ All tables exist! You can run tests with: npm run test:db');
  }
}

if (require.main === module) {
  main().catch(console.error);
}