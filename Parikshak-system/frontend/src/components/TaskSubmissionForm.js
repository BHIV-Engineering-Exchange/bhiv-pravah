import React, { useState } from 'react';
import { Send, Github, FileText, Type } from 'lucide-react';
import Button from './ui/Button';

const TaskSubmissionForm = ({ onSubmit, isLoading }) => {
    const [formData, setFormData] = useState({
        submitted_by: '',
        task_title: '',
        task_description: '',
        github_repo_link: '',
        module_id: 'core-development',
        schema_version: '1.0',
        pdf_file: null
    });

    const handleChange = (e) => {
        const { name, value, files } = e.target;
        if (name === 'pdf_file') {
            setFormData((prev) => ({ ...prev, [name]: files[0] }));
        } else {
            setFormData((prev) => ({ ...prev, [name]: value }));
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
                <div>
                    <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        <Type size={16} className="text-blue-500" />
                        Submitted By
                    </label>
                    <input
                        required
                        type="text"
                        name="submitted_by"
                        value={formData.submitted_by}
                        onChange={handleChange}
                        placeholder="Your Name"
                        className="input-field"
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        <Type size={16} className="text-blue-500" />
                        Task Title
                    </label>
                    <input
                        required
                        type="text"
                        name="task_title"
                        value={formData.task_title}
                        onChange={handleChange}
                        placeholder="e.g. Implement User Authentication"
                        className="input-field"
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        <FileText size={16} className="text-blue-500" />
                        Task Description
                    </label>
                    <textarea
                        required
                        name="task_description"
                        rows="4"
                        value={formData.task_description}
                        onChange={handleChange}
                        placeholder="Briefly describe what was implemented..."
                        className="input-field resize-none"
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        <Github size={16} className="text-blue-500" />
                        GitHub Repository URL
                    </label>
                    <input
                        required
                        type="url"
                        name="github_repo_link"
                        value={formData.github_repo_link}
                        onChange={handleChange}
                        placeholder="https://github.com/username/repo"
                        className="input-field"
                    />
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        <Type size={16} className="text-blue-500" />
                        Blueprint Registry Module
                    </label>
                    <select
                        required
                        name="module_id"
                        value={formData.module_id}
                        onChange={handleChange}
                        className="input-field"
                    >
                        <option value="core-development">Core Development</option>
                        <option value="advanced-features">Advanced Features</option>
                        <option value="system-integration">System Integration</option>
                        <option value="performance-optimization">Performance Optimization</option>
                        <option value="security-implementation">Security Implementation</option>
                    </select>
                </div>

                <div>
                    <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">
                        <FileText size={16} className="text-blue-500" />
                        Project PDF (Documentation)
                    </label>
                    <input
                        type="file"
                        name="pdf_file"
                        accept=".pdf"
                        onChange={handleChange}
                        className="file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 block w-full text-sm text-slate-500"
                    />
                </div>
            </div>

            <Button
                type="submit"
                isLoading={isLoading}
                className="w-full"
                size="lg"
            >
                <Send size={20} />
                Submit Task for Review
            </Button>
        </form>
    );
};

export default TaskSubmissionForm;
