#!/usr/bin/env node

/**
 * Automated Backup Script for Supabase Storage
 * Runs daily at midnight UTC to backup reports-previews bucket
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs').promises;
const path = require('path');

// Environment variables
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const BACKUP_BUCKET = `backups-${new Date().toISOString().split('T')[0]}`;

async function createBackup() {
  try {
    console.log('🔄 Starting storage backup...');

    if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables');
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // List all files in reports-previews bucket
    const { data: files, error: listError } = await supabase.storage
      .from('reports-previews')
      .list('', { limit: 1000 });

    if (listError) {
      throw new Error(`Failed to list files: ${listError.message}`);
    }

    console.log(`Found ${files.length} files to backup`);

    if (files.length === 0) {
      console.log('ℹ️  No files to backup');
      return;
    }

    // Create backup bucket if it doesn't exist
    const { error: createError } = await supabase.storage.createBucket(BACKUP_BUCKET, {
      public: false
    });

    if (createError && !createError.message.includes('already exists')) {
      console.warn(`⚠️  Could not create backup bucket: ${createError.message}`);
    }

    // Copy files to backup bucket
    let successCount = 0;
    let errorCount = 0;

    for (const file of files) {
      try {
        // Download file
        const { data: fileData, error: downloadError } = await supabase.storage
          .from('reports-previews')
          .download(file.name);

        if (downloadError) {
          console.error(`Failed to download ${file.name}: ${downloadError.message}`);
          errorCount++;
          continue;
        }

        // Upload to backup bucket with timestamp
        const backupPath = `${new Date().toISOString()}/${file.name}`;
        const { error: uploadError } = await supabase.storage
          .from(BACKUP_BUCKET)
          .upload(backupPath, fileData, {
            upsert: true // Allow overwrites for backup updates
          });

        if (uploadError) {
          console.error(`Failed to backup ${file.name}: ${uploadError.message}`);
          errorCount++;
        } else {
          successCount++;
          console.log(`✅ Backed up: ${file.name}`);
        }

      } catch (fileError) {
        console.error(`Error processing ${file.name}: ${fileError.message}`);
        errorCount++;
      }
    }

    console.log(`✅ Backup completed: ${successCount} files backed up, ${errorCount} errors`);

    // Clean up old backups (keep last 7 days)
    await cleanupOldBackups(supabase);

    // Log success
    console.log(`📦 Backup stored in bucket: ${BACKUP_BUCKET}`);

  } catch (error) {
    console.error('❌ Backup failed:', error.message);
    await sendEmailNotification(
      'Storage Backup Failed',
      `Backup process failed: ${error.message}`
    );
    throw error;
  }
}

async function cleanupOldBackups(supabase) {
  try {
    console.log('🧹 Cleaning up old backups...');

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 7); // Keep 7 days

    const { data: buckets, error } = await supabase.storage.listBuckets();

    if (error) {
      console.warn('Could not list buckets for cleanup:', error.message);
      return;
    }

    let cleanedCount = 0;

    for (const bucket of buckets) {
      if (bucket.name.startsWith('backups-')) {
        const bucketDate = new Date(bucket.name.replace('backups-', ''));

        if (bucketDate < cutoffDate) {
          console.log(`Removing old backup: ${bucket.name}`);

          try {
            // List all files in the old backup bucket
            const { data: files, error: listError } = await supabase.storage
              .from(bucket.name)
              .list('', { limit: 1000 });

            if (!listError && files.length > 0) {
              // Delete all files in the bucket
              const filePaths = files.map(file => file.name);
              await supabase.storage
                .from(bucket.name)
                .remove(filePaths);
            }

            // Delete the bucket (if API allows)
            // Note: This might require additional permissions
            console.log(`🗑️  Cleaned up backup: ${bucket.name}`);
            cleanedCount++;

          } catch (cleanupError) {
            console.warn(`Could not fully clean up ${bucket.name}: ${cleanupError.message}`);
          }
        }
      }
    }

    if (cleanedCount > 0) {
      console.log(`🧹 Cleaned up ${cleanedCount} old backup(s)`);
    } else {
      console.log('ℹ️  No old backups to clean up');
    }

  } catch (error) {
    console.warn('Cleanup failed:', error.message);
  }
}

// Email notification stub (replace with actual service)
async function sendEmailNotification(subject, message) {
  console.warn(`📧 EMAIL NOTIFICATION STUB: ${subject}`);
  console.warn(`Message: ${message}`);

  // Production implementation:
  // - SendGrid: https://sendgrid.com/
  // - AWS SES: https://aws.amazon.com/ses/
  // - Mailgun: https://www.mailgun.com/
  // - Slack webhook for alerts
}

// Schedule setup instructions
function printScheduleInstructions() {
  console.log('\n📅 Backup Schedule Setup Instructions:');
  console.log('=====================================');
  console.log('');
  console.log('1. CRON JOB (Linux/Mac):');
  console.log('   Add to crontab (crontab -e):');
  console.log('   0 0 * * * cd /path/to/your/project && node backup_schedule.js');
  console.log('');
  console.log('2. WINDOWS TASK SCHEDULER:');
  console.log('   - Open Task Scheduler');
  console.log('   - Create new task');
  console.log('   - Trigger: Daily at 12:00 AM');
  console.log('   - Action: Start program');
  console.log('   - Program: node.exe');
  console.log('   - Arguments: backup_schedule.js');
  console.log('   - Start in: C:\\path\\to\\your\\project');
  console.log('');
  console.log('3. NODE.JS SCHEDULER (in your app):');
  console.log('   const cron = require(\'node-cron\');');
  console.log('   cron.schedule(\'0 0 * * *\', () => createBackup());');
  console.log('');
  console.log('4. DOCKER CONTAINER:');
  console.log('   Add to docker-compose.yml:');
  console.log('   backup:');
  console.log('     build: .');
  console.log('     command: node backup_schedule.js');
  console.log('     environment:');
  console.log('       - SUPABASE_URL=${SUPABASE_URL}');
  console.log('       - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}');
}

// Run backup if called directly
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log('Supabase Storage Backup Script');
    console.log('==============================');
    console.log('');
    console.log('Usage: node backup_schedule.js [options]');
    console.log('');
    console.log('Options:');
    console.log('  --help, -h          Show this help message');
    console.log('  --schedule           Show scheduling instructions');
    console.log('  --cleanup-only       Run only cleanup (no backup)');
    console.log('');
    console.log('Environment Variables:');
    console.log('  SUPABASE_URL                 Your Supabase project URL');
    console.log('  SUPABASE_SERVICE_ROLE_KEY    Your Supabase service role key');
    console.log('');
    process.exit(0);
  }

  if (args.includes('--schedule')) {
    printScheduleInstructions();
    process.exit(0);
  }

  if (args.includes('--cleanup-only')) {
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    cleanupOldBackups(supabase).catch(console.error);
    return;
  }

  // Run full backup
  createBackup().catch(error => {
    console.error('Backup script failed:', error);
    process.exit(1);
  });
}

module.exports = { createBackup, cleanupOldBackups, printScheduleInstructions };