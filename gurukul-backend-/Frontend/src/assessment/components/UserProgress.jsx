import React, { useState, useEffect } from 'react';
import { useAuth } from "../../contexts/AuthContext";
import { supabase } from '../lib/supabaseClient';
import { CLERK_ENABLED } from '../config/auth';
import {
  Trophy,
  Calendar,
  Clock,
  TrendingUp,
  BarChart3,
  User,
  Award,
  Target,
  BookOpen
} from 'lucide-react';
import { toast } from 'react-hot-toast';

export default function UserProgress() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [attempts, setAttempts] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (user) {
      loadUserProgress();
    } else {
      setLoading(false);
    }
  }, [user]);

  const loadUserProgress = async () => {
    try {
      setLoading(true);
      console.log('📊 Loading user progress for:', user.id);

      // Load assignment attempts
      const { data: attemptsData, error: attemptsError } = await supabase
        .from('assignment_attempts')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (attemptsError) {
        console.error('Error loading attempts:', attemptsError);
        toast.error('Failed to load assignment history');
        return;
      }

      setAttempts(attemptsData || []);

      // Calculate statistics
      if (attemptsData && attemptsData.length > 0) {
        const stats = {
          totalAttempts: attemptsData.length,
          averageScore: attemptsData.reduce((sum, attempt) => sum + attempt.percentage, 0) / attemptsData.length,
          bestScore: Math.max(...attemptsData.map(attempt => attempt.percentage)),
          totalTimeSpent: attemptsData.reduce((sum, attempt) => sum + attempt.time_taken_seconds, 0),
          gradeDistribution: attemptsData.reduce((dist, attempt) => {
            dist[attempt.grade] = (dist[attempt.grade] || 0) + 1;
            return dist;
          }, {}),
          recentImprovement: attemptsData.length >= 2 ?
            attemptsData[0].percentage - attemptsData[1].percentage : 0
        };
        setStats(stats);
      }

      console.log('✅ User progress loaded:', { attempts: attemptsData?.length, stats });

    } catch (error) {
      console.error('Error loading user progress:', error);
      toast.error('Failed to load progress data');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return 'text-green-400 bg-green-500/20';
      case 'B': return 'text-blue-400 bg-blue-500/20';
      case 'C': return 'text-orange-400 bg-orange-500/20';
      case 'D': return 'text-yellow-400 bg-yellow-500/20';
      case 'F': return 'text-red-400 bg-red-500/20';
      default: return 'text-white bg-white/20';
    }
  };

  if (!user) {
    return (
      <div className="text-center p-8">
        <User className="h-12 w-12 text-white/40 mx-auto mb-4" />
        <div className="text-white/60">Please sign in to view your progress</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
        <div className="text-white/60">Loading your progress...</div>
      </div>
    );
  }

  if (attempts.length === 0) {
    return (
      <div className="text-center p-8">
        <BookOpen className="h-12 w-12 text-white/40 mx-auto mb-4" />
        <div className="text-white/60 mb-4">No assignments completed yet</div>
        <div className="text-sm text-white/40">Take your first assignment to see your progress here!</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* User Header */}
      <div className="flex items-center gap-4 p-4 rounded-lg bg-white/5 border border-white/10">
        <div className="p-3 rounded-full bg-blue-500/20">
          <User className="h-6 w-6 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            {user.fullName || user.firstName || 'Student'} Progress
          </h2>
          <div className="text-blue-300 text-sm">
            {user.email}
          </div>
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <div className="p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <Target className="h-5 w-5 text-orange-400" />
              <span className="text-white/80 text-sm">Total Attempts</span>
            </div>
            <div className="text-2xl font-bold text-white">{stats.totalAttempts}</div>
          </div>

          <div className="p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              <span className="text-white/80 text-sm">Average Score</span>
            </div>
            <div className="text-2xl font-bold text-white">{stats.averageScore.toFixed(1)}%</div>
          </div>

          <div className="p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <Trophy className="h-5 w-5 text-green-400" />
              <span className="text-white/80 text-sm">Best Score</span>
            </div>
            <div className="text-2xl font-bold text-white">{stats.bestScore.toFixed(1)}%</div>
          </div>

          <div className="p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="h-5 w-5 text-purple-400" />
              <span className="text-white/80 text-sm">Total Time</span>
            </div>
            <div className="text-2xl font-bold text-white">{formatTime(stats.totalTimeSpent)}</div>
          </div>
        </div>
      )}

      {/* Recent Improvement */}
      {stats && stats.recentImprovement !== 0 && (
        <div className={`p-4 rounded-lg border ${stats.recentImprovement > 0
          ? 'bg-green-500/10 border-green-500/30'
          : 'bg-red-500/10 border-red-500/30'
          }`}>
          <div className="flex items-center gap-3">
            <TrendingUp className={`h-5 w-5 ${stats.recentImprovement > 0 ? 'text-green-400' : 'text-red-400'
              }`} />
            <span className="text-white font-medium">
              {stats.recentImprovement > 0 ? 'Improvement' : 'Recent Change'}
            </span>
            <span className={`font-bold ${stats.recentImprovement > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
              {stats.recentImprovement > 0 ? '+' : ''}{stats.recentImprovement.toFixed(1)}%
            </span>
          </div>
        </div>
      )}

      {/* Assignment History */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">Assignment History</h3>
        <div className="space-y-3">
          {attempts.map((attempt, index) => (
            <div key={attempt.id} className="p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`px-3 py-1 rounded-full text-sm font-bold ${getGradeColor(attempt.grade)}`}>
                    {attempt.grade}
                  </div>
                  <div>
                    <div className="text-white font-medium">
                      {attempt.percentage.toFixed(1)}% ({attempt.total_score.toFixed(1)}/{attempt.max_score})
                    </div>
                    <div className="text-white/60 text-sm">
                      {formatDate(attempt.completed_at)} • {formatTime(attempt.time_taken_seconds)}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white/60 text-sm">
                    Attempt #{attempts.length - index}
                  </div>
                  {attempt.auto_submitted && (
                    <div className="text-orange-400 text-xs">Auto-submitted</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
