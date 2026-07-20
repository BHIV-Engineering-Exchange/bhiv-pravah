import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { lifecycleAPI } from '../api';

const TaskHistory = () => {
    const navigate = useNavigate();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadHistory = async () => {
            try {
                const data = await lifecycleAPI.getHistory();
                setHistory(data);
            } catch (err) {
                setError(err.response?.data?.detail || 'Failed to load history');
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
    }, []);

    const getStatusBadge = (status) => {
        const statusClasses = {
            pass: 'status-pass',
            borderline: 'status-borderline',
            fail: 'status-fail'
        };
        return statusClasses[status] || 'status-unknown';
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    if (loading) return <div className="loading">Loading task history...</div>;
    if (error) return <div className="error-message">Error: {error}</div>;

    return (
        <div className="task-history">
            <div className="history-header">
                <h2>Task History</h2>
                <button 
                    onClick={() => navigate('/')}
                    className="new-task-btn"
                >
                    Submit New Task
                </button>
            </div>

            {history.length === 0 ? (
                <div className="empty-history">
                    <p>No tasks submitted yet.</p>
                    <button onClick={() => navigate('/')}>Submit Your First Task</button>
                </div>
            ) : (
                <div className="history-list">
                    {history.map((item) => (
                        <div key={item.submission_id} className="history-item">
                            <div className="history-content">
                                <div className="task-info">
                                    <h3>{item.task_title}</h3>
                                    <p className="submitted-by">By: {item.submitted_by}</p>
                                    <p className="submitted-date">{formatDate(item.submitted_at)}</p>
                                </div>
                                
                                <div className="task-metrics">
                                    <div className="score-display">
                                        <span className="score-value">{item.score}/100</span>
                                        <span className="score-label">Score</span>
                                    </div>
                                    <div className={`status-badge ${getStatusBadge(item.status)}`}>
                                        {item.status.toUpperCase()}
                                    </div>
                                </div>
                            </div>
                            
                            <div className="history-actions">
                                <button 
                                    onClick={() => navigate(`/review/${item.submission_id}`)}
                                    className="view-review-btn"
                                >
                                    View Review
                                </button>
                                <button 
                                    onClick={() => navigate(`/next-task/${item.submission_id}`)}
                                    className="view-next-task-btn"
                                >
                                    Next Task
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default TaskHistory;