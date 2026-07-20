#!/usr/bin/env node

/**
 * Lead Report Generator
 * Compiles AIM and PROGRESS logs into /reports/lead_log.txt
 * Designed for Anmol's backend integration
 */

const { readLogs } = require('./task_logger');
const fs = require('fs').promises;
const path = require('path');

async function generateLeadReport() {
  try {
    console.log('📊 Generating lead report...');

    // Ensure reports directory exists
    const reportsDir = path.join(__dirname, 'reports');
    await fs.mkdir(reportsDir, { recursive: true });

    // Read all logs
    const logs = await readLogs();

    if (logs.length === 0) {
      console.log('No logs found to generate report');
      return;
    }

    // Group logs by day
    const days = {};
    logs.forEach(log => {
      if (!days[log.day]) {
        days[log.day] = { aim: null, progress: null, allLogs: [] };
      }
      days[log.day].allLogs.push(log);

      if (log.type === 'AIM') {
        days[log.day].aim = log;
      } else if (log.type === 'PROGRESS') {
        days[log.day].progress = log;
      }
    });

    // Generate report
    let report = '# AI Integration Platform - Lead Progress Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n`;
    report += `Total Log Entries: ${logs.length}\n\n`;
    report += '=' .repeat(60) + '\n\n';

    // Sort days and generate content
    const sortedDays = Object.keys(days).sort((a, b) => parseInt(a) - parseInt(b));

    sortedDays.forEach(dayNum => {
      const day = days[dayNum];
      const { aim, progress, allLogs } = day;

      report += `## Day ${dayNum}\n\n`;

      // AIM Section
      if (aim) {
        report += `**AIM:** ${aim.note}\n\n`;
        report += `Started: ${new Date(aim.timestamp).toLocaleString()}\n\n`;
      } else {
        report += `**AIM:** Not logged for this day\n\n`;
      }

      // PROGRESS Section
      if (progress) {
        const { done, failed, grateful } = progress.note;

        report += `**COMPLETED TASKS:**\n`;
        if (done.length > 0) {
          done.forEach(task => report += `- ✅ ${task}\n`);
        } else {
          report += `- No tasks completed\n`;
        }
        report += '\n';

        if (failed.length > 0) {
          report += `**FAILED TASKS:**\n`;
          failed.forEach(task => report += `- ❌ ${task}\n`);
          report += '\n';
        }

        report += `**LEARNINGS & GRATITUDE:**\n`;
        report += `${grateful}\n\n`;

        report += `Completed: ${new Date(progress.timestamp).toLocaleString()}\n\n`;
      } else {
        report += `**PROGRESS:** Not logged for this day\n\n`;
      }

      // Day Statistics
      report += `**DAY STATISTICS:**\n`;
      report += `- Total log entries: ${allLogs.length}\n`;
      report += `- AIM entries: ${allLogs.filter(l => l.type === 'AIM').length}\n`;
      report += `- PROGRESS entries: ${allLogs.filter(l => l.type === 'PROGRESS').length}\n`;
      report += `- Time span: ${new Date(allLogs[0].timestamp).toLocaleString()} - ${new Date(allLogs[allLogs.length - 1].timestamp).toLocaleString()}\n\n`;

      report += '-' .repeat(40) + '\n\n';
    });

    // Overall Statistics
    report += '# OVERALL STATISTICS\n\n';

    const totalDays = sortedDays.length;
    const daysWithAim = sortedDays.filter(d => days[d].aim).length;
    const daysWithProgress = sortedDays.filter(d => days[d].progress).length;
    const totalCompletedTasks = sortedDays.reduce((sum, d) => {
      return sum + (days[d].progress?.note?.done?.length || 0);
    }, 0);
    const totalFailedTasks = sortedDays.reduce((sum, d) => {
      return sum + (days[d].progress?.note?.failed?.length || 0);
    }, 0);

    report += `## Summary\n`;
    report += `- Days covered: ${totalDays}\n`;
    report += `- Days with AIM logged: ${daysWithAim} (${totalDays > 0 ? ((daysWithAim/totalDays)*100).toFixed(1) : 0}%)\n`;
    report += `- Days with PROGRESS logged: ${daysWithProgress} (${totalDays > 0 ? ((daysWithProgress/totalDays)*100).toFixed(1) : 0}%)\n`;
    report += `- Total tasks completed: ${totalCompletedTasks}\n`;
    report += `- Total tasks failed: ${totalFailedTasks}\n`;
    const totalTasks = totalCompletedTasks + totalFailedTasks;
    report += `- Success rate: ${totalTasks > 0 ? ((totalCompletedTasks/totalTasks)*100).toFixed(1) : 0}%\n\n`;

    // Recent Activity Summary
    report += `## Recent Activity\n`;
    const recentLogs = logs.slice(-10); // Last 10 entries
    recentLogs.forEach(log => {
      const time = new Date(log.timestamp).toLocaleString();
      if (log.type === 'AIM') {
        report += `- ${time}: AIM logged for Day ${log.day}\n`;
      } else if (log.type === 'PROGRESS') {
        const completed = log.note.done.length;
        const failed = log.note.failed.length;
        report += `- ${time}: PROGRESS logged for Day ${log.day} (${completed} done, ${failed} failed)\n`;
      }
    });

    // Write report
    const reportPath = path.join(reportsDir, 'lead_log.txt');
    await fs.writeFile(reportPath, report, 'utf8');

    console.log(`✅ Lead report generated successfully: ${reportPath}`);
    console.log(`📊 Report includes ${totalDays} days with ${logs.length} total log entries`);
    console.log(`📈 Success rate: ${totalTasks > 0 ? ((totalCompletedTasks/totalTasks)*100).toFixed(1) : 0}%`);

  } catch (error) {
    console.error('❌ Failed to generate lead report:', error.message);
    throw error;
  }
}

// Export for use in other scripts
module.exports = { generateLeadReport };

// Run if called directly
if (require.main === module) {
  generateLeadReport().catch(error => {
    console.error('Report generation failed:', error);
    process.exit(1);
  });
}