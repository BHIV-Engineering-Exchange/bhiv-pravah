const nodemailer = require('nodemailer');
const EmailTemplate = require('../models/EmailTemplate');
const ScheduledEmail = require('../models/ScheduledEmail');
const User = require('../models/User');
const Task = require('../models/Task');
const { auditLogger } = require('./complianceAuditLogger');

class EMSAutomation {
  constructor() {
    this.transporter = this.createTransporter();
    this.defaultTemplates = this.getDefaultTemplates();
    // Don't initialize templates in constructor - let it be done after MongoDB connects
    this.templatesInitialized = false;
  }

  createTransporter() {
    // Only create transporter if email credentials are provided
    if (!process.env.EMAIL_USER || !process.env.EMAIL_PASS) {
      console.warn('⚠️  EMS: Email credentials not configured. Running in MOCK MODE.');
      console.warn('   Add EMAIL_USER and EMAIL_PASS to .env file to enable real email sending.');
      return null;
    }

    const port = parseInt(process.env.EMAIL_PORT || '587');
    const secure = process.env.EMAIL_SECURE === 'true' || port === 465;

    return nodemailer.createTransport({
      host: process.env.EMAIL_HOST || 'smtp.gmail.com',
      port: port,
      secure: secure,
      connectionTimeout: 10000, // 10 seconds timeout
      greetingTimeout: 5000,
      socketTimeout: 15000,
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
      },
      pool: true,
      maxConnections: 5
    });
  }

  getDefaultTemplates() {
    return {
      task_assignment: {
        templateId: 'task_assignment',
        name: 'Task Assignment Notification',
        subject: '📋 New Task Assigned: {task_title}',
        htmlBody: `
          <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>📋 New Task Assigned</h2>
            <p>Hello {employee_name},</p>
            <p>You have been assigned a new task:</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
              <p><strong>Task:</strong> {task_title}</p>
              <p><strong>Description:</strong> {task_description}</p>
              <p><strong>Priority:</strong> {task_priority}</p>
              <p><strong>Due Date:</strong> {due_date}</p>
              <p><strong>Assigned By:</strong> {assigned_by}</p>
            </div>
            <p>Please log in to the system to view more details and start working on this task.</p>
            <p>Best regards,<br>Infiverse Team</p>
          </body>
          </html>
        `,
        category: 'task'
      },
      task_reminder: {
        templateId: 'task_reminder',
        name: 'Task Reminder',
        subject: '⏰ Task Reminder: {task_title}',
        htmlBody: `
          <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>⏰ Task Reminder</h2>
            <p>Hello {employee_name},</p>
            <p>This is a reminder about your upcoming task:</p>
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0;">
              <p><strong>Task:</strong> {task_title}</p>
              <p><strong>Due Date:</strong> {due_date}</p>
              <p><strong>Status:</strong> {task_status}</p>
              <p><strong>Progress:</strong> {task_progress}%</p>
            </div>
            <p>Please ensure to complete this task on time.</p>
            <p>Best regards,<br>Infiverse Team</p>
          </body>
          </html>
        `,
        category: 'task'
      },
      task_overdue: {
        templateId: 'task_overdue',
        name: 'Task Overdue Alert',
        subject: '🚨 Overdue Task: {task_title}',
        htmlBody: `
          <html>
          <body style="font-family: Arial, sans-serif;">
            <h2>🚨 Task Overdue Alert</h2>
            <p>Hello {employee_name},</p>
            <p>The following task is overdue:</p>
            <div style="background-color: #f8d7da; padding: 20px; border-radius: 5px; margin: 20px 0;">
              <p><strong>Task:</strong> {task_title}</p>
              <p><strong>Due Date:</strong> {due_date}</p>
              <p><strong>Days Overdue:</strong> {days_overdue}</p>
              <p><strong>Status:</strong> {task_status}</p>
            </div>
            <p>Please complete this task as soon as possible or contact your manager.</p>
            <p>Best regards,<br>Infiverse Team</p>
          </body>
          </html>
        `,
        category: 'task'
      }
    };
  }

  async initializeDefaultTemplates() {
    try {
      for (const template of Object.values(this.defaultTemplates)) {
        await EmailTemplate.findOneAndUpdate(
          { templateId: template.templateId },
          { ...template, createdBy: null },
          { upsert: true }
        );
      }
    } catch (error) {
      console.error('Error initializing default templates:', error);
    }
  }

  async sendTaskAssignmentEmail(taskId, assigneeId, assignedById) {
    try {
      const task = await Task.findById(taskId).populate('assignee department');
      const assignee = await User.findById(assigneeId);
      const assignedBy = await User.findById(assignedById);

      if (!task || !assignee || !assignedBy) {
        throw new Error('Task, assignee, or assigner not found');
      }

      const context = {
        employee_name: assignee.name,
        task_title: task.title,
        task_description: task.description,
        task_priority: task.priority,
        due_date: task.dueDate ? task.dueDate.toLocaleDateString() : 'Not set',
        assigned_by: assignedBy.name
      };

      return await this.sendTemplatedEmail('task_assignment', [assignee.email], context, assignedById);
    } catch (error) {
      console.error('Error sending task assignment email:', error);
      throw error;
    }
  }

  async sendTaskReminderEmail(taskId, reminderType = 'due_soon') {
    try {
      const task = await Task.findById(taskId).populate('assignee');
      
      if (!task || !task.assignee) {
        throw new Error('Task or assignee not found');
      }

      const context = {
        employee_name: task.assignee.name,
        task_title: task.title,
        due_date: task.dueDate ? task.dueDate.toLocaleDateString() : 'Not set',
        task_status: task.status,
        task_progress: task.progress || 0
      };

      return await this.sendTemplatedEmail('task_reminder', [task.assignee.email], context, 'system');
    } catch (error) {
      console.error('Error sending task reminder email:', error);
      throw error;
    }
  }

  async sendTaskOverdueEmail(taskId) {
    try {
      const task = await Task.findById(taskId).populate('assignee');
      
      if (!task || !task.assignee) {
        throw new Error('Task or assignee not found');
      }

      const daysOverdue = Math.floor((new Date() - task.dueDate) / (1000 * 60 * 60 * 24));

      const context = {
        employee_name: task.assignee.name,
        task_title: task.title,
        due_date: task.dueDate ? task.dueDate.toLocaleDateString() : 'Not set',
        days_overdue: daysOverdue,
        task_status: task.status
      };

      return await this.sendTemplatedEmail('task_overdue', [task.assignee.email], context, 'system');
    } catch (error) {
      console.error('Error sending task overdue email:', error);
      throw error;
    }
  }

  async sendTemplatedEmail(templateId, recipients, context, senderId, scheduleTime = null) {
    try {
      const template = await EmailTemplate.findOne({ templateId, isActive: true });
      
      if (!template) {
        throw new Error(`Template ${templateId} not found`);
      }

      const subject = this.renderTemplate(template.subject, context);
      const htmlBody = this.renderTemplate(template.htmlBody, context);

      if (scheduleTime) {
        return await this.scheduleEmail(subject, htmlBody, recipients, scheduleTime, templateId, senderId);
      } else {
        return await this.sendEmail(subject, htmlBody, recipients, senderId);
      }
    } catch (error) {
      console.error('Error sending templated email:', error);
      throw error;
    }
  }

  renderTemplate(template, context) {
    let rendered = template;
    for (const [key, value] of Object.entries(context)) {
      const regex = new RegExp(`{${key}}`, 'g');
      rendered = rendered.replace(regex, value || '');
    }
    return rendered;
  }

  async sendEmail(subject, htmlBody, recipients, senderId) {
    try {
      // If email is not configured, use mock mode (log only)
      if (!process.env.EMAIL_USER || !process.env.EMAIL_PASS) {
        console.log('📧 [MOCK MODE] Email would be sent:');
        console.log(`   Subject: ${subject}`);
        console.log(`   To: ${recipients.join(', ')}`);
        console.log(`   Recipients: ${recipients.length}`);
        
        // Log the email activity (mock mode)
        console.log(`📝 Email activity logged (mock mode)`);
        // Skip audit logging in mock mode to avoid enum validation errors

        console.log(`✅ Email logged successfully (${recipients.length} recipients) - Configure EMAIL_USER and EMAIL_PASS in .env to send real emails`);
        return { success: true, messageId: `mock-${Date.now()}`, mode: 'mock' };
      }

      const mailOptions = {
        from: process.env.EMAIL_USER,
        to: recipients.join(', '),
        subject,
        html: htmlBody
      };

      const result = await this.transporter.sendMail(mailOptions);

      console.log(`✅ Email sent successfully to ${recipients.length} recipients`);
      console.log(`   MessageId: ${result?.messageId || 'No messageId'}`);
      return { 
        success: true, 
        messageId: result?.messageId || `sent-${Date.now()}`,
        response: result?.response
      };
    } catch (error) {
      console.error('❌ Error sending email:', error);
      throw error;
    }
  }

  async scheduleEmail(subject, htmlBody, recipients, scheduleTime, eventType, senderId) {
    try {
      const scheduledEmail = new ScheduledEmail({
        subject,
        htmlBody,
        recipients,
        scheduledTime: new Date(scheduleTime),
        eventType,
        createdBy: senderId
      });

      await scheduledEmail.save();

      console.log(`📅 Email scheduled for ${scheduleTime}`);
      return { success: true, scheduledId: scheduledEmail._id };
    } catch (error) {
      console.error('Error scheduling email:', error);
      throw error;
    }
  }

  async processScheduledEmails() {
    try {
      const now = new Date();
      const dueEmails = await ScheduledEmail.find({
        scheduledTime: { $lte: now },
        status: 'scheduled'
      });

      let processed = 0;

      for (const email of dueEmails) {
        try {
          await this.sendEmail(email.subject, email.htmlBody, email.recipients, email.createdBy);
          
          email.status = 'sent';
          email.sentAt = new Date();
          await email.save();
          
          processed++;
        } catch (error) {
          email.status = 'failed';
          email.errorMessage = error.message;
          await email.save();
        }
      }

      return processed;
    } catch (error) {
      console.error('Error processing scheduled emails:', error);
      return 0;
    }
  }

  async sendBulkTaskEmails(taskIds, templateId, adminId) {
    try {
      const results = [];
      
      for (const taskId of taskIds) {
        try {
          let result;
          
          switch (templateId) {
            case 'task_assignment':
              const task = await Task.findById(taskId);
              result = await this.sendTaskAssignmentEmail(taskId, task.assignee, adminId);
              break;
            case 'task_reminder':
              result = await this.sendTaskReminderEmail(taskId);
              break;
            case 'task_overdue':
              result = await this.sendTaskOverdueEmail(taskId);
              break;
            default:
              throw new Error(`Unknown template: ${templateId}`);
          }
          
          results.push({ taskId, success: true, result });
        } catch (error) {
          results.push({ taskId, success: false, error: error.message });
        }
      }

      return results;
    } catch (error) {
      console.error('Error sending bulk task emails:', error);
      throw error;
    }
  }
}

module.exports = new EMSAutomation();