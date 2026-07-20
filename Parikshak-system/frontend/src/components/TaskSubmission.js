import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { lifecycleAPI } from '../api';

const TaskSubmission = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        submittedBy: 'Demo User',
        previousTaskId: null
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Pre-fill form if coming from next task
        if (location.state) {
            const { previousTaskId, suggestedTitle, suggestedDescription } = location.state;
            setFormData(prev => ({
                ...prev,
                title: suggestedTitle || prev.title,
                description: suggestedDescription || prev.description,
                previousTaskId: previousTaskId || null
            }));
        }
    }, [location.state]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const result = await lifecycleAPI.submitTask(formData);
            navigate(`/review/${result.submission_id}`, { 
                state: { submissionData: result } 
            });
        } catch (err) {
            setError(err.response?.data?.detail || 'Submission failed');
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    return (
        <div className="task-submission">
            <h2>Submit Task for Review</h2>
            {formData.previousTaskId && (
                <div className="continuation-notice">
                    <p>📋 Continuing from previous task assignment</p>
                </div>
            )}
            
            <form onSubmit={handleSubmit} className="submission-form">
                <div className="form-group">
                    <label htmlFor="title">Task Title *</label>
                    <input
                        id="title"
                        name="title"
                        type="text"
                        value={formData.title}
                        onChange={handleChange}
                        required
                        minLength={5}
                        maxLength={100}
                        placeholder="Enter task title (5-100 characters)"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="description">Task Description *</label>
                    <textarea
                        id="description"
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        required
                        minLength={10}
                        rows={8}
                        placeholder="Enter detailed task description (minimum 10 characters)"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="submittedBy">Your Name *</label>
                    <input
                        id="submittedBy"
                        name="submittedBy"
                        type="text"
                        value={formData.submittedBy}
                        onChange={handleChange}
                        required
                        minLength={2}
                        maxLength={50}
                        placeholder="Enter your name"
                    />
                </div>

                {error && (
                    <div className="error-message">
                        Error: {error}
                    </div>
                )}

                <button 
                    type="submit" 
                    disabled={loading}
                    className="submit-button"
                >
                    {loading ? 'Submitting...' : 'Submit Task'}
                </button>
            </form>
        </div>
    );
};

export default TaskSubmission;