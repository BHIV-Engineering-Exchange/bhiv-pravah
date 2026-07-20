// Assignment data structures and configurations
// Note: ASSIGNMENT_CATEGORIES is deprecated - use DynamicQuestionCategoryService instead
// Kept for backward compatibility only

export const ASSIGNMENT_CATEGORIES = {
  CODING: 'Coding',
  LOGIC: 'Logic',
  MATHEMATICS: 'Mathematics',
  LANGUAGE: 'Language',
  CULTURE: 'Culture',
  VEDIC_KNOWLEDGE: 'Vedic Knowledge',
  CURRENT_AFFAIRS: 'Current Affairs'
};

export const DIFFICULTY_LEVELS = {
  EASY: 'easy',
  MEDIUM: 'medium',
  HARD: 'hard'
};

export const QUESTION_TYPES = {
  MULTIPLE_CHOICE: 'multiple_choice',
  SHORT_ANSWER: 'short_answer',
  ESSAY: 'essay',
  CODE: 'code'
};

// Assignment configuration - Dynamic Categories
// Category distribution is now managed by DynamicQuestionCategoryService
export const ASSIGNMENT_CONFIG = {
  TOTAL_QUESTIONS: 10,
  TIME_LIMIT_MINUTES: 30,
  // DEPRECATED: Use DynamicQuestionCategoryService.getQuestionWeights() instead
  CATEGORY_DISTRIBUTION: {
    [ASSIGNMENT_CATEGORIES.CODING]: 2,
    [ASSIGNMENT_CATEGORIES.LOGIC]: 1,
    [ASSIGNMENT_CATEGORIES.MATHEMATICS]: 2,
    [ASSIGNMENT_CATEGORIES.LANGUAGE]: 1,
    [ASSIGNMENT_CATEGORIES.CULTURE]: 1,
    [ASSIGNMENT_CATEGORIES.VEDIC_KNOWLEDGE]: 2,
    [ASSIGNMENT_CATEGORIES.CURRENT_AFFAIRS]: 1
  },
  DIFFICULTY_DISTRIBUTION: {
    [DIFFICULTY_LEVELS.EASY]: 3,
    [DIFFICULTY_LEVELS.MEDIUM]: 5,
    [DIFFICULTY_LEVELS.HARD]: 2
  }
};

/**
 * Helper function to get dynamic category distribution
 * Uses DynamicQuestionCategoryService for category weights
 */
export async function getDynamicCategoryDistribution(totalQuestions = 10) {
  try {
    const { DynamicQuestionCategoryService } = await import('../lib/dynamicQuestionCategoryService');
    const categories = await DynamicQuestionCategoryService.getAllCategories();
    if (!categories || categories.length === 0) {
      throw new Error('No active categories');
    }

    const names = categories.map(c => c.name);
    const distribution = {};

    // Evenly distribute questions across categories
    const base = Math.floor(totalQuestions / names.length);
    let remainder = totalQuestions % names.length;

    names.forEach((name) => {
      distribution[name] = base + (remainder > 0 ? 1 : 0);
      if (remainder > 0) remainder--;
    });

    return distribution;
  } catch (error) {
    console.error('Failed to get dynamic category distribution, using fallback:', error);
    return ASSIGNMENT_CONFIG.CATEGORY_DISTRIBUTION;
  }
}

// Scoring criteria
export const SCORING_CRITERIA = {
  ACCURACY_WEIGHT: 0.4,
  EXPLANATION_QUALITY_WEIGHT: 0.3,
  REASONING_CLARITY_WEIGHT: 0.3,
  MAX_SCORE_PER_QUESTION: 10
};

// Question template structure
export const QUESTION_TEMPLATE = {
  id: '',
  category: '',
  difficulty: '',
  type: '',
  question_text: '',
  options: [], // For multiple choice
  correct_answer: '',
  explanation: '',
  points: 10,
  time_limit_seconds: 180,
  vedic_connection: '', // For questions that can be linked to Vedic knowledge
  modern_application: '' // How this knowledge applies today
};

// Assignment attempt structure
export const ASSIGNMENT_ATTEMPT_TEMPLATE = {
  id: '',
  user_id: '',
  assignment_id: '',
  questions: [],
  user_responses: [],
  started_at: '',
  completed_at: '',
  time_taken_seconds: 0,
  total_score: 0,
  max_score: 0,
  category_scores: {},
  ai_feedback: '',
  status: 'in_progress' // 'in_progress', 'completed', 'abandoned'
};

