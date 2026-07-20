const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const adminAuth = require('../middleware/adminAuth');
const groqService = require('../services/groqService');
const Task = require('../models/Task');
const User = require('../models/User');

// AI Insights endpoint - Now with Real Analysis
router.get('/ai/insights', auth, async (req, res) => {
  try {
    // Fetch real task and user data
    const [tasks, users] = await Promise.all([
      Task.find()
        .populate('assignee', 'name email')
        .sort({ dueDate: 1 })
        .lean(),
      User.find({ role: { $in: ['user', 'manager', 'admin'] } })
        .select('name email role')
        .lean(),
    ]);

    // Generate AI-powered insights using Groq
    const insights = await groqService.analyzeWorkflow(tasks, users);

    res.json(insights);

  } catch (error) {
    console.error('AI insights error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to generate AI insights',
    });
  }
});

// AI Optimization endpoint - Now with Real Analysis
router.post('/ai/optimize', auth, async (req, res) => {
  try {
    // Fetch real task and user data
    const [tasks, users] = await Promise.all([
      Task.find()
        .populate('assignee', 'name email')
        .sort({ dueDate: 1 })
        .lean(),
      User.find({ role: { $in: ['user', 'manager', 'admin'] } })
        .select('name email role')
        .lean(),
    ]);

    // Generate fresh insights
    const insights = await groqService.analyzeWorkflow(tasks, users);

    res.json({
      success: true,
      insights,
      generatedAt: new Date(),
      tasksAnalyzed: tasks.length,
      usersAnalyzed: users.length,
    });

  } catch (error) {
    console.error('AI optimization error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to generate optimization suggestions',
    });
  }
});

// AI Dependencies Analysis endpoint
router.get('/ai/dependencies', auth, async (req, res) => {
  try {
    // Mock dependencies analysis
    const dependencies = {
      critical: [
        {
          from: 'Frontend Development',
          to: 'API Development',
          type: 'blocking',
          impact: 'high',
          description: 'Frontend team waiting for API endpoints'
        },
        {
          from: 'Testing',
          to: 'Feature Development',
          type: 'sequential',
          impact: 'medium',
          description: 'Testing depends on completed features'
        }
      ],
      suggestions: [
        'Consider parallel development of API and frontend components',
        'Implement mock APIs for frontend development',
        'Set up continuous integration for faster feedback'
      ],
      riskAssessment: {
        level: 'medium',
        factors: [
          'Some blocking dependencies identified',
          'Resource allocation could be optimized',
          'Timeline buffers are adequate'
        ]
      }
    };

    res.json({
      success: true,
      data: dependencies,
      generatedAt: new Date()
    });

  } catch (error) {
    console.error('AI dependencies error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to analyze dependencies'
    });
  }
});

module.exports = router;