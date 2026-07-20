import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { lifecycleAPI } from '../api';

const NextTaskDetails = () => {
    const { submissionId } = useParams();
    const navigate = useNavigate();
    const [nextTask, setNextTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadNextTask = async () => {
            try {
                const data = await lifecycleAPI.getNextTask(submissionId);
                setNextTask(data);
            } catch (err) {
                setError(err.response?.data?.detail || 'Failed to load next task');
            } finally {
                setLoading(false);
            }
        };

        loadNextTask();
    }, [submissionId]);

    const getDifficultyColor = (difficulty) => {
        const colors = {
            beginner: '#10b981',
            intermediate: '#f59e0b',
            advanced: '#ef4444'
        };
        return colors[difficulty] || '#3b82f6';
    };

    const getTaskTypeIcon = (taskType) => {
        const icons = {
            correction: '🔧',
            reinforcement: '💪',
            advancement: '🚀'
        };
        return icons[taskType] || '📋';
    };

    const handleContinueWithTask = () => {
        // Navigate to submission form with this task as context
        navigate('/', { 
            state: { 
                previousTaskId: nextTask.next_task_id,
                suggestedTitle: nextTask.title,
                suggestedDescription: nextTask.objective
            } 
        });
    };

    if (loading) return <div className="loading">Loading next task details...</div>;
    if (error) return <div className="error-message">Error: {error}</div>;

    return (
        <div className="next-task-details">
            <div className="task-header">
                <h2>Next Task Assignment</h2>
                <div className="navigation-buttons">
                    <button onClick={() => navigate(`/review/${submissionId}`)}>
                        Back to Review
                    </button>
                    <button onClick={() => navigate('/history')}>
                        View History
                    </button>
                </div>
            </div>

            <div className="task-card">
                <div className="task-meta">
                    <div className="task-type">
                        <span className="task-icon">{getTaskTypeIcon(nextTask.task_type)}</span>
                        <span className="task-type-label">{nextTask.task_type.toUpperCase()}</span>
                    </div>
                    <div 
                        className="difficulty-badge"
                        style={{ backgroundColor: getDifficultyColor(nextTask.difficulty) }}
                    >
                        {nextTask.difficulty.toUpperCase()}
                    </div>
                </div>

                <h3 className="task-title">{nextTask.title}</h3>
                
                <div className="task-details">
                    <div className="detail-section">
                        <h4>Objective</h4>
                        <p>{nextTask.objective}</p>
                    </div>

                    <div className="detail-section">
                        <h4>Focus Area</h4>
                        <p>{nextTask.focus_area}</p>
                    </div>

                    <div className="detail-section">
                        <h4>Assignment Reason</h4>
                        <p>{nextTask.reason}</p>
                    </div>

                    <div className="detail-section">
                        <h4>Assigned</h4>
                        <p>{new Date(nextTask.assigned_at).toLocaleString()}</p>
                    </div>
                </div>

                <div className="task-actions">
                    <button 
                        onClick={handleContinueWithTask}
                        className="continue-task-btn primary"
                    >
                        Continue with This Task
                    </button>
                    <button 
                        onClick={() => navigate('/')}
                        className="new-task-btn secondary"
                    >
                        Submit Different Task
                    </button>
                </div>
            </div>

            <div className="task-info">
                <h4>Task ID: {nextTask.next_task_id}</h4>
                <p>This task was automatically assigned based on your previous submission's review results.</p>
            </div>
        </div>
    );
};

export default NextTaskDetails;