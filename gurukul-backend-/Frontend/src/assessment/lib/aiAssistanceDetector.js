/**
 * AI Assistance Detection Service
 * Balanced approach to detect AI-generated responses
 * Measures effort/context; flags laziness/straight copy; not harsh ban
 */

export class AIAssistanceDetector {
  /**
   * Analyze student response for AI assistance indicators
   * Returns detection score (0-100) and specific flags
   */
  static analyzeResponse(response, question, timeSpent = 0) {
    const indicators = {
      suspicionScore: 0,
      flags: [],
      effort: 0,
      context: 0,
      confidence: 'low'
    };

    // 1. Response length analysis
    const lengthAnalysis = this.analyzeResponseLength(response);
    indicators.suspicionScore += lengthAnalysis.suspicionPoints;
    if (lengthAnalysis.flag) indicators.flags.push(lengthAnalysis.flag);

    // 2. Language pattern analysis
    const languageAnalysis = this.analyzeLanguagePatterns(response);
    indicators.suspicionScore += languageAnalysis.suspicionPoints;
    if (languageAnalysis.flag) indicators.flags.push(languageAnalysis.flag);

    // 3. Time spent analysis
    const timeAnalysis = this.analyzeTimeSpent(response, timeSpent);
    indicators.suspicionScore += timeAnalysis.suspicionPoints;
    if (timeAnalysis.flag) indicators.flags.push(timeAnalysis.flag);

    // 4. Context relevance
    const contextAnalysis = this.analyzeContextRelevance(response, question);
    indicators.context = contextAnalysis.contextScore;
    indicators.suspicionScore += contextAnalysis.suspicionPoints;
    if (contextAnalysis.flag) indicators.flags.push(contextAnalysis.flag);

    // 5. Effort indicators
    indicators.effort = this.calculateEffortScore(response, timeSpent);

    // 6. AI-specific patterns
    const aiPatternsAnalysis = this.detectAIPatterns(response);
    indicators.suspicionScore += aiPatternsAnalysis.suspicionPoints;
    if (aiPatternsAnalysis.flag) indicators.flags.push(aiPatternsAnalysis.flag);

    // Determine confidence level
    indicators.confidence = this.determineConfidence(indicators.suspicionScore, indicators.flags.length);

    // Classify detection level
    indicators.detectionLevel = this.classifyDetectionLevel(indicators.suspicionScore);

    return indicators;
  }

  /**
   * Analyze response length (AI responses often have specific length patterns)
   */
  static analyzeResponseLength(response) {
    const wordCount = response.trim().split(/\s+/).length;
    let suspicionPoints = 0;
    let flag = null;

    // Very short responses (lazy)
    if (wordCount < 5) {
      suspicionPoints = 15;
      flag = 'Minimal effort - very short response';
    }
    // Suspiciously perfect length (AI often generates ~50-150 words)
    else if (wordCount > 100 && wordCount < 200) {
      suspicionPoints = 10;
    }
    // Overly long responses (possible AI elaboration)
    else if (wordCount > 300) {
      suspicionPoints = 20;
      flag = 'Unusually lengthy response - possible AI elaboration';
    }

    return { suspicionPoints, flag, wordCount };
  }

  /**
   * Detect AI-specific language patterns
   */
  static analyzeLanguagePatterns(response) {
    let suspicionPoints = 0;
    let flag = null;

    const lowerResponse = response.toLowerCase();

    // Common AI phrases
    const aiPhrases = [
      'as an ai', 
      'i apologize', 
      'i cannot', 
      'however, it is important to note',
      'in conclusion',
      'it is worth noting',
      'comprehensive understanding',
      'multifaceted',
      'delve into',
      'paradigm shift',
      'synergy',
      'leverage',
      'furthermore',
      'moreover',
      'it should be noted'
    ];

    let aiPhraseCount = 0;
    aiPhrases.forEach(phrase => {
      if (lowerResponse.includes(phrase)) {
        aiPhraseCount++;
        suspicionPoints += 5;
      }
    });

    if (aiPhraseCount >= 3) {
      flag = `Contains ${aiPhraseCount} AI-typical phrases`;
      suspicionPoints += 15;
    }

    // Perfect grammar without typos (unusual for quick responses)
    const hasTypos = /\b(teh|recieve|occured|thier|seperate)\b/i.test(response);
    const hasCasualLanguage = /\b(yeah|nah|gonna|wanna|kinda|sorta)\b/i.test(response);
    
    if (!hasTypos && !hasCasualLanguage && response.length > 100) {
      suspicionPoints += 10;
    }

    return { suspicionPoints, flag };
  }

