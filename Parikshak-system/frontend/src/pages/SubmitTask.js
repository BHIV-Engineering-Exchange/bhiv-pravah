import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Upload, FileText, X, Settings, Code, AlertTriangle, ArrowLeft, RefreshCw } from 'lucide-react';
import ConnectionStatus from '../components/ConnectionStatus';

const SubmitTask = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        task_title: '',
        task_description: '',
        submitted_by: 'Ishan Shirode', // Pre-fill with candidate/operator name
        github_repo_link: '',
        module_id: 'task-review-agent',
        schema_version: 'v1.0'
    });
    const [pdfFile, setPdfFile] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [validationErrors, setValidationErrors] = useState({});

    const availableModules = [
        { id: 'task-review-agent',       name: 'Parikshak (v1.0) - General Review', schema: 'v1.0' },
        { id: 'core-development',        name: 'Core Development (v1.0)',         schema: 'v1.0' },
        { id: 'advanced-features',       name: 'Advanced Features (v1.0)',        schema: 'v1.0' },
        { id: 'system-integration',      name: 'System Integration (v1.0)',       schema: 'v1.0' },
        { id: 'evaluation-engine',       name: 'Evaluation Engine (v3.0)',        schema: 'v3.0' }
    ];

    const handleModuleChange = (e) => {
        const selectedMod = availableModules.find(m => m.id === e.target.value);
        setFormData(prev => ({
            ...prev,
            module_id: e.target.value,
            schema_version: selectedMod ? selectedMod.schema : 'v1.0'
        }));
    };

    const validateInputs = () => {
        const errors = {};
        if (formData.github_repo_link) {
            const githubRepoPattern = /^https:\/\/github\.com\/[^/]+\/[^/]+\/?$/;
            if (!githubRepoPattern.test(formData.github_repo_link)) {
                errors.github_repo_link = 'Must be a valid GitHub repository URL (e.g., https://github.com/user/repo)';
            }
        }
        return errors;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const errors = validateInputs();
        if (Object.keys(errors).length > 0) {
            setValidationErrors(errors);
            return;
        }
        
        setValidationErrors({});
        setIsSubmitting(true);
        
        try {
            const { taskService } = await import('../services/taskService');
            const result = await taskService.submitTask({
                ...formData,
                pdf_file: pdfFile || undefined
            });
            navigate(`/review/${result.submission_id}`);
        } catch (error) {
            const detail = error.response?.data?.detail || error.message;
            alert(`Submission failed: ${detail}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            setPdfFile(file);
        } else if (file) {
            alert('Please select a PDF file only.');
            e.target.value = '';
        }
    };

    const handleReset = () => {
        setFormData({
            task_title: '',
            task_description: '',
            submitted_by: 'Ishan Shirode',
            github_repo_link: '',
            module_id: 'task-review-agent',
            schema_version: 'v1.0'
        });
        setPdfFile(null);
        setValidationErrors({});
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 fade-in">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1a243a] pb-6">
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => navigate('/')} 
                        className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 hover:text-white rounded-xl border border-[#1a243a] transition-all"
                    >
                        <ArrowLeft size={18} />
                    </button>
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Submit New Task</h1>
                        <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">Ingress queue submission module</p>
                    </div>
                </div>
                <button 
                    onClick={handleReset} 
                    className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 hover:text-white rounded-xl border border-[#1a243a] transition-all"
                    title="Reset Form"
                >
                    <RefreshCw size={16} />
                </button>
            </div>

            <div className="flex justify-center">
                <ConnectionStatus />
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 md:p-8 shadow-xl space-y-6">
                <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2">
                    Task Information
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Task Title */}
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-slate-400 uppercase">Task Title *</label>
                        <input 
                            type="text" 
                            name="task_title"
                            value={formData.task_title}
                            onChange={handleChange}
                            required
                            placeholder="e.g. Parikshak Completion, Integration and Handover Task"
                            className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>

                    {/* Candidate Name */}
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-slate-400 uppercase">Candidate Name *</label>
                        <input 
                            type="text" 
                            name="submitted_by"
                            value={formData.submitted_by}
                            onChange={handleChange}
                            required
                            placeholder="Enter candidate name"
                            className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none focus:border-blue-500"
                        />
                    </div>
                </div>

                {/* Task Description */}
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase">Task Description *</label>
                    <textarea 
                        name="task_description"
                        value={formData.task_description}
                        onChange={handleChange}
                        required
                        rows={4}
                        placeholder="Niyantran: Automatic live task assignment verification. Pravah: Replay continuity verification."
                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none focus:border-blue-500"
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* GitHub Repo URL */}
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-slate-400 uppercase">GitHub Repository URL *</label>
                        <input 
                            type="url" 
                            name="github_repo_link"
                            value={formData.github_repo_link}
                            onChange={handleChange}
                            required
                            placeholder="e.g. https://github.com/blackholeinfiverse78-rgb/Parikshak-system"
                            className={`w-full bg-[#131f37] border rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none focus:border-blue-500 ${
                                validationErrors.github_repo_link ? 'border-rose-500' : 'border-[#1a243a]'
                            }`}
                        />
                        {validationErrors.github_repo_link && (
                            <p className="text-[10px] text-rose-500 font-bold mt-1 flex items-center gap-1">
                                <AlertTriangle size={12} /> {validationErrors.github_repo_link}
                            </p>
                        )}
                    </div>

                    {/* Module Dropdown */}
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-black text-slate-400 uppercase">Module *</label>
                        <select 
                            name="module_id"
                            value={formData.module_id}
                            onChange={handleModuleChange}
                            className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                        >
                            {availableModules.map(m => (
                                <option key={m.id} value={m.id}>{m.name}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* PDF File Upload */}
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase">Attach Verification PDF (Optional)</label>
                    <div className="border border-dashed border-[#1a243a] bg-[#131f37]/50 rounded-xl p-6 text-center hover:bg-[#131f37] transition-all">
                        <input 
                            type="file" 
                            id="pdf_file" 
                            accept=".pdf"
                            onChange={handleFileChange}
                            className="hidden" 
                        />
                        <label htmlFor="pdf_file" className="cursor-pointer flex flex-col items-center gap-2">
                            <Upload className="text-slate-400" size={24} />
                            <span className="text-xs font-bold text-slate-300">
                                {pdfFile ? pdfFile.name : 'Click to upload or drag & drop PDF'}
                            </span>
                            <span className="text-[9px] text-slate-500 font-semibold">Only PDF files up to 10MB accepted</span>
                        </label>
                        {pdfFile && (
                            <button 
                                type="button" 
                                onClick={() => setPdfFile(null)} 
                                className="mt-3 px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-lg text-[9px] font-black uppercase flex items-center gap-1 mx-auto"
                            >
                                <X size={10} /> Remove PDF
                            </button>
                        )}
                    </div>
                </div>

                {/* Submit button */}
                <button 
                    type="submit" 
                    disabled={isSubmitting}
                    className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black text-xs uppercase tracking-wide rounded-xl shadow-lg shadow-blue-500/15 hover:scale-[1.005] active:scale-[0.995] transition-all flex items-center justify-center gap-2"
                >
                    <Send size={14} /> {isSubmitting ? 'Evaluating & Submitting...' : 'Submit Task'}
                </button>

            </form>
        </div>
    );
};

export default SubmitTask;