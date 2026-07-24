#!/usr/bin/env node

/**
 * Sample Usage Script for Task Logger Module
 * Demonstrates AIM and PROGRESS logging for Day 1
 */

const { startDay, endDay, generateDaySummary } = require('./task_logger');

async function demonstrateTaskLogging() {
  try {
    console.log('🚀 Starting Task Logger Demonstration\n');

    // Day 1: Database Setup Task
    console.log('📅 Day 1: Database Setup Task');
    console.log('=' .repeat(50));

    // Log AIM at the start of the day
    await startDay(
      'Setting up Supabase PostgreSQL database with tables, constraints, and RLS policies for AI Integration Platform',
      1
    );

    console.log('✅ AIM logged successfully\n');

    // Simulate some work...
    console.log('🔧 Performing database setup tasks...');

    // Simulate task progress (in real usage, this would be actual work)
    const progressDetails = {
      done: [
        'specs_table_created',
        'evaluations_table_created',
        'iterations_table_created',
        'rls_policies_applied',
        'test_queries_passed',
        'encrypted_credentials_generated'
      ],
      failed: [
        // In this demo, no failures
      ],
      grateful: 'Successfully automated the entire database setup process with comprehensive error handling and security measures'
    };

    // Log PROGRESS at the end of the day
    await endDay(progressDetails);

    console.log('✅ PROGRESS logged successfully\n');

    // Generate and display summary
    console.log('📊 Day 1 Summary:');
    console.log('=' .repeat(50));

    const summary = await generateDaySummary(1);
    console.log(JSON.stringify(summary, null, 2));

    console.log('\n🎉 Task logging demonstration completed!');
    console.log('📁 Check ./logs/task_manager.log for the logged entries');

  } catch (error) {
    console.error('❌ Task logging demonstration failed:', error.message);
    process.exit(1);
  }
}

// Integration example for other scripts
async function integrationExample() {
  console.log('\n🔗 Integration Example for Other Scripts:');
  console.log('=' .repeat(50));

  console.log(`
// In your script (e.g., supabase_setup.js):

const { startDay, endDay } = require('./task_logger');

// At the start of your task
await startDay('Your AIM note here', dayNumber);

// During execution, track progress
const progress = { done: [], failed: [], grateful: '' };

// At the end
await endDay(progress);
  `);
}

// Run the demonstration
if (require.main === module) {
  demonstrateTaskLogging()
    .then(() => integrationExample())
    .catch(error => {
      console.error('Demo failed:', error);
      process.exit(1);
    });
}

module.exports = { demonstrateTaskLogging };