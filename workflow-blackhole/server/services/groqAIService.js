const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

class GroqAIService {
  constructor() {
    this.apiKey = process.env.GROQ_API_KEY;
    this.apiUrl = 'https://api.groq.com/openai/v1/chat/completions';
    this.model = process.env.GROQ_MODEL || 'llama-3.2-90b-vision-preview'; // Use env variable or fallback
    this.maxRetries = 3;
    this.retryDelay = 1000;
  }

  /**
   * Analyze screenshot content using Groq AI
   */
  async analyzeScreenshot(screenshotPath, context = {}) {
    if (!this.apiKey) {
      console.warn('Groq API key not configured, skipping AI analysis');
      return null;
    }

    // Check if model supports vision
    const isVisionModel = this.model.includes('vision') || this.model.includes('llava');

    if (!isVisionModel) {
      console.warn(`Model ${this.model} does not support vision. Using fallback analysis.`);
      return this.createFallbackAnalysis(context);
    }

    try {
      // Convert image to base64
      const imageBase64 = await this.imageToBase64(screenshotPath);

      // Prepare analysis prompt
      const prompt = this.buildAnalysisPrompt(context);

      // Call Groq API with retry logic
      const response = await this.callGroqAPIWithRetry({
        model: this.model,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: prompt
              },
              {
                type: "image_url",
                image_url: {
                  url: `data:image/jpeg;base64,${imageBase64}`
                }
              }
            ]
          }
        ],
        max_tokens: 1000,
        temperature: 0.3
      });

      // Parse and structure the response
      return this.parseAnalysisResponse(response.data, context);

    } catch (error) {
      console.error('Groq AI analysis error:', error);
      return this.createFallbackAnalysis(context);
    }
  }

  /**
   * Build analysis prompt based on context
   */
  buildAnalysisPrompt(context) {
    const { currentTask, applicationData, employeeId } = context;
    
    let prompt = `Analyze this screenshot of an employee's computer screen and provide insights in JSON format.

Please analyze:
1. What type of content is being viewed (e.g., "social media", "video streaming", "work documents", "coding", "shopping")
2. Describe the specific activity (e.g., "watching YouTube cooking videos", "browsing Facebook feed", "reading technical documentation")
3. Assess the content's appropriateness for a workplace environment
4. Rate the content's risk level (low/medium/high) for productivity and security`;

    if (currentTask) {
      prompt += `\n5. Compare this activity to the employee's current assigned task: "${currentTask.title}" - ${currentTask.description}
6. Rate task relevance (0-100%) and explain the connection or lack thereof`;
    }

    if (applicationData?.url) {
      prompt += `\n\nThe employee is currently on: ${applicationData.url}`;
    }
    
    if (applicationData?.name) {
      prompt += `\nApplication: ${applicationData.name}`;
    }

    prompt += `\n\nRespond in this exact JSON format:
{
  "contentType": "brief category of content",
  "activityDescription": "detailed description of what the user is doing",
  "workplaceAppropriateness": "appropriate/questionable/inappropriate",
  "contentRisk": {
    "level": "low/medium/high",
    "reasons": ["reason1", "reason2"]
  },
  "taskRelevance": {
    "score": 0-100,
    "explanation": "explanation of relevance or lack thereof"
  },
  "recommendations": ["action1", "action2"],
  "confidence": 0-100
}`;

    return prompt;
  }

  /**
   * Parse AI response and structure data
   */
  parseAnalysisResponse(response, context) {
    try {
      const content = response.choices[0]?.message?.content;
      if (!content) {
        throw new Error('No content in AI response');
      }

      // Extract JSON from response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in AI response');
      }

      const analysis = JSON.parse(jsonMatch[0]);
      
      // Add metadata
      analysis.timestamp = new Date();
      analysis.model = this.model;
      analysis.context = {
        employeeId: context.employeeId,
        hasCurrentTask: !!context.currentTask,
        applicationUrl: context.applicationData?.url,
        applicationName: context.applicationData?.name
      };

      // Validate and sanitize
      return this.validateAnalysis(analysis);

    } catch (error) {
      console.error('Error parsing AI response:', error);
      return this.createFallbackAnalysis(context);
    }
  }

  /**
   * Validate and sanitize AI analysis
   */
  validateAnalysis(analysis) {
    const validated = {
      contentType: analysis.contentType || 'Unknown Content',
      activityDescription: analysis.activityDescription || 'Unable to determine activity',
      workplaceAppropriateness: ['appropriate', 'questionable', 'inappropriate'].includes(analysis.workplaceAppropriateness) 
        ? analysis.workplaceAppropriateness : 'questionable',
      contentRisk: {
        level: ['low', 'medium', 'high'].includes(analysis.contentRisk?.level) 
          ? analysis.contentRisk.level : 'medium',
        reasons: Array.isArray(analysis.contentRisk?.reasons) 
          ? analysis.contentRisk.reasons.slice(0, 5) : ['Unable to assess risk']
      },
      taskRelevance: {
        score: Math.max(0, Math.min(100, analysis.taskRelevance?.score || 0)),
        explanation: analysis.taskRelevance?.explanation || 'No task relevance analysis available'
      },
      recommendations: Array.isArray(analysis.recommendations) 
        ? analysis.recommendations.slice(0, 3) : ['Review employee activity'],
      confidence: Math.max(0, Math.min(100, analysis.confidence || 50)),
      timestamp: analysis.timestamp,
      model: analysis.model,
      context: analysis.context
    };

    return validated;
  }

  /**
   * Create fallback analysis when AI fails
   */
  createFallbackAnalysis(context) {
    const { applicationData, currentTask } = context;
    
    return {
      contentType: 'Unknown Content',
      activityDescription: `Accessing ${applicationData?.name || applicationData?.url || 'unknown application'}`,
      workplaceAppropriateness: 'questionable',
      contentRisk: {
        level: 'medium',
        reasons: ['Unable to analyze content automatically']
      },
      taskRelevance: {
        score: currentTask ? 25 : 0,
        explanation: currentTask 
          ? 'Unable to determine relevance to assigned task automatically'
          : 'No current task assigned for comparison'
      },
      recommendations: [
        'Manual review recommended',
        'Consider adding to whitelist if appropriate'
      ],
      confidence: 10,
      timestamp: new Date(),
      model: 'fallback',
      context: {
        employeeId: context.employeeId,
        hasCurrentTask: !!currentTask,
        applicationUrl: applicationData?.url,
        applicationName: applicationData?.name,
        fallbackReason: 'AI analysis failed'
      }
    };
  }

  /**
   * Call Groq API with retry logic
   */
  async callGroqAPIWithRetry(payload, retryCount = 0) {
    try {
      const response = await axios.post(this.apiUrl, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000 // 30 second timeout
      });

      return response;

    } catch (error) {
      if (retryCount < this.maxRetries) {
        console.log(`Groq API call failed, retrying... (${retryCount + 1}/${this.maxRetries})`);
        await this.delay(this.retryDelay * (retryCount + 1));
        return this.callGroqAPIWithRetry(payload, retryCount + 1);
      }
      
      throw error;
    }
  }

  /**
   * Convert image file to base64
   */
  async imageToBase64(imagePath) {
    try {
      const imageBuffer = await fs.readFile(imagePath);
      return imageBuffer.toString('base64');
    } catch (error) {
      console.error('Error converting image to base64:', error);
      throw new Error('Failed to process image for AI analysis');
    }
  }

  /**
   * Analyze multiple screenshots for pattern detection
   */
  async analyzeScreenshotPattern(screenshots, context = {}) {
    if (!screenshots || screenshots.length === 0) return null;

    try {
      // Analyze the most recent screenshot with context from previous ones
      const latestScreenshot = screenshots[screenshots.length - 1];
      const previousActivities = screenshots.slice(0, -1).map(s => s.activityDescription).join(', ');
      
      const enhancedContext = {
        ...context,
        previousActivities,
        sessionDuration: screenshots.length,
        patternAnalysis: true
      };

      const analysis = await this.analyzeScreenshot(latestScreenshot.file_path, enhancedContext);
      
      if (analysis) {
        // Add pattern-specific insights
        analysis.patternInsights = {
          sessionLength: screenshots.length,
          consistentActivity: this.detectConsistentActivity(screenshots),
          escalationLevel: this.calculateEscalationLevel(screenshots),
          timeSpent: this.calculateTimeSpent(screenshots)
        };
      }

      return analysis;

    } catch (error) {
      console.error('Error analyzing screenshot pattern:', error);
      return null;
    }
  }

  /**
   * Detect consistent activity patterns
   */
  detectConsistentActivity(screenshots) {
    if (screenshots.length < 2) return false;
    
    const activities = screenshots.map(s => s.activityDescription || '').filter(a => a);
    const uniqueActivities = new Set(activities);
    
    return uniqueActivities.size <= 2; // Consistent if only 1-2 different activities
  }

  /**
   * Calculate escalation level based on screenshot sequence
   */
  calculateEscalationLevel(screenshots) {
    const riskLevels = screenshots.map(s => {
      if (s.contentRisk?.level === 'high') return 3;
      if (s.contentRisk?.level === 'medium') return 2;
      return 1;
    });

    const avgRisk = riskLevels.reduce((sum, risk) => sum + risk, 0) / riskLevels.length;
    
    if (avgRisk >= 2.5) return 'high';
    if (avgRisk >= 1.5) return 'medium';
    return 'low';
  }

  /**
   * Calculate estimated time spent on activity
   */
  calculateTimeSpent(screenshots) {
    if (screenshots.length < 2) return 0;
    
    const firstTimestamp = new Date(screenshots[0].timestamp);
    const lastTimestamp = new Date(screenshots[screenshots.length - 1].timestamp);
    
    return Math.round((lastTimestamp - firstTimestamp) / 1000 / 60); // Minutes
  }

  /**
   * Utility delay function
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Analyze attendance patterns using AI
   */
  async analyzeAttendancePatterns(attendanceData, userContext = {}) {
    try {
      const prompt = this.buildAttendanceAnalysisPrompt(attendanceData, userContext);

      const response = await this.callGroqAPIWithRetry({
        model: 'llama3-8b-8192', // Use text model for attendance analysis
        messages: [
          {
            role: "system",
            content: "You are an AI attendance analyst specializing in workforce analytics, pattern recognition, and productivity insights. Provide detailed, actionable analysis in JSON format."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        max_tokens: 1500,
        temperature: 0.2
      });

      return this.parseAttendanceAnalysisResponse(response.data, attendanceData);

    } catch (error) {
      console.error('Attendance pattern analysis error:', error);
      return this.createFallbackAttendanceAnalysis(attendanceData);
    }
  }

  /**
   * Build attendance analysis prompt
   */
  buildAttendanceAnalysisPrompt(attendanceData, userContext) {
    const stats = this.calculateAttendanceStats(attendanceData);

    return `
Analyze the following employee attendance data and provide insights:

EMPLOYEE CONTEXT:
- Role: ${userContext.role || 'Employee'}
- Department: ${userContext.department || 'Unknown'}
- Employment Type: ${userContext.tag || 'Employee'}
- Analysis Period: ${attendanceData.length} days

ATTENDANCE STATISTICS:
- Total Days: ${stats.totalDays}
- Present Days: ${stats.presentDays}
- Absent Days: ${stats.absentDays}
- Attendance Rate: ${stats.attendanceRate}%
- Average Hours/Day: ${stats.avgHours}
- Total Overtime: ${stats.totalOvertime} hours
- Discrepancies: ${stats.discrepancies}

RECENT PATTERN (Last 14 days):
${attendanceData.slice(-14).map(day =>
  `${day.date}: ${day.isPresent ? 'Present' : 'Absent'} | Hours: ${day.hoursWorked || 0} | ${day.hasDiscrepancy ? 'DISCREPANCY' : 'OK'}`
).join('\n')}

Please provide analysis in this JSON format:
{
  "patterns": {
    "attendanceTrend": "improving/declining/stable",
    "punctualityPattern": "description",
    "workingHoursConsistency": "high/medium/low"
  },
  "risks": {
    "level": "low/medium/high",
    "factors": ["list of risk factors"],
    "probability": "percentage"
  },
  "insights": [
    "key insight 1",
    "key insight 2"
  ],
  "recommendations": [
    "specific recommendation 1",
    "specific recommendation 2"
  ],
  "predictions": {
    "nextMonthAttendance": "percentage",
    "potentialIssues": ["list of potential issues"]
  }
}
`;
  }

  /**
   * Calculate attendance statistics
   */
  calculateAttendanceStats(attendanceData) {
    const totalDays = attendanceData.length;
    const presentDays = attendanceData.filter(d => d.isPresent).length;
    const absentDays = totalDays - presentDays;
    const attendanceRate = totalDays > 0 ? Math.round((presentDays / totalDays) * 100) : 0;

    const totalHours = attendanceData.reduce((sum, d) => sum + (d.hoursWorked || 0), 0);
    const avgHours = presentDays > 0 ? Math.round((totalHours / presentDays) * 100) / 100 : 0;

    const totalOvertime = attendanceData.reduce((sum, d) => sum + (d.overtimeHours || 0), 0);
    const discrepancies = attendanceData.filter(d => d.hasDiscrepancy).length;

    return {
      totalDays,
      presentDays,
      absentDays,
      attendanceRate,
      avgHours,
      totalOvertime,
      discrepancies
    };
  }

  /**
   * Parse AI attendance analysis response
   */
  parseAttendanceAnalysisResponse(response, attendanceData) {
    try {
      const content = response.choices[0]?.message?.content;
      if (!content) throw new Error('No content in response');

      // Try to parse JSON response
      let analysis;
      try {
        // Extract JSON from response if it's wrapped in text
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        const jsonStr = jsonMatch ? jsonMatch[0] : content;
        analysis = JSON.parse(jsonStr);
      } catch (parseError) {
        // If JSON parsing fails, create structured response from text
        analysis = this.extractInsightsFromText(content);
      }

      // Enhance with calculated metrics
      return {
        ...analysis,
        metadata: {
          analysisDate: new Date(),
          dataPoints: attendanceData.length,
          confidence: this.calculateAnalysisConfidence(attendanceData),
          aiModel: 'llama3-8b-8192'
        },
        metrics: this.calculateAdvancedMetrics(attendanceData)
      };

    } catch (error) {
      console.error('Failed to parse attendance analysis:', error);
      return this.createFallbackAttendanceAnalysis(attendanceData);
    }
  }

  /**
   * Extract insights from text when JSON parsing fails
   */
  extractInsightsFromText(content) {
    const insights = [];
    const recommendations = [];

    // Simple text parsing for insights
    const lines = content.split('\n');
    lines.forEach(line => {
      if (line.toLowerCase().includes('insight') || line.toLowerCase().includes('pattern')) {
        insights.push(line.trim());
      }
      if (line.toLowerCase().includes('recommend') || line.toLowerCase().includes('suggest')) {
        recommendations.push(line.trim());
      }
    });

    return {
      patterns: {
        attendanceTrend: "stable",
        punctualityPattern: "Analysis from text content",
        workingHoursConsistency: "medium"
      },
      risks: {
        level: "medium",
        factors: ["Requires detailed analysis"],
        probability: "50%"
      },
      insights: insights.length > 0 ? insights : ["AI analysis completed"],
      recommendations: recommendations.length > 0 ? recommendations : ["Continue monitoring"],
      predictions: {
        nextMonthAttendance: "85%",
        potentialIssues: ["Monitor for patterns"]
      }
    };
  }

  /**
   * Test AI service connectivity
   */
  async testConnection() {
    if (!this.apiKey) {
      return { success: false, error: 'API key not configured' };
    }

    try {
      // Use the configured model or a fallback text model for testing
      const testModel = this.model.includes('vision') ? 'llama3-8b-8192' : this.model;

      const response = await axios.post(this.apiUrl, {
        model: testModel,
        messages: [
          {
            role: "user",
            content: "Hello, this is a test message. Please respond with 'AI service is working'."
          }
        ],
        max_tokens: 50
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });

      return {
        success: true,
        message: 'Groq AI service is connected and working',
        model: this.model
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        details: error.response?.data
      };
    }
  }

  /**
   * Calculate analysis confidence based on data quality
   */
  calculateAnalysisConfidence(attendanceData) {
    if (attendanceData.length < 7) return 0.3; // Low confidence with less than a week
    if (attendanceData.length < 30) return 0.6; // Medium confidence with less than a month
    if (attendanceData.length < 90) return 0.8; // High confidence with less than 3 months
    return 0.9; // Very high confidence with 3+ months
  }

  /**
   * Calculate advanced attendance metrics
   */
  calculateAdvancedMetrics(attendanceData) {
    const presentDays = attendanceData.filter(d => d.isPresent);
    const workingHours = presentDays.map(d => d.hoursWorked || 0);

    // Calculate variance in working hours
    const avgHours = workingHours.reduce((sum, h) => sum + h, 0) / workingHours.length;
    const variance = workingHours.reduce((sum, h) => sum + Math.pow(h - avgHours, 2), 0) / workingHours.length;
    const standardDeviation = Math.sqrt(variance);

    // Calculate punctuality score
    const punctualityScore = this.calculatePunctualityScore(attendanceData);

    // Calculate consistency score
    const consistencyScore = this.calculateConsistencyScore(attendanceData);

    return {
      workingHoursVariance: Math.round(variance * 100) / 100,
      workingHoursStdDev: Math.round(standardDeviation * 100) / 100,
      punctualityScore,
      consistencyScore,
      reliabilityIndex: Math.round((punctualityScore + consistencyScore) / 2)
    };
  }

  /**
   * Calculate punctuality score
   */
  calculatePunctualityScore(attendanceData) {
    const workingDays = attendanceData.filter(d => d.isPresent && (d.biometricTimeIn || d.startDayTime));
    if (workingDays.length === 0) return 0;

    const standardStartTime = 9; // 9 AM
    const punctualDays = workingDays.filter(day => {
      const checkInTime = day.biometricTimeIn || day.startDayTime;
      const checkInHour = checkInTime.getHours() + checkInTime.getMinutes() / 60;
      return checkInHour <= standardStartTime + 0.25; // 15 minutes grace period
    });

    return Math.round((punctualDays.length / workingDays.length) * 100);
  }

  /**
   * Calculate consistency score
   */
  calculateConsistencyScore(attendanceData) {
    const totalDays = attendanceData.length;
    const presentDays = attendanceData.filter(d => d.isPresent).length;
    const verifiedDays = attendanceData.filter(d => d.isVerified).length;
    const discrepancies = attendanceData.filter(d => d.hasDiscrepancy).length;

    const attendanceRate = presentDays / totalDays;
    const verificationRate = verifiedDays / totalDays;
    const discrepancyRate = discrepancies / totalDays;

    const score = (attendanceRate * 0.4) + (verificationRate * 0.4) - (discrepancyRate * 0.2);
    return Math.max(0, Math.min(100, Math.round(score * 100)));
  }

  /**
   * Create fallback analysis when AI fails
   */
  createFallbackAttendanceAnalysis(attendanceData) {
    const stats = this.calculateAttendanceStats(attendanceData);
    const metrics = this.calculateAdvancedMetrics(attendanceData);

    let attendanceTrend = 'stable';
    let riskLevel = 'low';
    const insights = [];
    const recommendations = [];

    if (stats.attendanceRate < 80) {
      attendanceTrend = 'declining';
      riskLevel = 'high';
      insights.push('Attendance rate is below acceptable threshold');
      recommendations.push('Implement attendance improvement plan');
    } else if (stats.attendanceRate > 95) {
      attendanceTrend = 'excellent';
      insights.push('Excellent attendance record');
    }

    if (metrics.punctualityScore < 80) {
      insights.push('Punctuality needs improvement');
      recommendations.push('Consider flexible working hours or punctuality training');
    }

    if (stats.discrepancies > stats.totalDays * 0.1) {
      riskLevel = 'medium';
      insights.push('High number of attendance discrepancies detected');
      recommendations.push('Review attendance tracking system and processes');
    }

    return {
      patterns: {
        attendanceTrend,
        punctualityPattern: `${metrics.punctualityScore}% punctuality rate`,
        workingHoursConsistency: metrics.workingHoursStdDev < 1 ? 'high' : metrics.workingHoursStdDev < 2 ? 'medium' : 'low'
      },
      risks: {
        level: riskLevel,
        factors: insights.filter(i => i.includes('risk') || i.includes('below') || i.includes('high')),
        probability: riskLevel === 'high' ? '70%' : riskLevel === 'medium' ? '40%' : '15%'
      },
      insights: insights.length > 0 ? insights : ['Attendance patterns are within normal range'],
      recommendations: recommendations.length > 0 ? recommendations : ['Continue current attendance practices'],
      predictions: {
        nextMonthAttendance: `${Math.max(75, Math.min(100, stats.attendanceRate + (Math.random() * 10 - 5)))}%`,
        potentialIssues: riskLevel === 'high' ? ['Continued attendance decline', 'Performance impact'] : ['Monitor for seasonal variations']
      },
      metadata: {
        analysisDate: new Date(),
        dataPoints: attendanceData.length,
        confidence: this.calculateAnalysisConfidence(attendanceData),
        aiModel: 'fallback-analysis'
      },
      metrics
    };
  }

  /**
   * Detect attendance anomalies
   */
  async detectAttendanceAnomalies(attendanceData, threshold = 0.7) {
    try {
      const anomalies = [];

      // Simple anomaly detection based on patterns
      for (let i = 0; i < attendanceData.length; i++) {
        const day = attendanceData[i];
        const anomalyScore = this.calculateSimpleAnomalyScore(day, attendanceData, i);

        if (anomalyScore > threshold) {
          anomalies.push({
            date: day.date,
            type: this.classifySimpleAnomaly(day),
            score: anomalyScore,
            description: this.generateAnomalyDescription(day),
            severity: anomalyScore > 0.9 ? 'high' : anomalyScore > 0.8 ? 'medium' : 'low',
            recommendations: this.generateAnomalyRecommendations(day)
          });
        }
      }

      return {
        anomalies,
        summary: {
          totalAnomalies: anomalies.length,
          highSeverity: anomalies.filter(a => a.severity === 'high').length,
          mediumSeverity: anomalies.filter(a => a.severity === 'medium').length,
          lowSeverity: anomalies.filter(a => a.severity === 'low').length
        }
      };

    } catch (error) {
      console.error('Anomaly detection error:', error);
      return { anomalies: [], summary: { totalAnomalies: 0 } };
    }
  }

  /**
   * Calculate simple anomaly score
   */
  calculateSimpleAnomalyScore(day, allData, index) {
    let score = 0;

    // Check for unusual working hours
    if (day.hoursWorked > 12) score += 0.3;
    if (day.hoursWorked < 2 && day.isPresent) score += 0.4;

    // Check for discrepancies
    if (day.hasDiscrepancy) score += 0.3;

    // Check for unusual patterns
    if (day.isPresent && !day.isVerified) score += 0.2;

    // Check against recent pattern
    const recentDays = allData.slice(Math.max(0, index - 7), index);
    const avgHours = recentDays.reduce((sum, d) => sum + (d.hoursWorked || 0), 0) / recentDays.length;

    if (Math.abs(day.hoursWorked - avgHours) > 3) score += 0.2;

    return Math.min(1, score);
  }

  /**
   * Classify simple anomaly type
   */
  classifySimpleAnomaly(day) {
    if (day.hoursWorked > 12) return 'excessive_hours';
    if (day.hoursWorked < 2 && day.isPresent) return 'insufficient_hours';
    if (day.hasDiscrepancy) return 'time_discrepancy';
    if (day.isPresent && !day.isVerified) return 'unverified_attendance';
    return 'pattern_deviation';
  }

  /**
   * Generate anomaly description
   */
  generateAnomalyDescription(day) {
    const type = this.classifySimpleAnomaly(day);
    const descriptions = {
      'excessive_hours': `Worked ${day.hoursWorked} hours, which is unusually high`,
      'insufficient_hours': `Only worked ${day.hoursWorked} hours despite being present`,
      'time_discrepancy': 'Discrepancy detected between biometric and app check-in times',
      'unverified_attendance': 'Attendance recorded but not verified through standard process',
      'pattern_deviation': 'Attendance pattern deviates from normal behavior'
    };
    return descriptions[type] || 'Unusual attendance pattern detected';
  }

  /**
   * Generate anomaly recommendations
   */
  generateAnomalyRecommendations(day) {
    const type = this.classifySimpleAnomaly(day);
    const recommendations = {
      'excessive_hours': ['Review workload distribution', 'Check for overtime approval', 'Monitor for burnout'],
      'insufficient_hours': ['Verify reason for short day', 'Check for early departure approval', 'Review productivity'],
      'time_discrepancy': ['Investigate timing systems', 'Verify employee location', 'Check for technical issues'],
      'unverified_attendance': ['Complete verification process', 'Review attendance policies', 'Ensure proper check-in'],
      'pattern_deviation': ['Monitor for consistency', 'Discuss with employee', 'Review recent changes']
    };
    return recommendations[type] || ['Monitor situation', 'Follow up with employee'];
  }
}

module.exports = new GroqAIService();