  /**
   * Analyze time spent on question
   */
  static analyzeTimeSpent(response, timeSpent) {
    let suspicionPoints = 0;
    let flag = null;

    const wordCount = response.trim().split(/\s+/).length;
    const expectedTime = Math.max(wordCount * 1.5, 10); // ~1.5 seconds per word minimum

    if (timeSpent > 0 && timeSpent < expectedTime && wordCount > 50) {
      suspicionPoints = 25;
      flag = `Response too fast for length (${timeSpent}s for ${wordCount} words)`;
    }

    // Suspiciously consistent timing
    if (timeSpent > 0 && timeSpent % 10 === 0 && wordCount > 100) {
      suspicionPoints += 5; // Might be copy-pasted
    }

    return { suspicionPoints, flag };
  }

  /**
   * Analyze context relevance to question
   */
  static analyzeContextRelevance(response, question) {
    let contextScore = 50; // Base score
    let suspicionPoints = 0;
    let flag = null;

    // Extract key terms from question
    const questionKeywords = this.extractKeywords(question);
    const responseKeywords = this.extractKeywords(response);

    // Check overlap
    const overlap = questionKeywords.filter(keyword => 
      responseKeywords.includes(keyword)
    ).length;

    const relevanceRatio = questionKeywords.length > 0 
      ? overlap / questionKeywords.length 
      : 0;

    if (relevanceRatio > 0.7) {
      contextScore = 90; // High relevance
    } else if (relevanceRatio > 0.4) {
      contextScore = 70; // Good relevance
    } else if (relevanceRatio > 0.2) {
      contextScore = 50; // Some relevance
    } else {
      contextScore = 20; // Low relevance
      suspicionPoints = 15;
      flag = 'Response may not be contextually relevant';
    }

    // Generic responses (copy-paste)
    if (this.isGenericResponse(response)) {
      suspicionPoints += 20;
      flag = 'Generic or templated response detected';
    }

    return { contextScore, suspicionPoints, flag };
  }

  /**
   * Calculate effort score based on multiple factors
   */
  static calculateEffortScore(response, timeSpent) {
    let effortScore = 0;

    // Length indicates effort
    const wordCount = response.trim().split(/\s+/).length;
    if (wordCount > 20) effortScore += 20;
    if (wordCount > 50) effortScore += 20;
    if (wordCount > 100) effortScore += 10;

    // Sentence variety
    const sentences = response.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length > 3) effortScore += 15;

    // Examples/specifics indicate thought
    if (/for example|such as|like|e\.g\.|specifically/i.test(response)) {
      effortScore += 15;
    }

    // Time spent (reasonable effort)
    if (timeSpent > 30) effortScore += 20;

