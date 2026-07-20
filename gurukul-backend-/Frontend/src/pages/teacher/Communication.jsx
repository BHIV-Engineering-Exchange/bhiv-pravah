import React, { useState, useEffect } from 'react';
import { FaComments, FaPaperPlane, FaUser, FaEnvelope } from 'react-icons/fa';
import { apiGet, apiPost, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const Communication = () => {
    const { alert } = useModal();
    const [messages, setMessages] = useState([]);
    const [students, setStudents] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStudents();
        fetchMessages();
    }, []);

    const fetchStudents = async () => {
        try {
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/students').catch(() => []);
            setStudents(data || []);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch students' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        }
    };

    const fetchMessages = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/messages').catch(() => []);
            setMessages(data || []);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch messages' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !selectedStudent) return;

        try {
            // TODO: Replace with actual endpoint
            await apiPost('/api/v1/ems/teacher/messages', {
                studentId: selectedStudent.id,
                message: newMessage
            });
            await alert('Message sent successfully!', 'Success');
            setNewMessage('');
            fetchMessages();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'send message' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading messages...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaComments className="text-orange-400" />
                    Communication
                </h3>
                <p className="text-gray-400 text-sm mt-1">Send messages and announcements to students and parents</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Students List */}
                <div className="lg:col-span-1 glass-panel p-4 rounded-2xl border border-white/10">
                    <h4 className="text-lg font-semibold text-white mb-4">Students</h4>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {students.map((student) => (
                            <button
                                key={student.id}
                                onClick={() => setSelectedStudent(student)}
                                className={`w-full text-left p-3 rounded-lg transition-colors ${
                                    selectedStudent?.id === student.id
                                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white'
                                        : 'bg-white/5 text-gray-300 hover:bg-white/10'
                                }`}
                            >
                                <div className="flex items-center gap-2">
                                    <FaUser />
                                    <span className="font-medium">{student.full_name || student.email}</span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Messages */}
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-white/10 flex flex-col">
                    {selectedStudent ? (
                        <>
                            <div className="mb-4 pb-4 border-b border-white/10">
                                <h4 className="text-lg font-semibold text-white">
                                    {selectedStudent.full_name || selectedStudent.email}
                                </h4>
                                <p className="text-gray-400 text-sm">{selectedStudent.email}</p>
                            </div>

                            {/* Messages List */}
                            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                                {messages
                                    .filter(msg => msg.studentId === selectedStudent.id)
                                    .map((message) => (
                                        <div
                                            key={message.id}
                                            className={`p-3 rounded-lg ${
                                                message.sender === 'teacher'
                                                    ? 'bg-orange-500/20 ml-auto max-w-[80%]'
                                                    : 'bg-white/5 mr-auto max-w-[80%]'
                                            }`}
                                        >
                                            <p className="text-white text-sm">{message.content}</p>
                                            <p className="text-gray-400 text-xs mt-1">
                                                {new Date(message.createdAt).toLocaleString()}
                                            </p>
                                        </div>
                                    ))}
                            </div>

                            {/* Send Message Form */}
                            <form onSubmit={handleSendMessage} className="flex gap-2">
                                <input
                                    type="text"
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    placeholder="Type your message..."
                                    className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                />
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all"
                                >
                                    <FaPaperPlane />
                                </button>
                            </form>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-400">
                            <div className="text-center">
                                <FaEnvelope className="mx-auto text-4xl mb-4 opacity-50" />
                                <p>Select a student to start messaging</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Communication;

