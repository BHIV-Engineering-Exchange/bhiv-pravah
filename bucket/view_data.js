#!/usr/bin/env node

/**
 * View Stored Data in Supabase
 * This script displays all data stored in the Supabase database
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: './.env' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

async function viewStoredData() {
  console.log('📊 Viewing Stored Data in Supabase Database\n');
  console.log('🔗 Dashboard URL: https://app.supabase.com/projects\n');
  console.log('='.repeat(60) + '\n');
  
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
  
  try {
    // Get all specs with related data
    console.log('📋 SPECS TABLE:');
    const { data: specs, error: specsError } = await supabase
      .from('specs')
      .select(`
        id,
        prompt,
        json_spec,
        created_at,
        user_id
      `)
      .order('created_at', { ascending: false })
      .limit(10);
    
    if (specsError) {
      console.log('❌ Error fetching specs:', specsError.message);
    } else {
      console.log(`📊 Found ${specs.length} specs:`);
      specs.forEach((spec, index) => {
        console.log(`\n${index + 1}. Spec ID: ${spec.id}`);
        console.log(`   Prompt: ${spec.prompt.substring(0, 50)}...`);
        console.log(`   JSON Spec: ${JSON.stringify(spec.json_spec).substring(0, 50)}...`);
        console.log(`   Created: ${new Date(spec.created_at).toLocaleString()}`);
        console.log(`   User ID: ${spec.user_id || 'null'}`);
      });
    }
    
    console.log('\n' + '='.repeat(60) + '\n');
    
    // Get all evaluations
    console.log('⭐ EVALUATIONS TABLE:');
    const { data: evaluations, error: evalsError } = await supabase
      .from('evaluations')
      .select(`
        id,
        spec_id,
        rating,
        feedback,
        created_at,
        evaluator_id
      `)
      .order('created_at', { ascending: false })
      .limit(10);
    
    if (evalsError) {
      console.log('❌ Error fetching evaluations:', evalsError.message);
    } else {
      console.log(`📊 Found ${evaluations.length} evaluations:`);
      evaluations.forEach((evaluation, index) => {
        console.log(`\n${index + 1}. Evaluation ID: ${evaluation.id}`);
        console.log(`   Spec ID: ${evaluation.spec_id}`);
        console.log(`   Rating: ${evaluation.rating}/10`);
        console.log(`   Feedback: ${evaluation.feedback ? evaluation.feedback.substring(0, 50) + '...' : 'None'}`);
        console.log(`   Created: ${new Date(evaluation.created_at).toLocaleString()}`);
        console.log(`   Evaluator ID: ${evaluation.evaluator_id || 'null'}`);
      });
    }
    
    console.log('\n' + '='.repeat(60) + '\n');
    
    // Get all iterations
    console.log('🔄 ITERATIONS TABLE:');
    const { data: iterations, error: itersError } = await supabase
      .from('iterations')
      .select(`
        id,
        spec_id,
        iteration_number,
        changes,
        status,
        created_at
      `)
      .order('created_at', { ascending: false })
      .limit(10);
    
    if (itersError) {
      console.log('❌ Error fetching iterations:', itersError.message);
    } else {
      console.log(`📊 Found ${iterations.length} iterations:`);
      iterations.forEach((iter, index) => {
        console.log(`\n${index + 1}. Iteration ID: ${iter.id}`);
        console.log(`   Spec ID: ${iter.spec_id}`);
        console.log(`   Iteration #: ${iter.iteration_number}`);
        console.log(`   Status: ${iter.status}`);
        console.log(`   Changes: ${JSON.stringify(iter.changes).substring(0, 50)}...`);
        console.log(`   Created: ${new Date(iter.created_at).toLocaleString()}`);
      });
    }
    
    console.log('\n' + '='.repeat(60) + '\n');
    
    // Summary
    console.log('📈 SUMMARY:');
    console.log(`   • ${specs ? specs.length : 0} specs stored`);
    console.log(`   • ${evaluations ? evaluations.length : 0} evaluations recorded`);
    console.log(`   • ${iterations ? iterations.length : 0} iterations tracked`);
    
    console.log('\n🔗 To view in dashboard:');
    console.log('1. Go to https://app.supabase.com/projects');
    console.log('2. Select your project');
    console.log('3. Go to Table Editor');
    console.log('4. Click on each table: specs, evaluations, iterations');
    
    console.log('\n📊 Sample API query for integration:');
    console.log('```javascript');
    console.log('const { data } = await supabase');
    console.log('  .from("specs")');
    console.log('  .select(`*,');
    console.log('    evaluations(*),');
    console.log('    iterations(*)');
    console.log('  `)');
    console.log('```');
    
  } catch (error) {
    console.error('❌ Error viewing data:', error.message);
  }
}

async function main() {
  await viewStoredData();
}

if (require.main === module) {
  main();
}