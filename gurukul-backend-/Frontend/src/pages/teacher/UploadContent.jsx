import React, { useState } from 'react';
import { FaUpload, FaFileAlt, FaVideo, FaImage, FaTimes, FaCheck } from 'react-icons/fa';
import { apiPost, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const UploadContent = () => {
    const { alert, confirm } = useModal();
    const [uploading, setUploading] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        subject: '',
        file: null,
        fileType: 'document'
    });

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            let fileType = 'document';
            if (file.type.startsWith('video/')) fileType = 'video';
            else if (file.type.startsWith('image/')) fileType = 'image';
            
            setFormData({ ...formData, file, fileType });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.title || !formData.file) {
            await alert('Please fill in all required fields', 'Missing Information');
            return;
        }

        const result = await confirm(
            `Upload "${formData.title}" to ${formData.subject || 'all subjects'}?`,
            'Confirm Upload'
        );
        if (!result) return;

        try {
            setUploading(true);
            const uploadFormData = new FormData();
            uploadFormData.append('title', formData.title);
            uploadFormData.append('description', formData.description);
            uploadFormData.append('subject', formData.subject);
            uploadFormData.append('file', formData.file);
            uploadFormData.append('fileType', formData.fileType);

            // TODO: Replace with actual endpoint
            await apiPost('/api/v1/ems/teacher/content/upload', uploadFormData);
            await alert('Content uploaded successfully!', 'Success');
            
            // Reset form
            setFormData({
                title: '',
                description: '',
                subject: '',
                file: null,
                fileType: 'document'
            });
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'upload content' });
            await alert(errorInfo.message, errorInfo.title);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaUpload className="text-orange-400" />
                    Upload Content
                </h3>
                <p className="text-gray-400 text-sm mt-1">Upload lectures, notes, or materials for your students</p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Title <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                            placeholder="e.g., Introduction to Calculus"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Description
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                            rows="3"
                            placeholder="Brief description of the content..."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Subject
                        </label>
                        <select
                            value={formData.subject}
                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-orange-500"
                        >
                            <option value="">All Subjects</option>
                            <option value="Mathematics">Mathematics</option>
                            <option value="Physics">Physics</option>
                            <option value="Chemistry">Chemistry</option>
                            <option value="Biology">Biology</option>
                            <option value="Computer Science">Computer Science</option>
                            <option value="History">History</option>
                            <option value="Geography">Geography</option>
                            <option value="Literature">Literature</option>
                            <option value="Economics">Economics</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            File <span className="text-red-400">*</span>
                        </label>
                        <div className="border-2 border-dashed border-white/20 rounded-lg p-6 text-center hover:border-orange-500 transition-colors">
                            <input
                                type="file"
                                onChange={handleFileChange}
                                className="hidden"
                                id="file-upload"
                                accept=".pdf,.doc,.docx,.ppt,.pptx,.mp4,.mov,.jpg,.jpeg,.png"
                            />
                            <label htmlFor="file-upload" className="cursor-pointer">
                                {formData.file ? (
                                    <div className="flex items-center justify-center gap-2 text-green-400">
                                        <FaCheck />
                                        <span>{formData.file.name}</span>
                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setFormData({ ...formData, file: null });
                                            }}
                                            className="ml-2 text-red-400 hover:text-red-300"
                                        >
                                            <FaTimes />
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        <FaUpload className="mx-auto text-3xl text-gray-400" />
                                        <p className="text-gray-400 text-sm">Click to upload or drag and drop</p>
                                        <p className="text-gray-500 text-xs">PDF, DOC, PPT, Video, Images</p>
                                    </div>
                                )}
                            </label>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={uploading || !formData.title || !formData.file}
                        className="w-full py-3 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {uploading ? (
                            <>
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                Uploading...
                            </>
                        ) : (
                            <>
                                <FaUpload />
                                Upload Content
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default UploadContent;

