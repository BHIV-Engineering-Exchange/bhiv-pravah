import React, { useState, useEffect } from 'react'
import { useAuth } from "../../contexts/AuthContext"
import {
  BookOpen, Brain, Clock, Star, Target, Trophy, BarChart3, Users, TrendingUp,
  Calendar, ChevronRight, Award, Activity, Zap, BookMarked, TrendingDown,
  CheckCircle, XCircle, ArrowRight, PlayCircle, PieChart, LineChart,
  Map, Compass, Lightbulb, Timer, Medal, GraduationCap
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { CLERK_ENABLED } from '../config/auth'
import { useI18n } from "../lib/i18n";
import { toast } from 'react-hot-toast'

export default function Dashboard() {
  const { user } = useAuth()
  const { t } = useI18n();
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState({
    recentAttempts: [],
    stats: null,
    streaks: null,
    achievements: [],
    recommendations: []
  })

  useEffect(() => {
    if (user) {
      loadDashboardData()
    } else {
      setLoading(false)
    }
  }, [user])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      console.log('📊 Loading dashboard data for:', user.id)

      // Load recent assignment attempts
      const { data: attemptsData, error: attemptsError } = await supabase
        .from('assignment_attempts')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(5)

      if (attemptsError) {
        console.error('Error loading attempts:', attemptsError)
        return
      }

      // Calculate comprehensive statistics
      if (attemptsData && attemptsData.length > 0) {
        const stats = calculateStats(attemptsData)
        const streaks = calculateStreaks(attemptsData)
        const achievements = calculateAchievements(attemptsData)
        const recommendations = generateRecommendations(attemptsData)

        setDashboardData({
          recentAttempts: attemptsData,
          stats,
          streaks,
          achievements,
          recommendations
        })
      }

      console.log('✅ Dashboard data loaded successfully')

    } catch (error) {
      console.error('Error loading dashboard data:', error)
      toast.error(t('dashboard.loading') || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const calculateStats = (attempts) => {
    const totalAttempts = attempts.length
    const averageScore = attempts.reduce((sum, attempt) => sum + attempt.percentage, 0) / totalAttempts
    const bestScore = Math.max(...attempts.map(attempt => attempt.percentage))
    const totalTimeSpent = attempts.reduce((sum, attempt) => sum + attempt.time_taken_seconds, 0)
    const improvement = attempts.length >= 2 ? attempts[0].percentage - attempts[attempts.length - 1].percentage : 0

    const gradeDistribution = attempts.reduce((dist, attempt) => {
      dist[attempt.grade] = (dist[attempt.grade] || 0) + 1
      return dist
    }, {})

    return {
      totalAttempts,
      averageScore,
      bestScore,
      totalTimeSpent,
      improvement,
      gradeDistribution
    }
  }

  const calculateStreaks = (attempts) => {
    let currentStreak = 0
    let longestStreak = 0

    // Calculate current streak (consecutive days with attempts)
    const today = new Date()
    const daysSinceLastAttempt = Math.floor((today - new Date(attempts[0]?.created_at)) / (1000 * 60 * 60 * 24))

    if (daysSinceLastAttempt <= 1) {
      currentStreak = 1
      // Count consecutive days
      for (let i = 1; i < attempts.length; i++) {
        const daysDiff = Math.floor((new Date(attempts[i - 1].created_at) - new Date(attempts[i].created_at)) / (1000 * 60 * 60 * 24))
        if (daysDiff <= 1) {
          currentStreak++
        } else {
          break
        }
      }
    }

    return { currentStreak, longestStreak: Math.max(longestStreak, currentStreak) }
  }

  const calculateAchievements = (attempts) => {
    const achievements = []
    const stats = calculateStats(attempts)

    if (stats.totalAttempts >= 1) achievements.push({ icon: Medal, title: 'First Steps', description: 'Completed your first assessment', color: 'text-green-400' })
    if (stats.totalAttempts >= 5) achievements.push({ icon: Trophy, title: 'Dedicated Learner', description: 'Completed 5 assessments', color: 'text-yellow-400' })
    if (stats.bestScore >= 90) achievements.push({ icon: Star, title: 'Excellence', description: 'Scored 90% or higher', color: 'text-purple-400' })
    if (stats.averageScore >= 80) achievements.push({ icon: Award, title: 'Consistent Performer', description: 'Average score above 80%', color: 'text-blue-400' })
    if (stats.improvement > 20) achievements.push({ icon: TrendingUp, title: 'Rising Star', description: 'Improved by 20+ points', color: 'text-orange-400' })

    return achievements.slice(0, 3)
  }

  const generateRecommendations = (attempts) => {
    const recommendations = []
    const stats = calculateStats(attempts)
    const latestAttempt = attempts[0]

    if (stats.averageScore < 70) {
      recommendations.push({
        icon: BookOpen,
        title: 'Focus on Fundamentals',
        description: 'Review basic concepts to strengthen your foundation',
        action: 'Take Assessment',
        link: '/assignment',
        color: 'bg-blue-500/20 border-blue-400/30'
      })
    }

    if (latestAttempt && latestAttempt.percentage >= 80) {
      recommendations.push({
        icon: Zap,
        title: 'Advanced Challenge',
        description: 'You\'re ready for more complex assessments',
        action: 'Take Advanced Test',
        link: '/assignment',
        color: 'bg-purple-500/20 border-purple-400/30'
      })
    }

    if (stats.totalAttempts < 3) {
      recommendations.push({
        icon: Target,
        title: 'Build Momentum',
        description: 'Take more assessments to track your progress',
        action: 'Take Assessment',
        link: '/assignment',
        color: 'bg-orange-500/20 border-orange-400/30'
      })
    }

    return recommendations.slice(0, 2)
  }

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return 'text-green-400 bg-green-500/20'
      case 'B': return 'text-blue-400 bg-blue-500/20'
      case 'C': return 'text-orange-400 bg-orange-500/20'
      case 'D': return 'text-yellow-400 bg-yellow-500/20'
      case 'F': return 'text-red-400 bg-red-500/20'
      default: return 'text-white bg-white/20'
    }
  }

  return (
    <div className="min-h-screen p-6">
      <div className="w-full max-w-7xl mx-auto space-y-6">
        {/* Header Section */}
        <div className="text-center space-y-4">
          {/* Student Tier Highlight */}
          {dashboardData.recentAttempts.length > 0 && (
            <div className="flex justify-center">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl border border-orange-400/30 px-6 py-4 shadow-xl">
                <div className="flex items-center gap-4">
                  <div className="text-3xl">
                    {dashboardData.stats.averageScore >= 90 ? '☁️' : dashboardData.stats.averageScore >= 75 ? '🌳' : '🌱'}
                  </div>
                  <div className="text-left">
                    <div className="text-lg font-bold text-white">
                      {dashboardData.stats.averageScore >= 90 ? 'Sky Level (Akash)' :
                        dashboardData.stats.averageScore >= 75 ? 'Tree Level (Vriksha)' :
                          'Seed Level (Beej)'}
                    </div>
                    <div className="text-sm text-orange-200/80">
                      {dashboardData.stats.averageScore >= 90 ? 'Mastery Achieved • Wisdom Synthesis' :
                        dashboardData.stats.averageScore >= 75 ? 'Growing Strong • Skill Development' :
                          'Foundation Building • Core Learning'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">{dashboardData.stats.averageScore.toFixed(1)}%</div>
                    <div className="text-sm text-orange-200/60">{t('dashboard.currentLevel')}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent mb-4">
              {user ?
                (dashboardData.recentAttempts.length > 0 ?
                  `Welcome back, ${user.full_name || 'Student'}!` :
                  `Welcome, ${user.full_name || 'Student'}!`
                ) :
                'Gurukul Learning Analytics Hub'
              }
            </h1>
            <p className="text-white/70 text-lg max-w-4xl mx-auto leading-relaxed">
              {loading ? 'Loading your comprehensive learning analytics...' :
                dashboardData.recentAttempts.length > 0 ?
                  'Your comprehensive Gurukul learning analytics dashboard featuring real-time performance tracking across multiple domains.' :
                  'Welcome to your personalized Gurukul learning analytics hub. This intelligent dashboard will unlock detailed performance insights once you complete your first assessment.'}
            </p>
            <div className="mt-4 text-sm text-white/50">
              {dashboardData.recentAttempts.length > 0 ?
                '📊 Real-time analytics • 🎯 AI-powered insights • 🏆 Achievement tracking • 📈 Progress monitoring' :
                '🚀 AI-generated assessments • ⚡ Instant evaluation • 📊 Detailed analytics • 🎯 Personalized learning paths'}
            </div>
          </div>
        </div>

        {user ? (
          <div>
            {loading ? (
              <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
                <div className="text-white/60 text-lg">Loading dashboard...</div>
              </div>
            ) : dashboardData.recentAttempts.length > 0 ? (
              <div className="space-y-6">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-blue-400/20 hover:bg-white/15 transition-all group">
                    <div className="text-3xl font-bold text-white mb-2">{dashboardData.stats.averageScore.toFixed(1)}%</div>
                    <div className="text-white/60 text-sm mb-2">Average Performance</div>
                    <div className="text-white/40 text-xs leading-relaxed">Composite score across {dashboardData.stats.totalAttempts} assessments</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-green-400/20 hover:bg-white/15 transition-all group">
                    <div className="text-3xl font-bold text-white mb-2">{dashboardData.stats.bestScore.toFixed(1)}%</div>
                    <div className="text-white/60 text-sm mb-2">Peak Achievement</div>
                    <div className="text-white/40 text-xs leading-relaxed">Your highest performance benchmark</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-purple-400/20 hover:bg-white/15 transition-all group">
                    <div className="text-3xl font-bold text-white mb-2">{formatTime(dashboardData.stats.totalTimeSpent)}</div>
                    <div className="text-white/60 text-sm mb-2">Learning Investment</div>
                    <div className="text-white/40 text-xs leading-relaxed">Total focused study time</div>
                  </div>
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-orange-400/20 hover:bg-white/15 transition-all group">
                    <div className="text-3xl font-bold text-white mb-2">{dashboardData.streaks?.currentStreak || 0}</div>
                    <div className="text-white/60 text-sm mb-2">Consistency Streak</div>
                    <div className="text-white/40 text-xs leading-relaxed">Consecutive days of learning</div>
                  </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Assessment History */}
                  <div className="lg:col-span-2 bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-blue-400/20">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-xl font-semibold text-white flex items-center gap-3">
                          <Activity className="h-6 w-6 text-blue-400" /> {t('dashboard.assessmentHistory')}
                        </h3>
                        <p className="text-white/50 text-sm mt-2">{t('dashboard.assessmentHistoryDesc')}</p>
                      </div>
                      <Link to="/assignment" className="bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 px-4 py-2 rounded-xl border border-orange-400/30 transition-all text-sm font-medium">
                        {t('dashboard.newAssessment')}
                      </Link>
                    </div>
                    <div className="space-y-4">
                      {dashboardData.recentAttempts.slice(0, 3).map((attempt) => (
                        <div key={attempt.id} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all">
                          <div className="flex items-center gap-4">
                            <div className={`px-3 py-2 rounded-lg text-sm font-medium ${getGradeColor(attempt.grade)} border border-current/30`}>
                              {t('dashboard.grade')} {attempt.grade}
                            </div>
                            <div>
                              <div className="text-lg font-medium text-white flex items-center gap-2">
                                {attempt.percentage.toFixed(1)}%
                                {attempt.percentage >= 90 && <span className="text-sm">🏆</span>}
                                {attempt.percentage >= 80 && attempt.percentage < 90 && <span className="text-sm">⭐</span>}
                              </div>
                              <div className="text-white/60 text-sm">
                                {attempt.total_questions} {t('dashboard.questions')} • {formatTime(attempt.time_taken_seconds)}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-white/80 text-sm font-medium">{formatDate(attempt.created_at)}</div>
                            <div className="text-white/50 text-xs mt-1 flex items-center gap-1">
                              <Brain className="h-3 w-3" />
                              {t('dashboard.aiEvaluated')}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="space-y-6">
                    <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-orange-400/20">
                      <h3 className="text-xl font-semibold text-white flex items-center gap-3 mb-4">
                        <Zap className="h-6 w-6 text-orange-400" /> {t('dashboard.quickActions')}
                      </h3>
                      <div className="space-y-3">
                        <Link to="/assignment" className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-400/30 hover:from-orange-500/30 transition-all group">
                          <Target className="w-6 h-6 text-orange-400" />
                          <div className="flex-1 text-left">
                            <div className="text-sm font-medium text-white">{t('dashboard.takeAssessment')}</div>
                            <div className="text-xs text-orange-200/80">{t('dashboard.aiPoweredEvaluation')}</div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-white/40" />
                        </Link>
                        <Link to="/assessment/intake" className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-400/30 hover:from-purple-500/30 transition-all group">
                          <Users className="w-6 h-6 text-purple-400" />
                          <div className="flex-1 text-left">
                            <div className="text-sm font-medium text-white">{t('dashboard.editProfile')}</div>
                            <div className="text-xs text-purple-200/80">{t('dashboard.updateInformation')}</div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-white/40" />
                        </Link>
                      </div>
                    </div>

                    {/* Achievements */}
                    {dashboardData.achievements.length > 0 && (
                      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-yellow-400/20">
                        <h3 className="text-xl font-semibold text-white flex items-center gap-3 mb-4">
                          <Award className="h-6 w-6 text-yellow-400" /> {t('dashboard.achievements')}
                        </h3>
                        <div className="space-y-3">
                          {dashboardData.achievements.slice(0, 2).map((achievement, index) => (
                            <div key={index} className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10">
                              <achievement.icon className={`w-5 h-5 ${achievement.color}`} />
                              <div className="flex-1">
                                <div className="text-sm font-medium text-white">{achievement.title}</div>
                                <div className="text-xs text-white/60">{achievement.description}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Gurukul Learning System */}
                <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-green-400/20">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-xl font-semibold text-white flex items-center gap-3">
                        <Map className="h-6 w-6 text-green-400" /> {t('dashboard.ancientGurukul')}
                      </h3>
                      <p className="text-white/50 text-sm mt-2">{t('dashboard.ancientGurukulDesc')}</p>
                    </div>
                    <div className="text-sm text-green-400/80 font-medium px-3 py-1 bg-green-500/20 rounded-lg">
                      {t('dashboard.yearsOld')}
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
                    <div className={`text-center p-4 sm:p-6 rounded-xl border transition-all ${dashboardData.stats.averageScore < 75 ?
                      'bg-gradient-to-br from-yellow-500/30 to-orange-500/30 border-yellow-400/50 shadow-lg' :
                      'bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-yellow-400/30'
                      }`}>
                      <div className="text-2xl sm:text-4xl mb-2 sm:mb-3">🌱</div>
                      <div className="text-base sm:text-lg font-semibold text-white mb-1 sm:mb-2">Seed Level (Beej)</div>
                      <div className="text-xs sm:text-sm text-yellow-200/80 mb-2 sm:mb-3">Foundation building • Core concepts</div>
                      <div className="text-xs text-yellow-300/60">Absorb fundamental knowledge across domains</div>
                    </div>
                    <div className={`text-center p-4 sm:p-6 rounded-xl border transition-all ${dashboardData.stats.averageScore >= 75 && dashboardData.stats.averageScore < 90 ?
                      'bg-gradient-to-br from-green-500/30 to-emerald-500/30 border-green-400/50 shadow-lg' :
                      'bg-gradient-to-br from-green-500/20 to-emerald-500/20 border-green-400/30'
                      }`}>
                      <div className="text-2xl sm:text-4xl mb-2 sm:mb-3">🌳</div>
                      <div className="text-base sm:text-lg font-semibold text-white mb-1 sm:mb-2">Tree Level (Vriksha)</div>
                      <div className="text-xs sm:text-sm text-green-200/80 mb-2 sm:mb-3">Growth phase • Skill development</div>
                      <div className="text-xs text-green-300/60">Expanding branches of specialized knowledge</div>
                    </div>
                    <div className={`text-center p-4 sm:p-6 rounded-xl border transition-all ${dashboardData.stats.averageScore >= 90 ?
                      'bg-gradient-to-br from-blue-500/30 to-cyan-500/30 border-blue-400/50 shadow-lg' :
                      'bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border-blue-400/30'
                      }`}>
                      <div className="text-2xl sm:text-4xl mb-2 sm:mb-3">☁️</div>
                      <div className="text-base sm:text-lg font-semibold text-white mb-1 sm:mb-2">Sky Level (Akash)</div>
                      <div className="text-xs sm:text-sm text-blue-200/80 mb-2 sm:mb-3">Mastery • Wisdom synthesis</div>
                      <div className="text-xs text-blue-300/60">Boundless understanding across subjects</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              // First-time user
              <div className="text-center py-16">
                <div className="bg-white/5 backdrop-blur-sm rounded-3xl p-12 border border-orange-400/20 max-w-2xl mx-auto">
                  <div className="flex items-center justify-center gap-4 mb-8">
                    <div className="p-4 rounded-2xl bg-orange-500/20">
                      <Star className="h-12 w-12 text-orange-400" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white">{t('dashboard.startYourJourney')}</h2>
                      <p className="text-orange-200 text-lg">{t('dashboard.takeYourFirstAssessment')}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                    <div className="flex flex-col items-center gap-2 text-white/80">
                      <BookOpen className="h-8 w-8 text-blue-400" />
                      <span className="text-sm font-medium">10 Questions</span>
                    </div>
                    <div className="flex flex-col items-center gap-2 text-white/80">
                      <Clock className="h-8 w-8 text-green-400" />
                      <span className="text-sm font-medium">30 Minutes</span>
                    </div>
                    <div className="flex flex-col items-center gap-2 text-white/80">
                      <Brain className="h-8 w-8 text-purple-400" />
                      <span className="text-sm font-medium">AI Generated</span>
                    </div>
                    <div className="flex flex-col items-center gap-2 text-white/80">
                      <Trophy className="h-8 w-8 text-orange-400" />
                      <span className="text-sm font-medium">AI Evaluation</span>
                    </div>
                  </div>

                  <Link to="/assignment" className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold rounded-2xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 text-lg">
                    <PlayCircle className="h-6 w-6" />
                    {t('dashboard.takeYourFirstAssessmentCta')}
                  </Link>
                </div>
              </div>
            )}
          </div>
        ) : (
          // Non-authenticated
          <div className="text-center py-16">
            <div className="bg-white/5 backdrop-blur-sm rounded-3xl p-12 border border-orange-400/20 max-w-2xl mx-auto">
              <div className="flex items-center justify-center gap-4 mb-8">
                <div className="p-4 rounded-2xl bg-orange-500/20">
                  <Target className="h-12 w-12 text-orange-400" />
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-white">{t('dashboard.experienceGurukul')}</h2>
                  <p className="text-orange-200 text-lg">{t('dashboard.aiPoweredAssessments')}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                <div className="flex flex-col items-center gap-2 text-white/80">
                  <BookOpen className="h-8 w-8 text-blue-400" />
                  <span className="text-sm font-medium">10 Questions</span>
                </div>
                <div className="flex flex-col items-center gap-2 text-white/80">
                  <Clock className="h-8 w-8 text-green-400" />
                  <span className="text-sm font-medium">30 Minutes</span>
                </div>
                <div className="flex flex-col items-center gap-2 text-white/80">
                  <Brain className="h-8 w-8 text-purple-400" />
                  <span className="text-sm font-medium">AI Generated</span>
                </div>
                <div className="flex flex-col items-center gap-2 text-white/80">
                  <Trophy className="h-8 w-8 text-orange-400" />
                  <span className="text-sm font-medium">AI Evaluation</span>
                </div>
              </div>

              <Link to="/assignment" className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold rounded-2xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 text-lg">
                <Target className="h-6 w-6" />
                {t('dashboard.tryAssessmentNow')}
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}