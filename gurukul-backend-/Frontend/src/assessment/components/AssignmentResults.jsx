import { useAuth } from '../../contexts/AuthContext';
import {
  Award,
  BarChart3,
  BookOpen,
  Brain,
  Calendar,
  CheckCircle,
  Clock,
  Lightbulb,
  MessageSquare,
  Target,
  TrendingDown,
  TrendingUp,
  Trophy,
  User,
  XCircle
} from 'lucide-react';
import { useState } from 'react';
import { ASSIGNMENT_CATEGORIES } from '../data/assignment';
import { CLERK_ENABLED } from '../config/auth';

function ScoreCard({ title, score, maxScore, percentage, icon: Icon, color = 'orange' }) {
  return (
    <div className="rounded-xl border border-white/20 bg-white/10 p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg bg-${color}-500/20`}>
          <Icon className={`h-5 w-5 text-${color}-400`} />
        </div>
        <div>
          <div className="font-medium text-white">{title}</div>
          <div className="text-sm text-white/70">
            {score.toFixed(1)} / {maxScore} ({percentage.toFixed(1)}%)
          </div>
        </div>
      </div>
      <div className="h-2 w-full rounded bg-white/10">
        <div
          className={`h-2 rounded bg-${color}-500 transition-all duration-1000`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
    </div>
  );
}

function CategoryBreakdown({ categoryScores }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-orange-400" />
        Category Performance
      </h3>
      <div className="grid gap-3 md:grid-cols-2">
        {Object.entries(categoryScores).map(([category, data]) => {
          if (data.count === 0) return null;

          const color = data.percentage >= 80 ? 'green' : data.percentage >= 60 ? 'orange' : 'red';

          return (
            <div key={category} className="rounded-lg border border-white/20 bg-white/5 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-white">{category}</span>
                <span className={`text-sm font-medium text-${color}-400`}>
                  {data.percentage.toFixed(1)}%
                </span>
              </div>
              <div className="text-sm text-white/70 mb-2">
                {data.total.toFixed(1)} / {data.max} points ({data.count} questions)
              </div>
              <div className="h-2 w-full rounded bg-white/10">
                <div
                  className={`h-2 rounded bg-${color}-500 transition-all duration-1000`}
                  style={{ width: `${Math.min(100, data.percentage)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StrengthsAndImprovements({ strengths, improvementAreas }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Strengths */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-green-400" />
          Your Strengths
        </h3>
        {strengths.length > 0 ? (
          <div className="space-y-3">
            {strengths.map((strength, index) => (
              <div key={index} className="rounded-lg border border-green-500/20 bg-green-500/10 p-3">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="h-4 w-4 text-green-400" />
                  <span className="font-medium text-green-400">{strength.category}</span>
                </div>
                <div className="text-sm text-white/80">{strength.description}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-white/60 text-sm">
            Keep working to identify your strengths! Every expert was once a beginner.
          </div>
        )}
      </div>

      {/* Areas for Improvement */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <TrendingDown className="h-5 w-5 text-orange-400" />
          Growth Opportunities
        </h3>
        {improvementAreas.length > 0 ? (
          <div className="space-y-3">
            {improvementAreas.map((area, index) => (
              <div key={index} className="rounded-lg border border-orange-500/20 bg-orange-500/10 p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-orange-400" />
                  <span className="font-medium text-orange-400">{area.category}</span>
                </div>
                <div className="text-sm text-white/80 mb-2">{area.description}</div>
                <div className="text-xs text-white/60">{area.suggestion}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-white/60 text-sm">
            Great job! You're performing well across all categories.
          </div>
        )}
      </div>
    </div>
  );
}

function DetailedQuestionReview({ evaluatedResponses, onToggleExpand }) {
  const [expandedQuestions, setExpandedQuestions] = useState(new Set());

  const toggleQuestion = (questionId) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
    }
    setExpandedQuestions(newExpanded);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
        <MessageSquare className="h-5 w-5 text-orange-400" />
        Detailed Question Review
      </h3>
      <div className="space-y-3">
        {evaluatedResponses.map((response, index) => {
          const isExpanded = expandedQuestions.has(response.question_id);
          const scoreColor = response.total_score >= 8 ? 'green' : response.total_score >= 6 ? 'orange' : 'red';

          return (
            <div key={response.question_id} className="rounded-lg border border-white/20 bg-white/5 p-4">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => toggleQuestion(response.question_id)}
              >
                <div className="flex items-center gap-3">
                  {response.is_correct ? (
                    <CheckCircle className="h-5 w-5 text-green-400" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-400" />
                  )}
                  <div>
                    <div className="font-medium text-white">Question {index + 1}</div>
                    <div className="text-sm text-white/70">{response.question_category}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className={`text-sm font-medium text-${scoreColor}-400`}>
                    {response.total_score.toFixed(1)}/10
                  </div>
                  <div className="text-white/60">
                    {isExpanded ? '−' : '+'}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-4 space-y-3 border-t border-white/10 pt-4">
                  <div className="grid gap-3 md:grid-cols-3">
                    <div className="text-center">
                      <div className="text-sm text-white/70">Accuracy</div>
                      <div className="text-lg font-medium text-white">{response.accuracy_score}/10</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-white/70">Explanation</div>
                      <div className="text-lg font-medium text-white">{response.explanation_score}/10</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-white/70">Reasoning</div>
                      <div className="text-lg font-medium text-white">{response.reasoning_score}/10</div>
                    </div>
                  </div>

                  {response.user_answer && (
                    <div>
                      <div className="text-sm font-medium text-white/80 mb-1">Your Answer:</div>
                      <div className="text-sm text-white/70">{response.user_answer}</div>
                    </div>
                  )}

                  {response.user_explanation && (
                    <div>
                      <div className="text-sm font-medium text-white/80 mb-1">Your Explanation:</div>
                      <div className="text-sm text-white/70">{response.user_explanation}</div>
                    </div>
                  )}

                  <div>
                    <div className="text-sm font-medium text-white/80 mb-1">Correct Answer:</div>
                    <div className="text-sm text-green-400">{response.correct_answer}</div>
                  </div>

                  {response.ai_feedback && (
                    <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-3">
                      <div className="text-sm font-medium text-blue-400 mb-1">AI Feedback:</div>
                      <div className="text-sm text-white/80">{response.ai_feedback}</div>
                    </div>
                  )}

                  {response.suggestions && (
                    <div className="rounded-lg bg-orange-500/10 border border-orange-500/20 p-3">
                      <div className="text-sm font-medium text-orange-400 mb-1 flex items-center gap-1">
                        <Lightbulb className="h-4 w-4" />
                        Suggestions:
                      </div>
                      <div className="text-sm text-white/80">{response.suggestions}</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function AssignmentResults({ results, onRetakeAssignment, onBackToDashboard }) {
  const { user } = useAuth();

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return 'text-green-400';
      case 'B': return 'text-blue-400';
      case 'C': return 'text-orange-400';
      case 'D': return 'text-yellow-400';
      case 'F': return 'text-red-400';
      default: return 'text-white';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-8">
      {/* User Information Header */}
      {CLERK_ENABLED && user && (
        <div className="rounded-xl border border-blue-500/30 bg-gradient-to-r from-blue-500/10 to-purple-500/10 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-blue-500/20">
                <User className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">
                  {user.full_name || 'Student'}
                </h2>
                <div className="text-blue-300 text-sm">
                  {user.email}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 text-white/70 text-sm">
                <Calendar className="h-4 w-4" />
                <span>Completed: {formatDate(results.evaluated_at)}</span>
              </div>
              <div className="flex items-center gap-2 text-white/70 text-sm mt-1">
                <Clock className="h-4 w-4" />
                <span>Time Taken: {formatTime(results.attempt?.time_taken_seconds || 0)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <Trophy className="h-8 w-8 text-orange-400" />
          <h1 className="text-3xl font-bold text-white">Assignment Results</h1>
          {CLERK_ENABLED && user && (
            <div className="flex items-center gap-2 text-white/60 text-sm">
              <Award className="h-4 w-4" />
              <span>for {user.full_name || 'Student'}</span>
            </div>
          )}
        </div>
        <div className={`text-6xl font-bold ${getGradeColor(results.grade)}`}>
          {results.grade}
        </div>
        <div className="text-xl text-white">
          {results.percentage.toFixed(1)}% ({results.total_score.toFixed(1)}/{results.max_score})
        </div>
      </div>

      {/* Overall Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <ScoreCard
          title="Overall Score"
          score={results.total_score}
          maxScore={results.max_score}
          percentage={results.percentage}
          icon={Target}
          color="orange"
        />
        <ScoreCard
          title="Correct Answers"
          score={results.evaluated_responses.filter(r => r.is_correct).length}
          maxScore={results.evaluated_responses.length}
          percentage={(results.evaluated_responses.filter(r => r.is_correct).length / results.evaluated_responses.length) * 100}
          icon={CheckCircle}
          color="green"
        />
        <ScoreCard
          title="Avg. Explanation"
          score={results.evaluated_responses.reduce((sum, r) => sum + r.explanation_score, 0) / results.evaluated_responses.length}
          maxScore={10}
          percentage={(results.evaluated_responses.reduce((sum, r) => sum + r.explanation_score, 0) / results.evaluated_responses.length / 10) * 100}
          icon={Brain}
          color="blue"
        />
        <ScoreCard
          title="Avg. Reasoning"
          score={results.evaluated_responses.reduce((sum, r) => sum + r.reasoning_score, 0) / results.evaluated_responses.length}
          maxScore={10}
          percentage={(results.evaluated_responses.reduce((sum, r) => sum + r.reasoning_score, 0) / results.evaluated_responses.length / 10) * 100}
          icon={BookOpen}
          color="purple"
        />
      </div>

      {/* Overall Feedback */}
      {results.overall_feedback && (
        <div className="rounded-xl border border-white/20 bg-white/10 p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-orange-400" />
            AI Feedback
          </h3>
          <div className="text-white/80 leading-relaxed">{results.overall_feedback}</div>
        </div>
      )}

      {/* Category Breakdown */}
      <CategoryBreakdown categoryScores={results.category_scores} />

      {/* Strengths and Improvements */}
      <StrengthsAndImprovements
        strengths={results.strengths}
        improvementAreas={results.improvement_areas}
      />

      {/* Detailed Question Review */}
      <DetailedQuestionReview evaluatedResponses={results.evaluated_responses} />

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center">
        <button
          onClick={onRetakeAssignment}
          className="px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-medium"
        >
          Retake Assignment
        </button>
        <button
          onClick={onBackToDashboard}
          className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg border border-white/20"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}
