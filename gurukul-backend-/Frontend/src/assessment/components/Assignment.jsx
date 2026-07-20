import { AlertCircle, BookOpen, Brain, Calculator, Clock, Code, Globe, Newspaper, Scroll, MessageCircle, HelpCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import { ASSIGNMENT_CONFIG } from '../data/assignment';
import { fieldBasedQuestionService } from '../lib/fieldBasedQuestionService';
import { supabase, SUPABASE_TABLE } from '../lib/supabaseClient';
import { backgroundSelectionService } from '../lib/backgroundSelectionService';
import { DynamicQuestionCategoryService } from '../lib/dynamicQuestionCategoryService';

// Icon mapping for question categories (supports dynamic categories)
const DEFAULT_CATEGORY_ICONS = {
  Code,
  Brain,
  Calculator,
  BookOpen,
  Globe,
  Scroll,
  Newspaper,
  MessageCircle,
  HelpCircle
};

// Helper function to get icon component by name
const getIconComponent = (iconName, category) => {
  if (iconName && DEFAULT_CATEGORY_ICONS[iconName]) {
    return DEFAULT_CATEGORY_ICONS[iconName];
  }
  // Fallback to category-based mapping for backward compatibility
  const legacyIcons = {
    'Coding': Code,
    'Logic': Brain,
    'Mathematics': Calculator,
    'Language': MessageCircle,
    'Culture': Globe,
    'Vedic Knowledge': Scroll,
    'Current Affairs': Newspaper
  };
  return legacyIcons[category] || BookOpen;
};

function QuestionCard({ question, questionNumber, userAnswer, onAnswerChange, onExplanationChange, userExplanation, categories }) {
  const IconComponent = getIconComponent(
    categories?.find(cat => cat.name === question.category)?.icon,
    question.category
  );

  return (
    <div className="rounded-xl border border-white/20 bg-white/10 p-4 sm:p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 sm:gap-0">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 min-w-fit">
            <IconComponent className="h-5 w-5 flex-shrink-0 text-orange-400" />
            <span className="text-sm font-medium text-orange-400 truncate">{question.category}</span>
          </div>
          <span className="text-xs px-2 py-1 rounded-full bg-white/10 text-white/70 whitespace-nowrap">
            {question.difficulty}
          </span>
        </div>
        <div className="text-sm text-white/60 whitespace-nowrap">
          Question {questionNumber} of {ASSIGNMENT_CONFIG.TOTAL_QUESTIONS}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">{question.question_text}</h3>

        <div className="space-y-2">
          {(Array.isArray(question.options) ? question.options : []).map((option, index) => (
            <label
              key={index}
              className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                userAnswer === option
                  ? 'border-orange-400 bg-orange-400/10'
                  : 'border-white/20 bg-white/5 hover:bg-white/10'
              }`}
            >
              <input
                type="radio"
                name={`question-${question.id}`}
                value={option}
                checked={userAnswer === option}
                onChange={(e) => onAnswerChange(question.id, e.target.value)}
                className="text-orange-400"
              />
              <span className="text-white">{option}</span>
            </label>
          ))}
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-white/80">
            Explain your reasoning (optional but recommended for better scoring):
          </label>
          <textarea
            value={userExplanation || ''}
            onChange={(e) => onExplanationChange(question.id, e.target.value)}
            placeholder="Explain why you chose this answer..."
            className="w-full p-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
            rows={3}
          />
        </div>

        {question.vedic_connection && (
          <div className="p-3 rounded-lg bg-orange-400/10 border border-orange-400/20">
            <div className="text-sm font-medium text-orange-400 mb-1">Vedic Connection:</div>
            <div className="text-sm text-white/80">{question.vedic_connection}</div>
          </div>
        )}
      </div>
    </div>
  );
}

function Timer({ timeRemaining, totalTime }) {
  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  const percentage = (timeRemaining / totalTime) * 100;

  return (
    <div className="flex items-center gap-3 p-4 rounded-lg bg-white/10 border border-white/20">
      <Clock className="h-5 w-5 text-orange-400" />
      <div className="flex-1">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/80">Time Remaining</span>
          <span className={`font-mono ${timeRemaining < 300 ? 'text-red-400' : 'text-white'}`}>
            {minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}
          </span>
        </div>
        <div className="mt-1 h-2 w-full rounded bg-white/10">
          <div
            className={`h-2 rounded transition-all duration-1000 ${
              percentage > 20 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${Math.max(0, percentage)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function ProgressIndicator({ currentQuestion, totalQuestions, answeredQuestions }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-white/80">Progress</span>
        <span className="text-white">
          {answeredQuestions.size} of {totalQuestions} answered
        </span>
      </div>
      <div className="h-2 w-full rounded bg-white/10">
        <div
          className="h-2 rounded bg-orange-500 transition-all duration-300"
          style={{ width: `${(answeredQuestions.size / totalQuestions) * 100}%` }}
        />
      </div>
      <div className="grid grid-cols-10 gap-1">
        {Array.from({ length: totalQuestions }, (_, i) => (
          <div
            key={i}
            className={`h-2 rounded ${
              i < currentQuestion
                ? answeredQuestions.has(i)
                  ? 'bg-green-500'
                  : 'bg-red-400'
                : i === currentQuestion
                ? 'bg-orange-500'
                : 'bg-white/20'
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export default function Assignment({ onComplete, userId = null, userEmail = null }) {
  const [assignment, setAssignment] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [userExplanations, setUserExplanations] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);

  // Load categories and assignment on component mount
  useEffect(() => {
    loadCategoriesAndAssignment();
  }, []);

  const loadCategoriesAndAssignment = async () => {
    try {
      // Load dynamic categories first
      const categoryList = await DynamicQuestionCategoryService.getAllCategories();
      setCategories(categoryList);
      console.log('📚 Loaded question categories:', categoryList);
      
      // Then load assignment
      await loadAssignment();
    } catch (error) {
      console.error('Error loading categories and assignment:', error);
      // Continue with assignment loading even if categories fail
      await loadAssignment();
    }
  };

  // Timer effect
  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            handleSubmit(true); // Auto-submit when time runs out
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [timeRemaining]);

  const loadAssignment = async () => {
    // Clear any existing toasts before starting
    toast.dismiss();
    
    setLoading(true);
    setLoadingProgress(0);
    setLoadingMessage('Loading student profile...');

    const loadingToast = toast.loading('Generating your personalized field-based assessment...');

    // Progress callback to update UI
    const progressCallback = (message, progress) => {
      setLoadingMessage(message);
      setLoadingProgress(progress);
      console.log(`📊 Progress: ${progress.toFixed(1)}% - ${message}`);
    };

    try {
      // Get student data for field-based question generation
      progressCallback('Fetching student profile...', 10);
      
      let studentData = {};
      try {
        let studentQuery = supabase
          .from(SUPABASE_TABLE)
          .select('*')
          .limit(1);

        // Prefer fetching by userId then email
        if (userId) {
          studentQuery = studentQuery.eq('user_id', userId);
        } else if (userEmail) {
          studentQuery = studentQuery.eq('email', userEmail);
        } else {
          studentQuery = studentQuery.order('created_at', { ascending: false });
        }

        const { data: students, error: studentError } = await studentQuery;

        if (!studentError && students && students.length > 0) {
          studentData = students[0];
          console.log('📊 Raw student data:', studentData);
          console.log('🎯 Student field_of_study from responses:', studentData?.responses?.field_of_study);
          console.log('🎯 Student field_of_study direct:', studentData?.field_of_study);
          progressCallback('Student profile loaded successfully', 30);
        } else {
          console.warn('No student data found, using default profile');
          progressCallback('Using default profile for question generation', 30);
        }
      } catch (studentError) {
        console.warn('Could not fetch student data:', studentError);
        progressCallback('Using default profile for question generation', 30);
      }

      // Merge background selection data for better field detection
      progressCallback('Loading background selection...', 40);
      try {
        const backgroundSelection = await backgroundSelectionService.getBackgroundSelection(userId);
        if (backgroundSelection) {
          console.log('📋 Background selection found:', backgroundSelection);
          // Merge background selection into student data for enhanced field detection
          studentData = {
            ...studentData,
            background_field_of_study: backgroundSelection.field_of_study,
            background_class_level: backgroundSelection.class_level,
            background_learning_goals: backgroundSelection.learning_goals,
            // Override field_of_study if background selection is more specific
            field_of_study: backgroundSelection.field_of_study || studentData.field_of_study || studentData.responses?.field_of_study
          };
          progressCallback('Background selection merged successfully', 45);
        } else {
          console.log('📋 No background selection found, using student data only');
          progressCallback('Using student data for field detection', 45);
        }
      } catch (bgError) {
        console.warn('Could not fetch background selection:', bgError);
        progressCallback('Using student data for field detection', 45);
      }

      progressCallback('Analyzing student background and study field...', 50);
      
      // Generate questions based on student's field
      progressCallback('Selecting field-appropriate questions...', 70);
      const rawQuestions = await fieldBasedQuestionService.generateQuestionsForStudent(
        studentData,
        ASSIGNMENT_CONFIG.TOTAL_QUESTIONS
      );
      // Normalize questions to ensure required fields and validate non-empty list
      const questions = Array.isArray(rawQuestions)
        ? rawQuestions
            .filter(q => q && (q.id || q.question_id || q.questionId || q.question_text || q.text))
            .map((q, index) => ({
              ...q,
              id: q?.id ?? q?.question_id ?? q?.questionId ?? `q_${index + 1}`,
              question_text: q?.question_text ?? q?.text ?? '',
              category: q?.category ?? 'General',
              difficulty: q?.difficulty ?? 'Medium',
              options: Array.isArray(q?.options) ? q.options : [],
              correct_answer: q?.correct_answer ?? q?.correctAnswer ?? q?.answer ?? (Array.isArray(q?.options) ? q.options[0] : ''),
              explanation: typeof q?.explanation === 'string' ? q.explanation : ''
            }))
        : [];
      if (!questions.length) {
        throw new Error('questions_generation_failed: no questions available');
      }

      progressCallback('Finalizing assignment...', 90);

      const generatedAssignment = {
        id: `field_assessment_${Date.now()}`,
        title: 'Field-Based Assessment',
        description: 'Personalized assessment based on your study field and background',
        questions: questions,
        student_field: studentData.field_of_study || 'General',
        created_at: new Date().toISOString()
      };

      progressCallback('Assignment ready!', 100);
      
      setAssignment(generatedAssignment);
      setTimeRemaining(ASSIGNMENT_CONFIG.TIME_LIMIT_MINUTES * 60);
      setStartTime(new Date());

      toast.success('Field-based assignment loaded successfully!', { id: loadingToast });
    } catch (error) {
      console.error('Failed to load assignment:', error);

      // Show specific error message based on error type
      let errorMessage = 'Failed to generate assignment. Please try again.';
      if (error.message.includes('student')) {
        errorMessage = 'Could not load student profile. Using default question set.';
      } else if (error.message.includes('questions')) {
        errorMessage = 'Could not generate enough questions for your field. Please try again.';
      } else if (error.message.includes('field')) {
        errorMessage = 'Could not determine your study field. Using general questions.';
      }

      // Use the same toast ID to update the loading toast instead of creating a new one
      toast.error(errorMessage, { id: loadingToast });
      setAssignment(null); // Ensure assignment is null on error
    } finally {
      setLoading(false);
      setLoadingProgress(0);
      setLoadingMessage('');
    }
  };

  const handleAnswerChange = useCallback((questionId, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  }, []);

  const handleExplanationChange = useCallback((questionId, explanation) => {
    setUserExplanations(prev => ({
      ...prev,
      [questionId]: explanation
    }));
  }, []);

  const handleSubmit = async (autoSubmit = false) => {
    if (!autoSubmit && !showConfirmSubmit) {
      setShowConfirmSubmit(true);
      return;
    }

    const endTime = new Date();
    const timeTaken = Math.floor((endTime - startTime) / 1000);

    const attempt = {
      id: `attempt_${Date.now()}`,
      assignment_id: assignment.id,
      student_field: assignment.student_field,
      started_at: startTime.toISOString(),
      completed_at: endTime.toISOString(),
      time_taken_seconds: timeTaken,
      user_answers: userAnswers,
      user_explanations: userExplanations,
      questions: assignment.questions,
      auto_submitted: autoSubmit
    };

    onComplete(attempt);
  };

  const navigateToQuestion = (index) => {
    setCurrentQuestionIndex(index);
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < assignment.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-6 max-w-md">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mx-auto"></div>

          <div className="space-y-3">
            <div className="text-xl font-semibold text-white">Generating Your Assignment</div>
            <div className="text-white/80">{loadingMessage || 'Preparing AI-powered questions...'}</div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-white/10 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-orange-500 to-orange-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${Math.max(5, loadingProgress)}%` }}
            ></div>
          </div>
          <div className="text-sm text-orange-400 font-medium">
            {loadingProgress > 0 ? `${Math.round(loadingProgress)}% Complete` : 'Starting...'}
          </div>

          <div className="space-y-2 text-sm text-white/60">
            <div>🎯 Analyzing your study field and background</div>
            <div>📚 Selecting field-appropriate questions</div>
            <div>⚡ Fast generation using curated question banks</div>
          </div>

          <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <div className="text-sm text-blue-300">
              💡 <strong>Personalized Assessment:</strong> We're selecting questions from our
              comprehensive question banks that match your study field and academic level.
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="text-center space-y-6 max-w-md mx-auto">
        <AlertCircle className="h-16 w-16 text-red-400 mx-auto" />
        <div className="space-y-3">
          <h2 className="text-xl font-semibold text-white">Assignment Generation Failed</h2>
          <p className="text-white/70 text-sm leading-relaxed">
            We couldn't generate your field-based assessment. This could be due to:
          </p>
          <ul className="text-left text-sm text-white/60 space-y-1">
            <li>• Network connectivity issues</li>
            <li>• Unable to load student profile</li>
            <li>• Question bank temporarily unavailable</li>
          </ul>
        </div>
        <div className="space-y-3">
          <button
            onClick={loadAssignment}
            className="px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
          <div className="text-xs text-white/50">
            If the problem persists, please contact support
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = assignment.questions[currentQuestionIndex] ?? assignment.questions.find(Boolean);
  const answeredQuestions = new Set(
    assignment.questions
      .map((q, index) => (q && q.id && userAnswers[q.id] ? index : null))
      .filter(index => index !== null)
  );

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="text-center space-y-2 px-4 sm:px-0 max-w-full overflow-hidden">
        <h1 className="text-xl sm:text-2xl font-bold text-white break-words">{assignment.title}</h1>
        <p className="text-sm sm:text-base text-white/70 break-words">{assignment.description}</p>
      </div>

      {/* Timer and Progress */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        <div className="w-full">
          <Timer timeRemaining={timeRemaining} totalTime={ASSIGNMENT_CONFIG.TIME_LIMIT_MINUTES * 60} />
        </div>
        <div className="w-full">
          <ProgressIndicator
            currentQuestion={currentQuestionIndex}
            totalQuestions={assignment.questions.length}
            answeredQuestions={answeredQuestions}
          />
        </div>
      </div>

      {/* Current Question */}
      <QuestionCard
        question={currentQuestion}
        questionNumber={currentQuestionIndex + 1}
        userAnswer={currentQuestion ? userAnswers[currentQuestion.id] : undefined}
        userExplanation={currentQuestion ? userExplanations[currentQuestion.id] : undefined}
        onAnswerChange={handleAnswerChange}
        onExplanationChange={handleExplanationChange}
        categories={categories}
      />

      {/* Navigation */}
      <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-0 sm:justify-between">
        <button
          onClick={previousQuestion}
          disabled={currentQuestionIndex === 0}
          className="w-full sm:w-auto px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg border border-white/20"
        >
          Previous
        </button>

        <div className="flex flex-wrap justify-center items-center gap-2 max-w-full overflow-x-auto py-2">
          {assignment.questions.map((_, index) => (
            <button
              key={index}
              onClick={() => navigateToQuestion(index)}
              className={`w-8 h-8 rounded text-sm flex-shrink-0 ${
                index === currentQuestionIndex
                  ? 'bg-orange-500 text-white'
                  : answeredQuestions.has(index)
                  ? 'bg-green-500 text-white'
                  : 'bg-white/20 text-white/70 hover:bg-white/30'
              }`}
            >
              {index + 1}
            </button>
          ))}
        </div>

        {currentQuestionIndex === assignment.questions.length - 1 ? (
          <button
            onClick={() => handleSubmit(false)}
            className="w-full sm:w-auto px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium"
          >
            Submit Assignment
          </button>
        ) : (
          <button
            onClick={nextQuestion}
            className="w-full sm:w-auto px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg"
          >
            Next
          </button>
        )}
      </div>

      {/* Confirm Submit Modal */}
      {showConfirmSubmit && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-white/20 rounded-xl p-4 sm:p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Submit Assignment?</h3>
            <p className="text-sm sm:text-base text-white/70 mb-6">
              You have answered {answeredQuestions.size} out of {assignment.questions.length} questions. 
              Are you sure you want to submit your assignment?
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setShowConfirmSubmit(false)}
                className="w-full px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg border border-white/20"
              >
                Continue Working
              </button>
              <button
                onClick={() => handleSubmit(false)}
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
              >
                Submit Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