    return Math.min(effortScore, 100);
  }

  /**
   * Detect AI-specific patterns
   */
  static detectAIPatterns(response) {
    let suspicionPoints = 0;
    let flag = null;

    // Numbered lists (common in AI responses)
    const hasNumberedList = /\n\s*\d+[.)]\s+/g.test(response);
    if (hasNumberedList) {
      suspicionPoints += 5;
    }

    // Perfect markdown formatting
    const hasMarkdown = /\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`/g.test(response);
    if (hasMarkdown) {
      suspicionPoints += 10;
      flag = 'Contains formatted text (markdown/rich text)';
    }

    // Overly structured (intro-body-conclusion)
    const hasStructure = /^(first|firstly|to begin|initially)|(second|secondly|next|furthermore)|(finally|in conclusion|to summarize)/im.test(response);
    if (hasStructure) {
      suspicionPoints += 10;
    }

    return { suspicionPoints, flag };
  }

  /**
   * Extract keywords from text
   */
  static extractKeywords(text) {
    const stopWords = new Set(['the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by']);
    
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 3 && !stopWords.has(word))
      .filter((word, index, self) => self.indexOf(word) === index); // Unique
  }

  /**
   * Check if response is generic/templated
   */
  static isGenericResponse(response) {
    const genericPhrases = [
      'this is a great question',
      'thank you for asking',
      'i would say that',
      'in my opinion',
      'based on my understanding',
      'according to my knowledge'
    ];

    return genericPhrases.some(phrase => 
      response.toLowerCase().includes(phrase)
    );
  }

  /**
   * Determine confidence level
   */
  static determineConfidence(suspicionScore, flagCount) {
    if (suspicionScore > 70 && flagCount >= 3) return 'high';
    if (suspicionScore > 50 && flagCount >= 2) return 'medium';
    if (suspicionScore > 30) return 'low';
    return 'minimal';
  }

  /**
   * Classify detection level
   */
  static classifyDetectionLevel(suspicionScore) {
    if (suspicionScore < 30) return 'clean';
    if (suspicionScore < 50) return 'possible_assistance';
    if (suspicionScore < 70) return 'likely_assistance';
    return 'high_probability_ai';
  }

  /**
   * Generate feedback message (balanced, not harsh)
   */
  static generateFeedback(indicators) {
    const { detectionLevel, effort, context, flags } = indicators;

    let feedback = '';
    let recommendation = '';

    switch (detectionLevel) {
      case 'clean':
        feedback = '✅ Your response shows genuine effort and understanding.';
        recommendation = 'Keep up the great work!';
        break;

      case 'possible_assistance':
        feedback = '⚠️ Your response shows some patterns that may indicate external assistance.';
        recommendation = 'Try to express ideas in your own words and show your thought process.';
        break;

      case 'likely_assistance':
        feedback = '⚠️ Your response contains several indicators of AI-generated content.';
        recommendation = 'We value authentic responses that reflect your understanding. Consider revising to show your personal insights.';
        break;

      case 'high_probability_ai':
        feedback = '❌ Your response shows strong indicators of AI-generated content.';
        recommendation = 'This assessment aims to evaluate YOUR understanding. Please provide responses in your own words with personal examples.';
        break;

      default:
        feedback = 'Response analyzed.';
        recommendation = 'Continue demonstrating your understanding.';
    }

    return {
      feedback,
      recommendation,
      effortScore: effort,
      contextScore: context,
      flags: flags.length > 0 ? flags.slice(0, 2) : [], // Show max 2 flags
      displayToStudent: detectionLevel !== 'clean' // Only show feedback if concerns exist
    };
  }

  /**
   * Batch analyze multiple responses
   */
  static analyzeMultipleResponses(responses, questions, timeSpents = []) {
    const analyses = responses.map((response, index) => ({
      questionIndex: index,
      ...this.analyzeResponse(
        response, 
        questions[index]?.question_text || '', 
        timeSpents[index] || 0
      )
    }));

    // Calculate overall pattern
    const avgSuspicion = analyses.reduce((sum, a) => sum + a.suspicionScore, 0) / analyses.length;
    const aiLikelyCount = analyses.filter(a => a.detectionLevel === 'likely_assistance' || a.detectionLevel === 'high_probability_ai').length;

    return {
      individualAnalyses: analyses,
      overallSuspicionScore: avgSuspicion,
      aiLikelyCount,
      totalResponses: responses.length,
      overallLevel: this.classifyDetectionLevel(avgSuspicion),
      recommendation: this.generateOverallRecommendation(avgSuspicion, aiLikelyCount, responses.length)
    };
  }

  /**
   * Generate overall recommendation for assessment
   */
  static generateOverallRecommendation(avgSuspicion, aiLikelyCount, totalResponses) {
    const aiRatio = aiLikelyCount / totalResponses;

    if (aiRatio > 0.5) {
      return 'More than half of your responses show signs of AI assistance. Future assessments should reflect your personal understanding.';
    } else if (aiRatio > 0.25) {
      return 'Several responses show possible AI assistance. Focus on demonstrating your own thinking and examples.';
    } else if (avgSuspicion > 40) {
      return 'Some responses could benefit from more personal expression and original examples.';
    } else {
      return 'Your responses demonstrate authentic effort and understanding.';
    }
  }
}

export default AIAssistanceDetector;
