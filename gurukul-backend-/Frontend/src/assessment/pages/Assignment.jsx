import { useAuth } from '../../contexts/AuthContext';
import API_BASE_URL from '../../config';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import Assignment from '../components/Assignment';
import AssignmentResults from '../components/AssignmentResults';
import ErrorBoundary from '../components/ErrorBoundary';
// Clerk disabled, using native AuthContext
const CLERK_ENABLED = false;
import { useI18n } from "../lib/i18n";
import { scoringService } from '../lib/scoringService';

export default function AssignmentPage() {
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('assignment'); // 'assignment', 'evaluating', 'results'
  const { t } = useI18n();
  const [_assignmentAttempt, setAssignmentAttempt] = useState(null);
  const [evaluationResults, setEvaluationResults] = useState(null);
  const { user, token, updateUser } = useAuth();

  const handleAssignmentComplete = async (attempt) => {
    setAssignmentAttempt(attempt);
    setCurrentView('evaluating');

    // Show evaluation progress
    const evaluationToast = toast.loading(t('assignment.evaluatingSubtitle'));

    try {
      // Prepare user context for evaluation
      const userContext = user ? {
        id: user.id,
        name: user.full_name || 'Student',
        email: user.email
      } : null;

      console.log('🎯 Starting evaluation with user context:', userContext);

      // Evaluate the assignment with user context
      const results = await scoringService.evaluateAssignmentAttempt(attempt, userContext);

      // Store results in Supabase if user is logged in
      if (user) {
        await storeAssignmentResults(attempt, results);
        // Call backend to mark assessment as completed
        try {
          await fetch(`${API_BASE_URL}/api/v1/auth/complete-assessment`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          console.log('✅ Assessment marked as completed in backend');
          if (updateUser) {
            updateUser({ assessment_completed: true });
          }
        } catch (err) {
          console.error('❌ Failed to mark assessment as completed:', err);
        }
      }

      setEvaluationResults(results);
      setCurrentView('results');

      toast.success('Assignment evaluated successfully!', { id: evaluationToast });
    } catch (error) {
      console.error('Error evaluating assignment:', error);

      // Show specific error message
      let errorMessage = 'Failed to evaluate assignment. Please try again.';
      if (error.message.includes('API key')) {
        errorMessage = 'Evaluation service is not properly configured. Please contact support.';
      } else if (error.message.includes('network') || error.message.includes('fetch')) {
        errorMessage = 'Network connection error. Please check your internet connection and try again.';
      } else if (error.message.includes('rate limit')) {
        errorMessage = 'Too many requests. Please wait a moment and try again.';
      }

      toast.error(errorMessage, { id: evaluationToast });
      setCurrentView('assignment');
    }
  };

  const storeAssignmentResults = async (attempt, results) => {
    console.log('💾 Storing assignment results to backend profile...');
    try {
      if (!user) {
        console.warn('⚠️ User not authenticated, skipping data storage');
        return;
      }

      // 1. Fetch current profile data from backend
      let profileData = {};
      try {
        const getResponse = await fetch(`${API_BASE_URL}/api/v1/auth/profile-data`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (getResponse.ok) {
          const resJson = await getResponse.json();
          profileData = resJson.data || {};
        }
      } catch (err) {
        console.warn('⚠️ Failed to fetch existing profile data, creating new:', err);
      }

      // 2. Prepare detailed responses data
      const detailedResponses = results.evaluated_responses.map(response => ({
        question_id: response.question_id,
        question_category: response.question_category,
        question_difficulty: response.question_difficulty,
        user_answer: response.user_answer,
        user_explanation: response.user_explanation,
        correct_answer: response.correct_answer,
        is_correct: response.is_correct,
        accuracy_score: response.accuracy_score,
        explanation_score: response.explanation_score,
        reasoning_score: response.reasoning_score,
        total_score: response.total_score,
        max_score: response.max_score,
        ai_feedback: response.ai_feedback,
        suggestions: response.suggestions,
        evaluated_at: response.evaluated_at
      }));

      // 3. Prepare assignment attempt data
      const assignmentData = {
        assignment_id: attempt.assignment_id,
        started_at: attempt.started_at,
        completed_at: attempt.completed_at,
        time_taken_seconds: attempt.time_taken_seconds,
        total_score: results.total_score,
        max_score: results.max_score,
        percentage: results.percentage,
        grade: results.grade,
        category_scores: results.category_scores,
        overall_feedback: results.overall_feedback,
        strengths: results.strengths,
        improvement_areas: results.improvement_areas,
        auto_submitted: attempt.auto_submitted || false,
        evaluated_at: results.evaluated_at,
        detailed_responses: detailedResponses
      };

      // 4. Update assignment_attempts array in profile data
      const attempts = Array.isArray(profileData.assignment_attempts)
        ? [...profileData.assignment_attempts]
        : [];
      attempts.push(assignmentData);
      
      const updatedProfileData = {
        ...profileData,
        assignment_attempts: attempts,
        updated_at: new Date().toISOString()
      };

      // 5. Save back to backend
      const putResponse = await fetch(`${API_BASE_URL}/api/v1/auth/profile-data`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatedProfileData)
      });

      if (!putResponse.ok) {
        throw new Error(`Failed to update profile data on backend. Status: ${putResponse.status}`);
      }

      console.log('✅ Assignment results stored in backend profile successfully!');

      // Set student_record mock in attempt for display components
      results.attempt = {
        ...attempt,
        stored_at: new Date().toISOString(),
        student_record: {
          id: user.id,
          name: user.full_name,
          email: user.email
        }
      };

    } catch (error) {
      console.error('💥 Error storing assignment results:', error);
      toast.error('Results evaluated successfully, but failed to save to backend profile.');
    }
  };

  const handleRetakeAssignment = () => {
    setCurrentView('assignment');
    setAssignmentAttempt(null);
    setEvaluationResults(null);
  };

  const handleBackToDashboard = () => {
    // Navigate back to dashboard using React Router
    navigate('/dashboard');
  };

  if (currentView === 'evaluating') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-6">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mx-auto"></div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-white">{t('assignment.evaluatingTitle')}</h2>
            <p className="text-white/70">{t('assignment.evaluatingSubtitle')}</p>
            <div className="text-sm text-white/60">
              {t('assignment.checkingAccuracy')} • {t('assignment.evaluatingExplanation')} • {t('assignment.analyzingReasoning')}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm text-orange-400">{t('assignment.checkingAccuracy')}</div>
            <div className="text-sm text-orange-400">{t('assignment.evaluatingExplanation')}</div>
            <div className="text-sm text-orange-400">{t('assignment.analyzingReasoning')}</div>
            <div className="text-sm text-white/60">{t('assignment.generatingFeedback')}</div>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'results' && evaluationResults) {
    return (
      <ErrorBoundary fallbackMessage="Failed to display assignment results. Your evaluation was successful, but there was an error showing the results.">
        <AssignmentResults
          results={evaluationResults}
          onRetakeAssignment={handleRetakeAssignment}
          onBackToDashboard={handleBackToDashboard}
        />
      </ErrorBoundary>
    );
  }

  return (
    <Assignment
      onComplete={handleAssignmentComplete}
      userId={user?.id}
      userEmail={user?.email}
    />
  );
}
