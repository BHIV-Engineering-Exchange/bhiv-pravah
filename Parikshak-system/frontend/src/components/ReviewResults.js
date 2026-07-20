import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { lifecycleAPI } from '../api';

const ReviewResults = () => {
    const { submissionId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    const [review, setReview] = useState(null);
    const [nextTask, setNextTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadReviewData = async () => {
            try {
                // Use passed data if available, otherwise fetch
                if (location.state?.submissionData) {
                    const data = location.state.submissionData;
                    setReview(data.review_summary);
                    setNextTask(data.next_task_summary);
                } else {
                    const [reviewData, nextTaskData] = await Promise.all([
                        lifecycleAPI.getReview(submissionId),
                        lifecycleAPI.getNextTask(submissionId)
                    ]);
                    setReview(reviewData);
                    setNextTask(nextTaskData);
                }
            } catch (err) {
                setError(err.response?.data?.detail || 'Failed to load review data');
            } finally {
                setLoading(false);
            }
        };

        loadReviewData();
    }, [submissionId, location.state]);

    const getStatusColor = (status) => {
        const colors = {
            pass: '#10b981',
            borderline: '#f59e0b',
            fail: '#ef4444'
        };
        return colors[status] || '#3b82f6';
    };

    if (loading) return <div className="loading">Loading review results...</div>;
    if (error) return <div className="error-message">Error: {error}</div>;

    return (
        <div className="review-results">
            <div className="review-header">
                <h2>Review Results</h2>
                <div className="navigation-buttons">
                    <button onClick={() => navigate('/history')}>View History</button>
                    <button onClick={() => navigate('/')}>New Submission</button>
                </div>
            </div>

            <div className="status-section" style={{ borderColor: getStatusColor(review.status) }}>
                <h3 style={{ color: getStatusColor(review.status) }}>
                    Status: {review.status.toUpperCase()}
                </h3>
                
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-label">Score</div>
                        <div className="metric-value">{review.score}/100</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">Readiness</div>
                        <div className="metric-value">{review.readiness_percent}%</div>
                    </div>
                </div>
            </div>

            {review.analysis && (
                <div className="analysis-section">
                    <h3>Technical Analysis</h3>
                    <div className="progress-grid">
                        <div className="progress-item">
                            <span>Technical Quality: {review.analysis.technical_quality}%</span>
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill" 
                                    style={{ width: `${review.analysis.technical_quality}%` }}
                                />
                            </div>
                        </div>
                        <div className="progress-item">
                            <span>Clarity: {review.analysis.clarity}%</span>
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill" 
                                    style={{ width: `${review.analysis.clarity}%` }}
                                />
                            </div>
                        </div>
                        <div className="progress-item">
                            <span>Discipline Signals: {review.analysis.discipline_signals}%</span>
                            <div className="progress-bar">
                                <div 
                                    className="progress-fill" 
                                    style={{ width: `${review.analysis.discipline_signals}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {review.failure_reasons && review.failure_reasons.length > 0 && (
                <div className="feedback-section failure">
                    <h3>Failure Reasons</h3>
                    <ul>
                        {review.failure_reasons.map((reason, idx) => (
                            <li key={idx}>{reason}</li>
                        ))}
                    </ul>
                </div>
            )}

            {review.improvement_hints && review.improvement_hints.length > 0 && (
                <div className="feedback-section hints">
                    <h3>Improvement Hints</h3>
                    <ul>
                        {review.improvement_hints.map((hint, idx) => (
                            <li key={idx}>{hint}</li>
                        ))}
                    </ul>
                </div>
            )}

            {nextTask && (
                <div className="next-task-section">
                    <h3>Next Task Assignment</h3>
                    <div className="next-task-card">
                        <h4>{nextTask.title}</h4>
                        <p><strong>Type:</strong> {nextTask.task_type}</p>
                        <p><strong>Difficulty:</strong> {nextTask.difficulty}</p>
                        {nextTask.objective && <p><strong>Objective:</strong> {nextTask.objective}</p>}
                        <button 
                            onClick={() => navigate(`/next-task/${submissionId}`)}
                            className="view-next-task-btn"
                        >
                            View Full Next Task Details
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ReviewResults;