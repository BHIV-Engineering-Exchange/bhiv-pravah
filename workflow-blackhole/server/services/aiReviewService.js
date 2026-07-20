const axios = require('axios');
const AIReview = require('../models/AIReview');
const Task = require('../models/Task');
const TaskSubmission = require('../models/TaskSubmission');
const { auditLogger } = require('./complianceAuditLogger');

class AIReviewService {
  constructor() {
    this.openaiApiKey = process.env.OPENAI_API_KEY;
    this.geminiApiKey = process.env.GEMINI_API_KEY;
    this.groqApiKey = process.env.GROQ_API_KEY;
  }

  async reviewSubmission(taskId, submissionId, repositoryUrl, adminId, aiProvider = 'openai') {
    try {
      // Create initial review record
      const review = new AIReview({
        taskId,
        submissionId,
        repositoryUrl,
        reviewStatus: 'analyzing',
        aiProvider,
        reviewedBy: adminId
      });
      await review.save();

      // Get task details for context
      const task = await Task.findById(taskId).populate('assignee');
      const submission = await TaskSubmission.findById(submissionId);

      if (!task || !submission) {
        throw new Error('Task or submission not found');
      }

      // Analyze repository with AI
      const analysisResult = await this.analyzeWithAI(task, submission, repositoryUrl, aiProvider);

      // Update review with results
      review.reviewStatus = 'completed';
      review.overallScore = analysisResult.overallScore;
      review.completionPercentage = analysisResult.completionPercentage;
      review.codeQualityScore = analysisResult.codeQualityScore;
      review.requirementsFulfillment = analysisResult.requirementsFulfillment;
      review.aiSummary = analysisResult.summary;
      review.strengths = analysisResult.strengths;
      review.weaknesses = analysisResult.weaknesses;
      review.missingRequirements = analysisResult.missingRequirements;
      review.recommendations = analysisResult.recommendations;
      review.codeAnalysis = analysisResult.codeAnalysis;

      await review.save();

      // Log the review
      await auditLogger.logEvent(
        adminId,
        'ai_review_completed',
        `task/${taskId}/submission/${submissionId}`,
        {
          repository_url: repositoryUrl,
          overall_score: analysisResult.overallScore,
          ai_provider: aiProvider
        }
      );

      return review;
    } catch (error) {
      console.error('Error reviewing submission:', error);
      
      // Update review status to failed
      if (review) {
        review.reviewStatus = 'failed';
        review.errorMessage = error.message;
        await review.save();
      }

      throw error;
    }
  }

  async analyzeWithAI(task, submission, repositoryUrl, aiProvider) {
    const prompt = this.buildAnalysisPrompt(task, submission, repositoryUrl);
    
    let aiResponse;
    switch (aiProvider) {
      case 'openai':
        aiResponse = await this.callOpenAI(prompt);
        break;
      case 'gemini':
        aiResponse = await this.callGemini(prompt);
        break;
      case 'groq':
        aiResponse = await this.callGroq(prompt);
        break;
      default:
        throw new Error(`Unsupported AI provider: ${aiProvider}`);
    }

    return this.parseAIResponse(aiResponse);
  }

  buildAnalysisPrompt(task, submission, repositoryUrl) {
    return `
You are an expert code reviewer analyzing a task submission. Please provide a comprehensive review.

TASK DETAILS:
- Title: ${task.title}
- Description: ${task.description}
- Priority: ${task.priority}
- Due Date: ${task.dueDate}

SUBMISSION DETAILS:
- Repository URL: ${repositoryUrl}
- Submission Notes: ${submission.notes || 'No notes provided'}
- Files Submitted: ${submission.files?.length || 0}

Please analyze this submission and provide a JSON response with the following structure:
{
  "overallScore": 85,
  "completionPercentage": 90,
  "codeQualityScore": 80,
  "requirementsFulfillment": 85,
  "summary": "Brief overall assessment",
  "strengths": ["List of strengths"],
  "weaknesses": ["List of weaknesses"],
  "missingRequirements": [
    {
      "requirement": "Missing feature description",
      "severity": "high",
      "suggestion": "How to fix it"
    }
  ],
  "recommendations": ["List of recommendations"],
  "codeAnalysis": {
    "filesAnalyzed": 15,
    "linesOfCode": 500,
    "complexity": "Medium",
    "testCoverage": "Good",
    "documentation": "Adequate"
  }
}

Focus on:
1. How well the submission meets the task requirements
2. Code quality and best practices
3. Missing functionality or requirements
4. Areas for improvement
5. Overall completeness

Provide scores from 0-100 and be constructive in feedback.
`;
  }

