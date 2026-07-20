/**
 * Learning Progress Tracker
 * Tracks student learning activities in a calm, non-competitive way
 * Updates progress when students complete learning activities
 */

/**
 * Update progress when a topic is studied
 */
export const trackTopicStudied = (subject, topic) => {
    const progress = getProgress();
    progress.topicsStudied += 1;
    progress.lastActivity = new Date().toISOString();
    saveProgress(progress);
};

/**
 * Update progress when a practice session is completed
 */
export const trackPracticeSession = () => {
    const progress = getProgress();
    progress.practiceSessions += 1;
    progress.lastActivity = new Date().toISOString();
    saveProgress(progress);
};

/**
 * Update progress when a reflection session is completed
 */
export const trackReflectionSession = () => {
    const progress = getProgress();
    progress.reflectionSessions += 1;
    progress.lastActivity = new Date().toISOString();
    saveProgress(progress);
};

/**
 * Update learning streak
 */
export const updateLearningStreak = () => {
    const progress = getProgress();
    const today = new Date().toDateString();
    const lastActivityDate = progress.lastActivity 
        ? new Date(progress.lastActivity).toDateString() 
        : null;
    
    if (lastActivityDate === today) {
        // Already counted today
        return;
    }
    
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toDateString();
    
    if (lastActivityDate === yesterdayStr) {
        // Continuing streak
        progress.learningStreak += 1;
    } else if (lastActivityDate !== today) {
        // New streak
        progress.learningStreak = 1;
    }
    
    saveProgress(progress);
};

/**
 * Get current progress
 */
export const getProgress = () => {
    const saved = localStorage.getItem('gurukul_learning_progress');
    return saved ? JSON.parse(saved) : {
        topicsStudied: 0,
        practiceSessions: 0,
        reflectionSessions: 0,
        learningStreak: 0,
        lastActivity: null
    };
};

/**
 * Save progress to localStorage
 */
const saveProgress = (progress) => {
    localStorage.setItem('gurukul_learning_progress', JSON.stringify(progress));
};

/**
 * Reset progress (for testing or account reset)
 */
export const resetProgress = () => {
    localStorage.removeItem('gurukul_learning_progress');
};

