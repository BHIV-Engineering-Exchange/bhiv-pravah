const Groq = require('groq-sdk');

class GroqService {
  constructor() {
    this.client = null;
    this.model = process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';
    this.initialize();
  }

  initialize() {
    if (!process.env.GROQ_API_KEY) {
      console.warn('⚠️ GROQ_API_KEY not found in environment variables. AI insights will be limited.');
      return;
    }

    try {
      this.client = new Groq({
        apiKey: process.env.GROQ_API_KEY,
      });
      console.log('✅ Groq AI service initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize Groq client:', error.message);
    }
  }

  isAvailable() {
    return this.client !== null;
  }

  /**
   * Analyze tasks and generate workflow insights
   * @param {Array} tasks - Array of task objects from database
   * @param {Array} users - Array of user objects from database
   * @returns {Promise<Array>} - Array of AI-generated insights
   */
  async analyzeWorkflow(tasks, users) {
    if (!this.isAvailable()) {
      console.log('🔄 Groq not available, using fallback analysis');
      return this.generateFallbackInsights(tasks, users);
    }

    try {
      // Prepare task data for AI analysis
      const taskSummary = this.prepareTaskSummary(tasks, users);
      
      const prompt = `You are an expert workflow optimization AI assistant. Analyze the following task and team data, then generate actionable insights.

**Task Data:**
${JSON.stringify(taskSummary, null, 2)}

**Instructions:**
1. Identify specific workflow optimization opportunities
2. Focus on: resource allocation, deadline risks, dependencies, and workload balance
3. Provide 3-5 insights with HIGH impact priorities first
4. Each insight MUST have specific task/user references
5. Suggest concrete, actionable steps

**Output Format (JSON array):**
[
  {
    "id": "unique-id",
    "title": "Short descriptive title",
    "category": "Resources|Dependencies|Deadlines|Workflow",
    "impact": "High|Medium|Low",
    "description": "Detailed description with specific task/user names",
    "actions": ["Action 1", "Action 2"],
    "createdAt": "${new Date().toISOString()}"
  }
]

Return ONLY the JSON array, no additional text.`;

      const chatCompletion = await this.client.chat.completions.create({
        messages: [
          {
            role: 'system',
            content: 'You are a workflow optimization expert. Analyze data and return insights as valid JSON arrays only.',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        model: this.model,
        temperature: 0.7,
        max_tokens: 2000,
        response_format: { type: 'json_object' },
      });

      const responseText = chatCompletion.choices[0]?.message?.content;
      
      if (!responseText) {
        throw new Error('Empty response from Groq API');
      }

      // Parse the response
      let insights;
      try {
        const parsed = JSON.parse(responseText);
        // Handle both direct array and wrapped object responses
        insights = Array.isArray(parsed) ? parsed : (parsed.insights || []);
      } catch (parseError) {
        console.error('Failed to parse Groq response:', responseText);
        throw new Error('Invalid JSON response from AI');
      }

      // Validate and enrich insights
      insights = insights.map((insight, index) => ({
        id: insight.id || `insight-${Date.now()}-${index}`,
        title: insight.title || 'Optimization Suggestion',
        category: this.validateCategory(insight.category),
        impact: this.validateImpact(insight.impact),
        description: insight.description || 'No description provided',
        actions: Array.isArray(insight.actions) ? insight.actions : [],
        createdAt: insight.createdAt || new Date().toISOString(),
      }));

      console.log(`✅ Generated ${insights.length} AI insights using Groq`);
      return insights;

    } catch (error) {
      console.error('❌ Groq API error:', error.message);
      
      // Fallback to rule-based insights on error
      return this.generateFallbackInsights(tasks, users);
    }
  }

  /**
   * Prepare task summary for AI analysis
   */
  prepareTaskSummary(tasks, users) {
    const now = new Date();
    
    // User workload analysis
    const userWorkload = {};
    users.forEach(user => {
      userWorkload[user._id.toString()] = {
        name: user.name,
        email: user.email,
        role: user.role,
        taskCount: 0,
        highPriorityCount: 0,
        overdueTasks: 0,
      };
    });

    // Task categorization
    const taskStats = {
      total: tasks.length,
      completed: 0,
      inProgress: 0,
      notStarted: 0,
      overdue: 0,
      highPriority: 0,
      categories: {},
    };

    const taskSummary = tasks.slice(0, 20).map(task => {
      const isOverdue = new Date(task.dueDate) < now && task.status !== 'completed';
      
      if (task.status === 'completed') taskStats.completed++;
      else if (task.status === 'in-progress') taskStats.inProgress++;
      else taskStats.notStarted++;
      
      if (isOverdue) taskStats.overdue++;
      if (task.priority === 'High') taskStats.highPriority++;

      // Update user workload
      if (task.assignee && userWorkload[task.assignee.toString()]) {
        userWorkload[task.assignee.toString()].taskCount++;
        if (task.priority === 'High') {
          userWorkload[task.assignee.toString()].highPriorityCount++;
        }
        if (isOverdue) {
          userWorkload[task.assignee.toString()].overdueTasks++;
        }
      }

      return {
        title: task.title,
        status: task.status,
        priority: task.priority,
        dueDate: task.dueDate,
        assignee: task.assignee ? userWorkload[task.assignee.toString()]?.name : 'Unassigned',
        isOverdue,
      };
    });

    return {
      taskStats,
      taskSummary,
      userWorkload: Object.values(userWorkload),
      analysisDate: now.toISOString(),
    };
  }

  /**
   * Generate fallback insights using rule-based analysis
   */
  generateFallbackInsights(tasks, users) {
    const insights = [];
    const now = new Date();

    // Analyze overdue tasks
    const overdueTasks = tasks.filter(
      task => new Date(task.dueDate) < now && task.status !== 'completed'
    );

    if (overdueTasks.length > 0) {
      insights.push({
        id: `insight-overdue-${Date.now()}`,
        title: 'Multiple Overdue Tasks Detected',
        category: 'Deadlines',
        impact: 'High',
        description: `${overdueTasks.length} task(s) are overdue. Immediate attention required to prevent project delays. Tasks include: ${overdueTasks.slice(0, 3).map(t => `'${t.title}'`).join(', ')}.`,
        actions: ['Review and reprioritize tasks', 'Extend deadlines if necessary', 'Reallocate resources'],
        createdAt: new Date().toISOString(),
      });
    }

    // Analyze workload distribution
    const userWorkload = {};
    tasks.forEach(task => {
      if (task.assignee) {
        const userId = task.assignee.toString();
        if (!userWorkload[userId]) {
          userWorkload[userId] = { count: 0, tasks: [] };
        }
        userWorkload[userId].count++;
        userWorkload[userId].tasks.push(task.title);
      }
    });

    const workloadValues = Object.values(userWorkload);
    if (workloadValues.length > 0) {
      const avgWorkload = workloadValues.reduce((sum, w) => sum + w.count, 0) / workloadValues.length;
      const overloaded = workloadValues.filter(w => w.count > avgWorkload * 1.5);

      if (overloaded.length > 0) {
        insights.push({
          id: `insight-workload-${Date.now()}`,
          title: 'Unbalanced Workload Distribution',
          category: 'Resources',
          impact: 'Medium',
          description: `${overloaded.length} team member(s) have significantly more tasks than average (${Math.round(avgWorkload)} tasks). This may lead to burnout and delays.`,
          actions: ['Redistribute tasks', 'Review team capacity', 'Consider additional resources'],
          createdAt: new Date().toISOString(),
        });
      }
    }

    // Analyze high priority tasks
    const highPriorityTasks = tasks.filter(
      task => task.priority === 'High' && task.status !== 'completed'
    );

    if (highPriorityTasks.length > 5) {
      insights.push({
        id: `insight-priority-${Date.now()}`,
        title: 'Too Many High Priority Tasks',
        category: 'Workflow',
        impact: 'Medium',
        description: `${highPriorityTasks.length} tasks marked as high priority. This may dilute focus and reduce effectiveness. Consider re-evaluating priorities.`,
        actions: ['Re-evaluate task priorities', 'Focus on top 3-5 critical tasks', 'Defer lower impact items'],
        createdAt: new Date().toISOString(),
      });
    }

    // Analyze upcoming deadlines
    const upcomingDeadlines = tasks.filter(task => {
      const daysUntilDue = (new Date(task.dueDate) - now) / (1000 * 60 * 60 * 24);
      return daysUntilDue > 0 && daysUntilDue <= 3 && task.status !== 'completed';
    });

    if (upcomingDeadlines.length > 0) {
      insights.push({
        id: `insight-upcoming-${Date.now()}`,
        title: 'Critical Deadlines Approaching',
        category: 'Deadlines',
        impact: 'High',
        description: `${upcomingDeadlines.length} task(s) due within the next 3 days: ${upcomingDeadlines.slice(0, 3).map(t => `'${t.title}'`).join(', ')}. Ensure adequate focus and resources.`,
        actions: ['Prioritize these tasks', 'Clear blockers', 'Daily progress check-ins'],
        createdAt: new Date().toISOString(),
      });
    }

    // If no issues found, add positive insight
    if (insights.length === 0) {
      insights.push({
        id: `insight-positive-${Date.now()}`,
        title: 'Workflow Running Smoothly',
        category: 'Workflow',
        impact: 'Low',
        description: 'No critical issues detected in current workflow. Team workload is balanced, and deadlines are being met.',
        actions: ['Maintain current pace', 'Continue monitoring progress', 'Plan for upcoming tasks'],
        createdAt: new Date().toISOString(),
      });
    }

    console.log(`✅ Generated ${insights.length} rule-based insights (fallback)`);
    return insights;
  }

  validateCategory(category) {
    const validCategories = ['Resources', 'Dependencies', 'Deadlines', 'Workflow'];
    return validCategories.includes(category) ? category : 'Workflow';
  }

  validateImpact(impact) {
    const validImpacts = ['High', 'Medium', 'Low'];
    return validImpacts.includes(impact) ? impact : 'Medium';
  }
}

// Export singleton instance
module.exports = new GroqService();