  async callOpenAI(prompt) {
    if (!this.openaiApiKey) {
      throw new Error('OpenAI API key not configured');
    }

    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are an expert code reviewer. Always respond with valid JSON.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.3,
      max_tokens: 2000
    }, {
      headers: {
        'Authorization': `Bearer ${this.openaiApiKey}`,
        'Content-Type': 'application/json'
      }
    });

    return response.data.choices[0].message.content;
  }

  async callGemini(prompt) {
    if (!this.geminiApiKey) {
      throw new Error('Gemini API key not configured');
    }

    const response = await axios.post(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${this.geminiApiKey}`, {
      contents: [{
        parts: [{
          text: prompt
        }]
      }]
    });

    return response.data.candidates[0].content.parts[0].text;
  }

  async callGroq(prompt) {
    if (!this.groqApiKey) {
      throw new Error('Groq API key not configured');
    }

    const response = await axios.post('https://api.groq.com/openai/v1/chat/completions', {
      model: 'llama3-8b-8192',
      messages: [
        {
          role: 'system',
          content: 'You are an expert code reviewer. Always respond with valid JSON.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.3,
      max_tokens: 2000
    }, {
      headers: {
        'Authorization': `Bearer ${this.groqApiKey}`,
        'Content-Type': 'application/json'
      }
    });

    return response.data.choices[0].message.content;
  }

  parseAIResponse(aiResponse) {
    try {
      // Extract JSON from response (in case there's extra text)
      const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
      const jsonStr = jsonMatch ? jsonMatch[0] : aiResponse;
      
      const parsed = JSON.parse(jsonStr);
      
      // Validate and set defaults
      return {
        overallScore: Math.min(100, Math.max(0, parsed.overallScore || 0)),
        completionPercentage: Math.min(100, Math.max(0, parsed.completionPercentage || 0)),
        codeQualityScore: Math.min(100, Math.max(0, parsed.codeQualityScore || 0)),
        requirementsFulfillment: Math.min(100, Math.max(0, parsed.requirementsFulfillment || 0)),
        summary: parsed.summary || 'No summary provided',
        strengths: Array.isArray(parsed.strengths) ? parsed.strengths : [],
        weaknesses: Array.isArray(parsed.weaknesses) ? parsed.weaknesses : [],
        missingRequirements: Array.isArray(parsed.missingRequirements) ? parsed.missingRequirements : [],
        recommendations: Array.isArray(parsed.recommendations) ? parsed.recommendations : [],
        codeAnalysis: {
          filesAnalyzed: parsed.codeAnalysis?.filesAnalyzed || 0,
          linesOfCode: parsed.codeAnalysis?.linesOfCode || 0,
          complexity: parsed.codeAnalysis?.complexity || 'Unknown',
          testCoverage: parsed.codeAnalysis?.testCoverage || 'Unknown',
          documentation: parsed.codeAnalysis?.documentation || 'Unknown'
        }
      };
    } catch (error) {
      console.error('Error parsing AI response:', error);
      
      // Return default analysis if parsing fails
      return {
        overallScore: 50,
        completionPercentage: 50,
        codeQualityScore: 50,
        requirementsFulfillment: 50,
        summary: 'AI analysis failed - manual review required',
        strengths: ['Submission received'],
        weaknesses: ['Unable to analyze automatically'],
        missingRequirements: [{
          requirement: 'Manual review needed',
          severity: 'medium',
          suggestion: 'Please review manually due to AI analysis failure'
        }],
        recommendations: ['Conduct manual code review'],
        codeAnalysis: {
          filesAnalyzed: 0,
          linesOfCode: 0,
          complexity: 'Unknown',
          testCoverage: 'Unknown',
          documentation: 'Unknown'
        }
      };
    }
  }

  async getReviewsByTask(taskId) {
    return await AIReview.find({ taskId })
      .populate('reviewedBy', 'name email')
      .sort({ reviewedAt: -1 });
  }

  async getReviewById(reviewId) {
    return await AIReview.findById(reviewId)
      .populate('taskId', 'title description')
      .populate('submissionId')
      .populate('reviewedBy', 'name email');
  }

  async bulkReviewSubmissions(submissionIds, adminId, aiProvider = 'openai') {
    const results = [];
    
    for (const submissionId of submissionIds) {
      try {
        const submission = await TaskSubmission.findById(submissionId);
        if (!submission || !submission.repositoryUrl) {
          results.push({
            submissionId,
            success: false,
            error: 'Submission not found or no repository URL'
          });
          continue;
        }

        const review = await this.reviewSubmission(
          submission.task,
          submissionId,
          submission.repositoryUrl,
          adminId,
          aiProvider
        );

        results.push({
          submissionId,
          success: true,
          reviewId: review._id,
          overallScore: review.overallScore
        });
      } catch (error) {
        results.push({
          submissionId,
          success: false,
          error: error.message
        });
      }
    }

    return results;
  }
}

module.exports = new AIReviewService();