import React, { useState, useEffect } from 'react';
import { 
  Trophy, TrendingUp, TrendingDown, Minus, 
  Brain, AlertCircle, CheckCircle, Target,
  BarChart3, PieChart, Award
} from 'lucide-react';
import AIAssistanceDetector from '../lib/aiAssistanceDetector';

export default function MultiDomainResults({ 
  results, 
  questions, 
  userResponses, 
  selectedDomains,
  onRetake,
  onClose 
}) {
  const [aiDetectionResults, setAiDetectionResults] = useState(null);
  const [showAIDetails, setShowAIDetails] = useState(false);

  useEffect(() => {
    const analyze = () => {
      if (userResponses && questions) {
        const responses = userResponses.map(r => r.explanation || r.text_answer || '');
        const timeSpents = userResponses.map(r => r.time_taken_seconds || 0);

        const analysis = AIAssistanceDetector.analyzeMultipleResponses(
          responses,
          questions,
          timeSpents
        );

        setAiDetectionResults(analysis);
      }
    };

    analyze();
  }, [userResponses, questions]);

  // Calculate domain-wise performance
  const getDomainPerformance = () => {
    const domainStats = {};

    questions.forEach((question, index) => {
      const domain = question.category;
      if (!domainStats[domain]) {
        domainStats[domain] = {
          total: 0,
          correct: 0,
          points: 0,
          maxPoints: 0
        };
      }

      domainStats[domain].total++;
      domainStats[domain].maxPoints += question.points || 10;

      const response = userResponses[index];
      if (response) {
        if (response.is_correct) {
          domainStats[domain].correct++;
        }
        domainStats[domain].points += response.total_score || 0;
      }
    });

    return domainStats;
  };

  const domainPerformance = getDomainPerformance();

  // Calculate difficulty performance
  const getDifficultyPerformance = () => {
    const difficultyStats = { easy: { correct: 0, total: 0 }, medium: { correct: 0, total: 0 }, hard: { correct: 0, total: 0 } };

    questions.forEach((question, index) => {
      const difficulty = question.difficulty || 'medium';
      difficultyStats[difficulty].total++;

      const response = userResponses[index];
      if (response && response.is_correct) {
        difficultyStats[difficulty].correct++;
      }
    });

    return difficultyStats;
  };

  const difficultyPerformance = getDifficultyPerformance();

  const getGradeInfo = (percentage) => {
    if (percentage >= 90) return { grade: 'A+', color: 'green', message: 'Outstanding!' };
    if (percentage >= 80) return { grade: 'A', color: 'green', message: 'Excellent!' };
    if (percentage >= 70) return { grade: 'B', color: 'blue', message: 'Good Job!' };
    if (percentage >= 60) return { grade: 'C', color: 'yellow', message: 'Fair' };
    if (percentage >= 50) return { grade: 'D', color: 'orange', message: 'Needs Improvement' };
    return { grade: 'F', color: 'red', message: 'Keep Practicing' };
  };

  const percentage = (results.total_score / results.max_score) * 100;
  const gradeInfo = getGradeInfo(percentage);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Overall Score Card */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 border border-gray-700">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className={`p-4 rounded-full bg-${gradeInfo.color}-500/20`}>
              <Trophy className={`w-8 h-8 text-${gradeInfo.color}-400`} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Assessment Complete!</h2>
              <p className="text-gray-400">{selectedDomains?.length || 1} domain{selectedDomains?.length !== 1 ? 's' : ''} assessed</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-6xl font-bold text-${gradeInfo.color}-400`}>
              {gradeInfo.grade}
            </div>
            <p className={`text-sm text-${gradeInfo.color}-400`}>{gradeInfo.message}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="bg-gray-800/50 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Total Score</p>
            <p className="text-2xl font-bold text-white">
              {results.total_score} / {results.max_score}
            </p>
            <p className="text-sm text-gray-500">{percentage.toFixed(1)}%</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Correct Answers</p>
            <p className="text-2xl font-bold text-white">
              {userResponses.filter(r => r.is_correct).length} / {questions.length}
            </p>
            <p className="text-sm text-gray-500">
              {((userResponses.filter(r => r.is_correct).length / questions.length) * 100).toFixed(1)}% accuracy
            </p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4">
            <p className="text-gray-400 text-sm mb-1">Time Taken</p>
            <p className="text-2xl font-bold text-white">
              {Math.floor(results.time_taken_seconds / 60)}m {results.time_taken_seconds % 60}s
            </p>
            <p className="text-sm text-gray-500">
              ~{Math.floor(results.time_taken_seconds / questions.length)}s per question
            </p>
          </div>
        </div>
      </div>

      {/* Domain Performance */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center gap-3 mb-4">
          <Target className="w-6 h-6 text-purple-400" />
          <h3 className="text-xl font-bold text-white">Domain Performance</h3>
        </div>

        <div className="space-y-4">
          {Object.entries(domainPerformance).map(([domain, stats]) => {
            const domainPercentage = (stats.points / stats.maxPoints) * 100;
            const trend = domainPercentage >= 70 ? 'up' : domainPercentage >= 50 ? 'neutral' : 'down';

            return (
              <div key={domain} className="bg-gray-900/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {trend === 'up' && <TrendingUp className="w-5 h-5 text-green-400" />}
                    {trend === 'neutral' && <Minus className="w-5 h-5 text-yellow-400" />}
                    {trend === 'down' && <TrendingDown className="w-5 h-5 text-red-400" />}
                    <span className="font-semibold text-white">{domain}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-400">
                      {stats.correct}/{stats.total} correct
                    </span>
                    <span className={`font-bold ${
                      trend === 'up' ? 'text-green-400' : 
                      trend === 'neutral' ? 'text-yellow-400' : 
                      'text-red-400'
                    }`}>
                      {domainPercentage.toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      trend === 'up' ? 'bg-green-500' : 
                      trend === 'neutral' ? 'bg-yellow-500' : 
                      'bg-red-500'
                    }`}
                    style={{ width: `${domainPercentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Difficulty Analysis */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-6 h-6 text-blue-400" />
          <h3 className="text-xl font-bold text-white">Difficulty Analysis</h3>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {Object.entries(difficultyPerformance).map(([difficulty, stats]) => {
            const percentage = stats.total > 0 ? (stats.correct / stats.total) * 100 : 0;
            return (
              <div key={difficulty} className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-sm text-gray-400 capitalize mb-2">{difficulty}</p>
                <p className="text-3xl font-bold text-white mb-1">
                  {stats.correct}/{stats.total}
                </p>
                <div className="w-full bg-gray-700 rounded-full h-2 mb-1">
                  <div 
                    className={`h-2 rounded-full ${
                      difficulty === 'easy' ? 'bg-green-500' : 
                      difficulty === 'medium' ? 'bg-yellow-500' : 
                      'bg-red-500'
                    }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500">{percentage.toFixed(0)}%</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Assistance Detection */}
      {aiDetectionResults && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Brain className="w-6 h-6 text-pink-400" />
              <h3 className="text-xl font-bold text-white">Response Analysis</h3>
            </div>
            <button
              onClick={() => setShowAIDetails(!showAIDetails)}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              {showAIDetails ? 'Hide Details' : 'Show Details'}
            </button>
          </div>

          <div className={`p-4 rounded-lg border-2 ${
            aiDetectionResults.overallLevel === 'clean' ? 'bg-green-500/10 border-green-500/30' :
            aiDetectionResults.overallLevel === 'possible_assistance' ? 'bg-yellow-500/10 border-yellow-500/30' :
            aiDetectionResults.overallLevel === 'likely_assistance' ? 'bg-orange-500/10 border-orange-500/30' :
            'bg-red-500/10 border-red-500/30'
          }`}>
            <div className="flex items-start gap-3">
              {aiDetectionResults.overallLevel === 'clean' ? (
                <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-6 h-6 text-yellow-400 flex-shrink-0" />
              )}
              <div className="flex-1">
                <p className={`font-semibold mb-2 ${
                  aiDetectionResults.overallLevel === 'clean' ? 'text-green-400' :
                  aiDetectionResults.overallLevel === 'possible_assistance' ? 'text-yellow-400' :
                  'text-orange-400'
                }`}>
                  {aiDetectionResults.recommendation}
                </p>
                
                {showAIDetails && (
                  <div className="mt-4 space-y-2 text-sm text-gray-400">
                    <p>
                      <strong>Overall Suspicion Score:</strong> {aiDetectionResults.overallSuspicionScore.toFixed(0)}/100
                    </p>
                    <p>
                      <strong>Responses Flagged:</strong> {aiDetectionResults.aiLikelyCount} out of {aiDetectionResults.totalResponses}
                    </p>
                    {aiDetectionResults.individualAnalyses.some(a => a.flags.length > 0) && (
                      <div className="mt-3">
                        <p className="font-semibold text-white mb-1">Improvement Areas:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {aiDetectionResults.individualAnalyses
                            .filter(a => a.flags.length > 0)
                            .slice(0, 3)
                            .map((analysis, index) => (
                              <li key={index}>
                                Question {analysis.questionIndex + 1}: {analysis.flags[0]}
                              </li>
                            ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Feedback */}
      {results.ai_feedback && (
        <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-xl p-6 border border-purple-500/30">
          <div className="flex items-center gap-3 mb-4">
            <Award className="w-6 h-6 text-purple-400" />
            <h3 className="text-xl font-bold text-white">AI Feedback & Recommendations</h3>
          </div>
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-300 whitespace-pre-line">{results.ai_feedback}</p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center">
        <button
          onClick={onRetake}
          className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Retake Assessment
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-lg transition-all"
          >
            Return to Dashboard
          </button>
        )}
      </div>
    </div>
  );
}