// User response structure
export const USER_RESPONSE_TEMPLATE = {
  question_id: '',
  selected_option: '',
  text_answer: '',
  explanation: '',
  time_taken_seconds: 0,
  is_correct: false,
  accuracy_score: 0,
  explanation_score: 0,
  reasoning_score: 0,
  total_score: 0,
  ai_feedback: ''
};

// Sample prompts for Grok API - Updated for Dynamic Categories
export const GROK_PROMPTS = {
  GENERATE_QUESTIONS: `You are an expert educational content creator. Generate exactly {count} unique {category} questions at {difficulty} difficulty level.

CRITICAL REQUIREMENTS:
1. Return ONLY a valid JSON array - no other text
2. Each question must be completely unique
3. Use exactly 4 multiple choice options (A, B, C, D)
4. One option must be clearly correct

QUESTION SPECIFICATIONS:
- Category: {category}
- Difficulty: {difficulty}
- Count: {count}

CONTENT GUIDELINES:
- Adapt to the category provided (not limited to predefined categories)
- For programming/coding: Focus on algorithms, data structures, programming concepts
- For logic/reasoning: Test reasoning, pattern recognition, logical deduction
- For mathematics: Real-world applications, problem-solving
- For language: Grammar, comprehension, communication skills
- For culture: Global awareness, traditions, diversity
- For traditional knowledge: Ancient wisdom with modern relevance
- For current events: Recent events, global developments
- For other categories: Adapt content to match the category theme

JSON FORMAT (return exactly this structure):
[
  {
    "question_text": "Clear, specific question here",
    "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
    "correct_answer": "A) First option",
    "explanation": "Brief explanation of correct answer",
    "vedic_connection": "Traditional knowledge relevance (if applicable, otherwise empty string)",
    "modern_application": "Modern relevance (if applicable, otherwise empty string)"
  }
]

Generate exactly {count} questions. Return only the JSON array.`,

  EVALUATE_RESPONSE: `You are an expert educational evaluator. Evaluate this student response and return ONLY valid JSON.

QUESTION: {question}
STUDENT ANSWER: {answer}
STUDENT EXPLANATION: {explanation}
CORRECT ANSWER: {correct_answer}

EVALUATION CRITERIA (score 0-10 for each):
1. ACCURACY: How correct is the student's answer? (10 = completely correct, 0 = completely wrong)
2. EXPLANATION QUALITY: How well did they explain their reasoning? (10 = excellent explanation, 0 = no explanation)
3. REASONING CLARITY: How clear and logical is their thought process? (10 = very clear, 0 = unclear)

IMPORTANT: Return ONLY the JSON object below with no additional text:

{
  "accuracy_score": [number 0-10],
  "explanation_score": [number 0-10],
  "reasoning_score": [number 0-10],
  "feedback": "Brief constructive feedback about their response",
  "suggestions": "Specific suggestions for improvement"
}`,

  GENERATE_OVERALL_FEEDBACK: `You are an expert educational advisor providing personalized feedback after a comprehensive assessment. Generate encouraging, specific, and actionable feedback.

ASSESSMENT RESULTS:
- Student Name: {student_name}
- Overall Score: {overall_percentage}% ({total_score}/{max_score} points)
- Total Questions: {total_questions}
- Correct Answers: {correct_answers}
- Categories Tested: {categories}

CATEGORY PERFORMANCE:
{category_breakdown}

STRONG AREAS:
{strong_categories}

IMPROVEMENT AREAS:
{weak_categories}

AVERAGE EXPLANATION QUALITY: {avg_explanation_score}/10

GENERATE PERSONALIZED FEEDBACK:
1. Start with the student's name and an encouraging opening
2. Acknowledge their overall performance level
3. Highlight specific strengths and strong categories
4. Address areas for improvement with specific suggestions
5. Comment on explanation quality and reasoning
6. Provide motivational conclusion with next steps
7. Keep tone positive, constructive, and encouraging
8. Make it personal and specific to their performance

Return ONLY a well-structured paragraph of feedback (no JSON, no special formatting).`
};

// Error messages for API failures
export const API_ERROR_MESSAGES = {
  GENERATION_FAILED: 'Unable to generate questions at this time. Please check your internet connection and try again.',
  API_KEY_MISSING: 'Assessment service is not properly configured. Please contact support.',
  RATE_LIMIT: 'API rate limit reached. The system is generating questions too quickly. Please wait 2-3 minutes before trying again.',
  NETWORK_ERROR: 'Network connection error. Please check your internet connection.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again later.'
};
