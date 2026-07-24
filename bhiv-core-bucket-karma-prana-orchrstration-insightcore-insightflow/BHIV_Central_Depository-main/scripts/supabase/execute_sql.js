#!/usr/bin/env node

/**
 * Execute SQL files directly in Supabase
 * This script attempts to execute DDL statements using various methods
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs').promises;
require('dotenv').config({ path: './.env' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function executeSQLFile(filePath) {
  console.log(`\n🔄 Executing SQL file: ${filePath}`);
  
  try {
    const sql = await fs.readFile(filePath, 'utf8');
    console.log(`📄 SQL Content (first 200 chars):\n${sql.substring(0, 200)}...`);
    
    // Initialize Supabase client with service role
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    
    // Try to execute using RPC function
    // Note: This approach works for some DDL, but may have limitations
    const { data, error } = await supabase.rpc('exec_sql', { sql_string: sql });
    
    if (error) {
      console.log(`❌ RPC execution failed: ${error.message}`);
      console.log(`💡 You may need to execute this manually in Supabase SQL Editor`);
      return false;
    } else {
      console.log(`✅ Successfully executed: ${filePath}`);
      return true;
    }
  } catch (err) {
    console.error(`❌ Error processing ${filePath}:`, err.message);
    return false;
  }
}

async function main() {
  console.log('🚀 Starting SQL execution...');
  
  const sqlFiles = [
    'create_specs_table.sql',
    'create_evaluations_table.sql', 
    'create_iterations_table.sql'
  ];
  
  let successCount = 0;
  
  for (const file of sqlFiles) {
    const success = await executeSQLFile(file);
    if (success) successCount++;
  }
  
  console.log(`\n📊 Results: ${successCount}/${sqlFiles.length} files executed successfully`);
  
  if (successCount === 0) {
    console.log(`\n📋 Manual execution required:`);
    console.log(`1. Go to your Supabase dashboard`);
    console.log(`2. Navigate to SQL Editor`);
    console.log(`3. Execute each file in order:`);
    sqlFiles.forEach((file, i) => console.log(`   ${i + 1}. ${file}`));
  }
}

if (require.main === module) {
  main().catch(console.error);
}