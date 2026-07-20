/**
 * @typedef {Object} Task
 * @property {string} id
 * @property {string} task_title
 * @property {string} task_description
 * @property {string} github_repo_link
 * @property {string} status - 'assigned' | 'submitted' | 'reviewed' | 'next_assigned'
 * @property {number} review_score
 * @property {string} feedback
 * @property {string} evaluation_summary
 * @property {string} submission_date
 * @property {string} lifecycle_stage
 */

export const TaskStatus = {
    ASSIGNED: 'assigned',
    SUBMITTED: 'submitted',
    REVIEWED: 'reviewed',
    NEXT_ASSIGNED: 'next_assigned',
};

export const DifficultyLevel = {
    BEGINNER: 'beginner',
    INTERMEDIATE: 'intermediate',
    ADVANCED: 'advanced',
    EXPERT: 'expert',
};
