import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { FaRobot, FaCog, FaCommentAlt, FaBook, FaDollarSign, FaHeartbeat, FaCircle, FaPaperPlane, FaSpinner, FaCheckCircle, FaTrashAlt, FaGlobeAmericas, FaUser, FaChevronDown } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';
import { containsProfanity } from '../utils/profanityDetector';
import { sendLifeEvent } from '../utils/karmaTrackerClient';
import { apiPost } from '../utils/apiClient';
import API_BASE_URL from '../config';

const AGENTS = [
    {
        id: 1,
        name: "EduMentor",
        category: "education",
        description: "Specialized in educational content and academic guidance",
        confidence: 85,
        icon: FaBook,
        color: "text-green-300",
        barColor: "bg-green-500",
        tagBg: "bg-green-500/30",
        tagText: "text-green-100"
    },
    {
        id: 2,
        name: "FinancialCrew",
        category: "financial",
        description: "Expert in financial planning and investment strategies",
        confidence: 78,
        icon: FaDollarSign,
        color: "text-blue-300",
        barColor: "bg-blue-500",
        tagBg: "bg-blue-500/30",
        tagText: "text-blue-100"
    },
    {
        id: 3,
        name: "WellnessBot",
        category: "wellness",
        description: "Focused on mental and physical wellbeing advice",
        confidence: 92,
        icon: FaHeartbeat,
        color: "text-orange-300",
        barColor: "bg-orange-500",
        tagBg: "bg-orange-500/30",
        tagText: "text-orange-100"
    }
];

const AgentSimulator = () => {
    const { agentName } = useParams();
    const navigate = useNavigate();
    const { alert, confirm, error } = useModal();
    const { user } = useAuth();
    // --- State ---
    const [selectedAgent, setSelectedAgent] = useState(() => {
        // Priority to URL param
        if (agentName) {
            const found = AGENTS.find(a => a.name.toLowerCase() === agentName.toLowerCase());
            if (found) return found;
        }
        const saved = localStorage.getItem('agent_sim_selectedAgent');
        if (!saved) return AGENTS[0];
        try {
            const parsed = JSON.parse(saved);
            return AGENTS.find(a => a.id === parsed.id) || AGENTS[0];
        } catch (e) {
            return AGENTS[0];
        }
    });

    // Sync URL with selection changes
    useEffect(() => {
        if (selectedAgent && selectedAgent.name !== agentName) {
            // Update URL without full reload if possible, or just accept the discrepancy until user shares link
            // For now, let's just respect URL if present on mount. 
            // If user clicks sidebar, they go to /agent-simulator?
            // If user selects in UI, we might want to update URL?
            // Let's just listen to URL changes for now.
        }
    }, [selectedAgent]);

    // Listen to URL param changes
    useEffect(() => {
        if (agentName) {
            const found = AGENTS.find(a => a.name.toLowerCase() === agentName.toLowerCase());
            if (found && found.id !== selectedAgent?.id) {
                setSelectedAgent(found);
            }
        }
    }, [agentName]);

    // EduMentor Specific State
    const [config, setConfig] = useState(() => {
        const saved = localStorage.getItem('agent_sim_edumentor_config');
        return saved ? JSON.parse(saved) : {
            subject: '',
            topic: '',
            include_wikipedia: false,
            use_knowledge_store: false,
            use_orchestration: false
        };
    });
    const [lastGenConfig, setLastGenConfig] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedLesson, setGeneratedLesson] = useState(null);

    // FinancialCrew Specific State
    const [financialConfig, setFinancialConfig] = useState(() => {
        const saved = localStorage.getItem('agent_sim_financial_config');
        return saved ? JSON.parse(saved) : {
            name: '',
            monthly_income: '',
            monthly_expenses: '',
            expense_categories: [],
            financial_goal: '',
            financial_type: 'Moderate',
            risk_level: 'Moderate'
        };
    });
    const [lastFinancialConfig, setLastFinancialConfig] = useState(null);
    const [isGeneratingAdvice, setIsGeneratingAdvice] = useState(false);
    const [generatedAdvice, setGeneratedAdvice] = useState(null);
    const [isFinancialTypeOpen, setIsFinancialTypeOpen] = useState(false);
    const [isRiskLevelOpen, setIsRiskLevelOpen] = useState(false);

    // WellnessBot State
    const [wellnessConfig, setWellnessConfig] = useState(() => {
        const saved = localStorage.getItem('agent_sim_wellness_config');
        return saved ? JSON.parse(saved) : {
            emotional_wellness_score: 5,
            financial_wellness_score: 5,
            current_mood_score: 5,
            stress_level: 5,
            concerns: ''
        };
    });
    const [lastWellnessConfig, setLastWellnessConfig] = useState(null);
    const [isGeneratingSupport, setIsGeneratingSupport] = useState(false);
    const [generatedSupport, setGeneratedSupport] = useState(null);

    // Shared State
    const [isChatEnabled, setIsChatEnabled] = useState(() => {
        return localStorage.getItem('agent_sim_isChatEnabled') === 'true';
    });

    // Chat State
    const [chatHistory, setChatHistory] = useState([]);
    const [message, setMessage] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [conversationId, setConversationId] = useState(() => localStorage.getItem('agent_sim_conversationId') || null);
    const chatEndRef = useRef(null);

    // Sync all agent-specific data when switching agents
    useEffect(() => {
        if (!selectedAgent) return;

        const agentName = selectedAgent.name;

        // Sync chat history
        const chatKey = `agent_sim_chatHistory_${agentName}`;
        const savedChat = localStorage.getItem(chatKey);
        setChatHistory(savedChat ? JSON.parse(savedChat) : []);

        // Sync conversationId
        const convKey = `agent_sim_conversationId_${agentName}`;
        setConversationId(localStorage.getItem(convKey) || null);

        // Clear other agents' generated content first
        if (agentName !== 'EduMentor') {
            setGeneratedLesson(null);
            setLastGenConfig(null);
        }
        if (agentName !== 'FinancialCrew') {
            setGeneratedAdvice(null);
            setLastFinancialConfig(null);
        }
        if (agentName !== 'WellnessBot') {
            setGeneratedSupport(null);
            setLastWellnessConfig(null);
        }

        // Load agent-specific generated content
        if (agentName === 'EduMentor') {
            const lessonKey = `agent_sim_edumentor_lesson_${agentName}`;
            const savedLesson = localStorage.getItem(lessonKey);
            setGeneratedLesson(savedLesson ? JSON.parse(savedLesson) : null);

            const lastConfigKey = `agent_sim_edumentor_lastGenConfig_${agentName}`;
            const savedLastConfig = localStorage.getItem(lastConfigKey);
            setLastGenConfig(savedLastConfig ? JSON.parse(savedLastConfig) : null);

            setIsChatEnabled(!!savedLesson);
        } else if (agentName === 'FinancialCrew') {
            const adviceKey = `agent_sim_financial_advice_${agentName}`;
            const savedAdvice = localStorage.getItem(adviceKey);
            setGeneratedAdvice(savedAdvice ? JSON.parse(savedAdvice) : null);

            const lastConfigKey = `agent_sim_financial_lastGenConfig_${agentName}`;
            const savedLastConfig = localStorage.getItem(lastConfigKey);
            setLastFinancialConfig(savedLastConfig ? JSON.parse(savedLastConfig) : null);

            setIsChatEnabled(!!savedAdvice);
        } else if (agentName === 'WellnessBot') {
            const supportKey = `agent_sim_wellness_support_${agentName}`;
            const savedSupport = localStorage.getItem(supportKey);
            setGeneratedSupport(savedSupport ? JSON.parse(savedSupport) : null);

            const lastConfigKey = `agent_sim_wellness_lastGenConfig_${agentName}`;
            const savedLastConfig = localStorage.getItem(lastConfigKey);
            setLastWellnessConfig(savedLastConfig ? JSON.parse(savedLastConfig) : null);

            setIsChatEnabled(!!savedSupport);
        } else {
            // For non-config agents, chat is always enabled
            setIsChatEnabled(true);
        }
    }, [selectedAgent]);

    // Save chat history per agent whenever it changes
    useEffect(() => {
        if (!selectedAgent) return;
        const key = `agent_sim_chatHistory_${selectedAgent.name}`;
        localStorage.setItem(key, JSON.stringify(chatHistory));

        const convKey = `agent_sim_conversationId_${selectedAgent.name}`;
        if (conversationId) localStorage.setItem(convKey, conversationId);
        else localStorage.removeItem(convKey);
    }, [chatHistory, conversationId, selectedAgent]);

    const handleResetAgent = async (e) => {
        e?.stopPropagation();
        e?.preventDefault();

        if (!selectedAgent) return;
        const result = await confirm(`Reset ${selectedAgent.name} session? This will clear all chat history and generated content for this agent.`, 'Reset Session');
        if (!result) return;

        const name = selectedAgent.name;

        // Clear state
        if (name === 'EduMentor') {
            setGeneratedLesson(null);
            setLastGenConfig(null);
            setConfig({ subject: '', topic: '', include_wikipedia: false, use_knowledge_store: false, use_orchestration: false });
            localStorage.removeItem(`agent_sim_edumentor_lesson_${name}`);
            localStorage.removeItem(`agent_sim_edumentor_lastGenConfig_${name}`);
        } else if (name === 'FinancialCrew') {
            setGeneratedAdvice(null);
            setLastFinancialConfig(null);
            setFinancialConfig({
                name: '',
                monthly_income: '',
                monthly_expenses: '',
                expense_categories: [],
                financial_goal: '',
                financial_type: 'Moderate',
                risk_level: 'Moderate'
            });
            localStorage.removeItem(`agent_sim_financial_advice_${name}`);
            localStorage.removeItem(`agent_sim_financial_lastGenConfig_${name}`);
        } else if (name === 'WellnessBot') {
            setGeneratedSupport(null);
            setLastWellnessConfig(null);
            setWellnessConfig({
                emotional_wellness_score: 5,
                financial_wellness_score: 5,
                current_mood_score: 5,
                stress_level: 5,
                concerns: ''
            });
            localStorage.removeItem(`agent_sim_wellness_support_${name}`);
            localStorage.removeItem(`agent_sim_wellness_lastGenConfig_${name}`);
        }

        setChatHistory([]);
        setConversationId(null);
        setIsChatEnabled(false);

        // Clear all agent-specific storage
        const keys = [
            `agent_sim_chatHistory_${name}`,
            `agent_sim_conversationId_${name}`,
            `agent_sim_isEnabled_${name}`
        ];
        keys.forEach(k => localStorage.removeItem(k));
    };

    // --- Persistence Effects ---
    useEffect(() => {
        if (selectedAgent) localStorage.setItem('agent_sim_selectedAgent', JSON.stringify(selectedAgent));
    }, [selectedAgent]);

    useEffect(() => {
        localStorage.setItem('agent_sim_edumentor_config', JSON.stringify(config));
    }, [config]);

    // Persist generated content per-agent
    useEffect(() => {
        if (!selectedAgent) return;
        if (selectedAgent.name === 'EduMentor') {
            if (generatedLesson) {
                localStorage.setItem(`agent_sim_edumentor_lesson_${selectedAgent.name}`, JSON.stringify(generatedLesson));
            } else {
                localStorage.removeItem(`agent_sim_edumentor_lesson_${selectedAgent.name}`);
            }
        }
    }, [generatedLesson, selectedAgent]);

    useEffect(() => {
        if (!selectedAgent) return;
        if (selectedAgent.name === 'EduMentor') {
            if (lastGenConfig) {
                localStorage.setItem(`agent_sim_edumentor_lastGenConfig_${selectedAgent.name}`, JSON.stringify(lastGenConfig));
            } else {
                localStorage.removeItem(`agent_sim_edumentor_lastGenConfig_${selectedAgent.name}`);
            }
        }
    }, [lastGenConfig, selectedAgent]);

    useEffect(() => {
        localStorage.setItem('agent_sim_financial_config', JSON.stringify(financialConfig));
    }, [financialConfig]);

    useEffect(() => {
        if (!selectedAgent) return;
        if (selectedAgent.name === 'FinancialCrew') {
            if (generatedAdvice) {
                localStorage.setItem(`agent_sim_financial_advice_${selectedAgent.name}`, JSON.stringify(generatedAdvice));
            } else {
                localStorage.removeItem(`agent_sim_financial_advice_${selectedAgent.name}`);
            }
        }
    }, [generatedAdvice, selectedAgent]);

    useEffect(() => {
        if (!selectedAgent) return;
        if (selectedAgent.name === 'FinancialCrew') {
            if (lastFinancialConfig) {
                localStorage.setItem(`agent_sim_financial_lastGenConfig_${selectedAgent.name}`, JSON.stringify(lastFinancialConfig));
            } else {
                localStorage.removeItem(`agent_sim_financial_lastGenConfig_${selectedAgent.name}`);
            }
        }
    }, [lastFinancialConfig, selectedAgent]);

    useEffect(() => {
        localStorage.setItem('agent_sim_wellness_config', JSON.stringify(wellnessConfig));
    }, [wellnessConfig]);

    useEffect(() => {
        if (!selectedAgent) return;
        if (selectedAgent.name === 'WellnessBot') {
            if (generatedSupport) {
                localStorage.setItem(`agent_sim_wellness_support_${selectedAgent.name}`, JSON.stringify(generatedSupport));
            } else {
                localStorage.removeItem(`agent_sim_wellness_support_${selectedAgent.name}`);
            }
        }
    }, [generatedSupport, selectedAgent]);

    useEffect(() => {
        if (!selectedAgent) return;
        if (selectedAgent.name === 'WellnessBot') {
            if (lastWellnessConfig) {
                localStorage.setItem(`agent_sim_wellness_lastGenConfig_${selectedAgent.name}`, JSON.stringify(lastWellnessConfig));
            } else {
                localStorage.removeItem(`agent_sim_wellness_lastGenConfig_${selectedAgent.name}`);
            }
        }
    }, [lastWellnessConfig, selectedAgent]);

    // --- Effects ---
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory, generatedLesson]);

    // Enable chat for non-config agents if no history
    useEffect(() => {
        if (selectedAgent && selectedAgent.name !== 'EduMentor' && selectedAgent.name !== 'FinancialCrew' && selectedAgent.name !== 'WellnessBot') {
            setIsChatEnabled(true);
        }
    }, [selectedAgent]);


    const agents = AGENTS;


    // --- Handlers ---

    const handleGenerate = async () => {
        if (!config.subject || !config.topic) {
            alert("Subject and Topic are required!", "Validation Error");
            return;
        }

        setIsGenerating(true);
        setGeneratedLesson(null);
        setChatHistory([]); // Clear chat immediately for new generation
        setConversationId(null); // Reset conversation for new lesson
        setIsChatEnabled(false); // Lock chat during generation

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/agent/edumentor/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (!response.ok) throw new Error('Generation failed');

            const data = await response.json();
            const lessonContent = data.lesson_content;
            setGeneratedLesson(lessonContent);
            setLastGenConfig({ ...config }); // Store the config we just used

            // Initialize conversation with backend by sending the lesson context
            // This ensures the AI remembers the lesson throughout the conversation
            try {
                const contextMessage = `I have generated a comprehensive lesson on ${config.subject} - ${config.topic}. Here is the lesson content:\n\n${lessonContent}\n\nI'm ready to answer any questions about this lesson.`;

                const chatData = await apiPost('/api/v1/chat', {
                    message: contextMessage,
                    conversation_id: null,
                    provider: 'auto',
                    use_rag: true
                });

                // Store the conversation ID
                if (chatData.conversation_id) {
                    setConversationId(chatData.conversation_id);
                }

                // Show user-friendly message in chat
                setChatHistory([{
                    role: 'assistant',
                    content: `✅ I have generated a lesson on **${config.topic}**. Using this as context, what questions do you have?`
                }]);

                setIsChatEnabled(true);
            } catch (chatError) {
                console.error('Failed to initialize conversation:', chatError);
                // Fallback: still enable chat even if context initialization fails
                setChatHistory([{
                    role: 'assistant',
                    content: `✅ I have generated a lesson on **${config.topic}**. Using this as context, what questions do you have?`
                }]);
                setIsChatEnabled(true);
            }

        } catch (error) {
            console.error(error);
            error("Failed to generate lesson. Please try again.", "Generation Error");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSendMessage = async () => {
        if (!message.trim() || !isChatEnabled) return;

        // Check for profanity
        if (containsProfanity(message)) {
            // Karma: negative event for cursing with any agent
            if (user?.id) {
                sendLifeEvent({
                    userId: user.id,
                    action: 'cheat',
                    note: `Inappropriate language detected in Agent Simulator (${selectedAgent?.name || 'Unknown agent'})`,
                    context: `source=agent-simulator;agent=${selectedAgent?.name || 'unknown'}`
                });
            }
            alert('Please keep the conversation respectful.', 'Warning');
            return;
        }

        const userMsg = { role: 'user', content: message };
        setChatHistory(prev => [...prev, userMsg]);
        setMessage('');
        setIsChatLoading(true);

        // Karma: positive event for using an agent (any of the three)
        if (user?.id && selectedAgent?.name) {
            sendLifeEvent({
                userId: user.id,
                action: 'completing_lessons',
                note: `Interacted with ${selectedAgent.name} in Agent Simulator`,
                context: `source=agent-simulator;agent=${selectedAgent.name}`
            });
        }

        try {
            const data = await apiPost('/api/v1/chat', {
                message: userMsg.content,
                conversation_id: conversationId,
                provider: 'auto',
                use_rag: true
            });

            // Store conversation_id for subsequent messages
            if (data.conversation_id) {
                setConversationId(data.conversation_id);
            }

            setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);

        } catch (error) {
            setChatHistory(prev => [...prev, { role: 'assistant', content: "⚠️ Connection error. Please try again." }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    // FinancialCrew Handlers
    const addExpense = () => {
        setFinancialConfig({
            ...financialConfig,
            expense_categories: [
                ...financialConfig.expense_categories,
                { name: '', amount: '' }
            ]
        });
    };

    const removeExpense = (index) => {
        const updated = financialConfig.expense_categories.filter((_, i) => i !== index);
        setFinancialConfig({ ...financialConfig, expense_categories: updated });
    };

    const updateExpense = (index, field, value) => {
        const updated = [...financialConfig.expense_categories];
        updated[index][field] = value;
        setFinancialConfig({ ...financialConfig, expense_categories: updated });
    };

    const handleGenerateAdvice = async () => {
        if (!financialConfig.name || !financialConfig.monthly_income || parseFloat(financialConfig.monthly_income) <= 0) {
            alert("Name and valid monthly income are required!", "Validation Error");
            return;
        }

        setIsGeneratingAdvice(true);
        setGeneratedAdvice(null);
        setChatHistory([]);
        setConversationId(null);
        setIsChatEnabled(false);

        try {
            // Calculate total expenses from categories
            const totalExpenses = financialConfig.expense_categories.reduce((sum, exp) =>
                sum + (parseFloat(exp.amount) || 0), 0
            );

            const response = await fetch(`${API_BASE_URL}/api/v1/agent/financial/advice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: financialConfig.name,
                    monthly_income: parseFloat(financialConfig.monthly_income),
                    monthly_expenses: totalExpenses,
                    expense_categories: financialConfig.expense_categories.map(exp => ({
                        name: exp.name,
                        amount: parseFloat(exp.amount) || 0
                    })),
                    financial_goal: financialConfig.financial_goal,
                    financial_type: financialConfig.financial_type,
                    risk_level: financialConfig.risk_level
                })
            });

            if (!response.ok) throw new Error('Generation failed');

            const data = await response.json();
            setGeneratedAdvice(data);
            setLastFinancialConfig({ ...financialConfig });

            // Initialize conversation with backend
            try {
                const contextMessage = `I have analyzed the financial profile for ${financialConfig.name}. Monthly Income: ₹${financialConfig.monthly_income}, Monthly Savings: ₹${data.monthly_savings}, Financial Goal: ${financialConfig.financial_goal}. Here is my financial advice:\n\n${data.financial_advice}\n\nI'm ready to answer questions about this advice.`;

                const chatData = await apiPost('/api/v1/chat', {
                    message: contextMessage,
                    conversation_id: null,
                    provider: 'auto',
                    use_rag: true
                });

                if (chatData.conversation_id) {
                    setConversationId(chatData.conversation_id);
                }

                setChatHistory([{
                    role: 'assistant',
                    content: `✅ I've analyzed your financial profile for **${financialConfig.name}**. What questions do you have about the advice?`
                }]);

                setIsChatEnabled(true);
            } catch (chatError) {
                console.error('Failed to initialize conversation:', chatError);
                setChatHistory([{
                    role: 'assistant',
                    content: `✅ I've analyzed your financial profile for **${financialConfig.name}**. What questions do you have about the advice?`
                }]);
                setIsChatEnabled(true);
            }

        } catch (error) {
            console.error(error);
            error("Failed to generate financial advice. Please try again.", "Generation Error");
        } finally {
            setIsGeneratingAdvice(false);
        }
    };

    const handleGenerateSupport = async () => {
        setIsGeneratingSupport(true);
        setGeneratedSupport(null);
        setChatHistory([]);
        setConversationId(null);
        setIsChatEnabled(false);

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/agent/wellness/support`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(wellnessConfig)
            });

            if (!response.ok) throw new Error('Generation failed');

            const data = await response.json();
            setGeneratedSupport(data);
            setLastWellnessConfig({ ...wellnessConfig });

            // Initialize conversation with backend
            try {
                const contextMessage = `I have prepared personalized wellness support based on these scores: Emotional Wellness: ${wellnessConfig.emotional_wellness_score}/10, Financial Wellness: ${wellnessConfig.financial_wellness_score}/10, Current Mood: ${wellnessConfig.current_mood_score}/10, Stress Level: ${wellnessConfig.stress_level}/10. Overall Assessment:\n\n${data.overall_assessment}\n\nI'm here to support you with any questions.`;

                const chatData = await apiPost('/api/v1/chat', {
                    message: contextMessage,
                    conversation_id: null,
                    provider: 'auto',
                    use_rag: true
                });

                if (chatData.conversation_id) {
                    setConversationId(chatData.conversation_id);
                }

                setChatHistory([{
                    role: 'assistant',
                    content: `✨ I've prepared personalized wellness support for you. How can I help you further?`
                }]);

                setIsChatEnabled(true);
            } catch (chatError) {
                console.error('Failed to initialize conversation:', chatError);
                setChatHistory([{
                    role: 'assistant',
                    content: `✨ I've prepared personalized wellness support for you. How can I help you further?`
                }]);
                setIsChatEnabled(true);
            }

        } catch (error) {
            console.error(error);
            error("Failed to generate wellness support. Please try again.", "Generation Error");
        } finally {
            setIsGeneratingSupport(false);
        }
    };


    // --- Renderers ---

    const renderConfigPanel = () => {
        if (!selectedAgent) {
            return (
                <div className="flex-grow flex items-center justify-center text-center">
                    <p className="text-gray-400 text-sm px-4">Select an agent to configure.</p>
                </div>
            );
        }

        if (selectedAgent.name === 'EduMentor') {
            // Check if current inputs match what was last generated
            const isConfigChanged = !lastGenConfig ||
                config.subject !== lastGenConfig.subject ||
                config.topic !== lastGenConfig.topic;

            const isGenerateDisabled = isGenerating || !config.subject || !config.topic || (!isConfigChanged && generatedLesson);
            const isInputDisabled = isGenerating; // Only lock inputs during generation
            const isToggleDisabled = isGenerating || (!isConfigChanged && generatedLesson); // Lock toggles during generation AND after

            return (
                <div className="space-y-4 animate-fade-in-up">
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Subject</label>
                        <input
                            type="text"
                            disabled={isInputDisabled}
                            className={`w-full bg-white/5 border border-white/10 rounded-lg p-2 text-white text-sm mt-1 outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-orange-500'}`}
                            placeholder="e.g. Physics"
                            value={config.subject}
                            onChange={e => setConfig({ ...config, subject: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Topic</label>
                        <input
                            type="text"
                            disabled={isInputDisabled}
                            className={`w-full bg-white/5 border border-white/10 rounded-lg p-2 text-white text-sm mt-1 outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-orange-500'}`}
                            placeholder="e.g. Newton's Laws"
                            value={config.topic}
                            onChange={e => setConfig({ ...config, topic: e.target.value })}
                        />
                    </div>

                    <div className="pt-2 space-y-3">
                        {/* Toggle: Knowledge Store */}
                        <div
                            onClick={() => !isToggleDisabled && setConfig({ ...config, use_knowledge_store: !config.use_knowledge_store })}
                            className={`p-3 rounded-xl border transition-all flex items-center justify-between group 
                                ${isToggleDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                                ${config.use_knowledge_store ? 'bg-orange-500/10 border-orange-500/50 shadow-[0_0_10px_rgba(249,115,22,0.1)]' : 'bg-white/5 border-white/10 hover:bg-white/10'}
                            `}
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${config.use_knowledge_store ? 'bg-orange-500 text-white' : 'bg-white/10 text-gray-400'}`}>
                                    <FaBook className="text-sm" />
                                </div>
                                <div>
                                    <h4 className={`text-sm font-bold ${config.use_knowledge_store ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>Knowledge Store</h4>
                                    <p className="text-[10px] text-gray-500">Use recalled memories (RAG)</p>
                                </div>
                            </div>
                            <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${config.use_knowledge_store ? 'border-orange-500 bg-orange-500' : 'border-gray-600'}`}>
                                {config.use_knowledge_store && <FaCheckCircle className="text-[10px] text-white" />}
                            </div>
                        </div>

                        {/* Toggle: Wikipedia */}
                        <div
                            onClick={() => !isToggleDisabled && setConfig({ ...config, include_wikipedia: !config.include_wikipedia })}
                            className={`p-3 rounded-xl border transition-all flex items-center justify-between group 
                                ${isToggleDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                                ${config.include_wikipedia ? 'bg-blue-500/10 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.1)]' : 'bg-white/5 border-white/10 hover:bg-white/10'}
                            `}
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${config.include_wikipedia ? 'bg-blue-500 text-white' : 'bg-white/10 text-gray-400'}`}>
                                    <FaGlobeAmericas className="text-sm" />
                                </div>
                                <div>
                                    <h4 className={`text-sm font-bold ${config.include_wikipedia ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>Wikipedia Search</h4>
                                    <p className="text-[10px] text-gray-500">Fetch external sources</p>
                                </div>
                            </div>
                            <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${config.include_wikipedia ? 'border-blue-500 bg-blue-500' : 'border-gray-600'}`}>
                                {config.include_wikipedia && <FaCheckCircle className="text-[10px] text-white" />}
                            </div>
                        </div>

                        {/* Toggle: Orchestration */}
                        <div
                            onClick={() => !isToggleDisabled && setConfig({ ...config, use_orchestration: !config.use_orchestration })}
                            className={`p-3 rounded-xl border transition-all flex items-center justify-between group 
                                ${isToggleDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                                ${config.use_orchestration ? 'bg-purple-500/10 border-purple-500/50 shadow-[0_0_10px_rgba(168,85,247,0.1)]' : 'bg-white/5 border-white/10 hover:bg-white/10'}
                            `}
                        >
                            <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${config.use_orchestration ? 'bg-purple-500 text-white' : 'bg-white/10 text-gray-400'}`}>
                                    <FaRobot className="text-sm" />
                                </div>
                                <div>
                                    <h4 className={`text-sm font-bold ${config.use_orchestration ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>Orchestration</h4>
                                    <p className="text-[10px] text-gray-500">Multi-pass refinement</p>
                                </div>
                            </div>
                            <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${config.use_orchestration ? 'border-purple-500 bg-purple-500' : 'border-gray-600'}`}>
                                {config.use_orchestration && <FaCheckCircle className="text-[10px] text-white" />}
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isGenerateDisabled}
                        className={`w-full py-3 mt-4 rounded-xl font-bold text-sm transition-all shadow-lg flex justify-center items-center gap-2 ${isGenerateDisabled && generatedLesson ? 'bg-green-600/20 text-green-400 cursor-not-allowed border border-green-500/30' : 'bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white hover:shadow-orange-500/20'} ${!generatedLesson && isGenerateDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isGenerating ? <><FaSpinner className="animate-spin" /> Generating...</> :
                            (generatedLesson && !isConfigChanged ? <><FaCheckCircle /> Lesson Generated</> :
                                (generatedLesson ? <><FaPaperPlane /> Generate New Lesson</> : 'Generate Lesson')
                            )}
                    </button>
                    {isGenerating && <p className="text-xs text-gray-500 text-center animate-pulse">This may take a minute...</p>}
                </div>
            );
        }

        if (selectedAgent.name === 'FinancialCrew') {
            // Check if config has changed
            const isConfigChanged = !lastFinancialConfig ||
                financialConfig.name !== lastFinancialConfig.name ||
                financialConfig.monthly_income !== lastFinancialConfig.monthly_income ||
                financialConfig.financial_goal !== lastFinancialConfig.financial_goal;

            const isGenerateDisabled = isGeneratingAdvice || !financialConfig.name || !financialConfig.monthly_income || parseFloat(financialConfig.monthly_income) <= 0 || (!isConfigChanged && generatedAdvice);
            const isInputDisabled = isGeneratingAdvice;

            // Calculate total expenses
            const totalExpenses = financialConfig.expense_categories.reduce((sum, exp) => sum + (parseFloat(exp.amount) || 0), 0);

            return (
                <div className="space-y-4 animate-fade-in-up">
                    {/* Basic Info */}
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Name</label>
                        <input
                            type="text"
                            disabled={isInputDisabled}
                            className={`w-full bg-white/5 border border-white/10 rounded-lg p-2 text-white text-sm mt-1 outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-blue-500'}`}
                            placeholder="Your name"
                            value={financialConfig.name}
                            onChange={e => setFinancialConfig({ ...financialConfig, name: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Monthly Income (₹)</label>
                        <input
                            type="number"
                            disabled={isInputDisabled}
                            className={`w-full bg-white/5 border border-white/10 rounded-lg p-2 text-white text-sm mt-1 outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-blue-500'}`}
                            placeholder="e.g. 50000"
                            value={financialConfig.monthly_income}
                            onChange={e => setFinancialConfig({ ...financialConfig, monthly_income: e.target.value })}
                        />
                    </div>

                    {/* Expense Categories */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Expense Categories</label>
                            <button
                                onClick={addExpense}
                                disabled={isInputDisabled}
                                className={`text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30 transition-colors ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                + Add
                            </button>
                        </div>
                        <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                            {financialConfig.expense_categories.map((exp, index) => (
                                <div key={index} className="flex gap-2 items-center">
                                    <input
                                        type="text"
                                        disabled={isInputDisabled}
                                        className={`flex-1 bg-white/5 border border-white/10 rounded-lg p-2 text-white text-xs outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-blue-500'}`}
                                        placeholder="Category (e.g., Rent)"
                                        value={exp.name}
                                        onChange={e => updateExpense(index, 'name', e.target.value)}
                                    />
                                    <input
                                        type="number"
                                        disabled={isInputDisabled}
                                        className={`w-24 bg-white/5 border border-white/10 rounded-lg p-2 text-white text-xs outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-blue-500'}`}
                                        placeholder="Amount"
                                        value={exp.amount}
                                        onChange={e => updateExpense(index, 'amount', e.target.value)}
                                    />
                                    <button
                                        onClick={() => removeExpense(index)}
                                        disabled={isInputDisabled}
                                        className={`p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                                    >
                                        <FaTrashAlt className="text-xs" />
                                    </button>
                                </div>
                            ))}
                        </div>
                        {totalExpenses > 0 && (
                            <p className="text-xs text-gray-400 mt-2">Total Expenses: ₹{totalExpenses.toFixed(2)}</p>
                        )}
                    </div>

                    {/* Financial Profile */}
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Financial Goal</label>
                        <input
                            type="text"
                            disabled={isInputDisabled}
                            className={`w-full bg-white/5 border border-white/10 rounded-lg p-2 text-white text-sm mt-1 outline-none ${isInputDisabled ? 'opacity-50 cursor-not-allowed' : 'focus:border-blue-500'}`}
                            placeholder="e.g., Buy a house, Save for retirement"
                            value={financialConfig.financial_goal}
                            onChange={e => setFinancialConfig({ ...financialConfig, financial_goal: e.target.value })}
                        />
                    </div>

                    {/* Financial Type & Risk Level */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="relative">
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Financial Type</label>
                            <div className="relative mt-1">
                                <button
                                    onClick={() => !isInputDisabled && setIsFinancialTypeOpen(!isFinancialTypeOpen)}
                                    onBlur={() => setTimeout(() => setIsFinancialTypeOpen(false), 200)}
                                    disabled={isInputDisabled}
                                    className={`w-full p-2 rounded-lg bg-white/5 border text-left flex items-center justify-between transition-all ${isFinancialTypeOpen
                                        ? 'border-blue-500/50 ring-2 ring-blue-500/20 bg-white/10'
                                        : isInputDisabled
                                            ? 'opacity-50 cursor-not-allowed border-white/10'
                                            : 'border-white/10 hover:bg-white/10 cursor-pointer'
                                        }`}
                                >
                                    <span className="text-white text-sm">{financialConfig.financial_type}</span>
                                    <FaChevronDown className={`text-xs text-gray-400 transition-transform duration-300 ${isFinancialTypeOpen ? 'rotate-180' : ''}`} />
                                </button>
                                {isFinancialTypeOpen && (
                                    <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1c16] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                                        {['Conservative', 'Moderate', 'Aggressive'].map(type => (
                                            <div
                                                key={type}
                                                onClick={() => { setFinancialConfig({ ...financialConfig, financial_type: type }); setIsFinancialTypeOpen(false); }}
                                                className="px-5 py-3.5 text-sm text-gray-300 hover:bg-white/5 hover:text-blue-400 cursor-pointer flex justify-between items-center"
                                            >
                                                {type}
                                                {financialConfig.financial_type === type && <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)] self-center"></div>}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="relative">
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Risk Level</label>
                            <div className="relative mt-1">
                                <button
                                    onClick={() => !isInputDisabled && setIsRiskLevelOpen(!isRiskLevelOpen)}
                                    onBlur={() => setTimeout(() => setIsRiskLevelOpen(false), 200)}
                                    disabled={isInputDisabled}
                                    className={`w-full p-2 rounded-lg bg-white/5 border text-left flex items-center justify-between transition-all ${isRiskLevelOpen
                                        ? 'border-blue-500/50 ring-2 ring-blue-500/20 bg-white/10'
                                        : isInputDisabled
                                            ? 'opacity-50 cursor-not-allowed border-white/10'
                                            : 'border-white/10 hover:bg-white/10 cursor-pointer'
                                        }`}
                                >
                                    <span className="text-white text-sm">{financialConfig.risk_level}</span>
                                    <FaChevronDown className={`text-xs text-gray-400 transition-transform duration-300 ${isRiskLevelOpen ? 'rotate-180' : ''}`} />
                                </button>
                                {isRiskLevelOpen && (
                                    <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1c16] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                                        {['Low', 'Moderate', 'High'].map(level => (
                                            <div
                                                key={level}
                                                onClick={() => { setFinancialConfig({ ...financialConfig, risk_level: level }); setIsRiskLevelOpen(false); }}
                                                className="px-5 py-3.5 text-sm text-gray-300 hover:bg-white/5 hover:text-blue-400 cursor-pointer flex justify-between items-center"
                                            >
                                                {level}
                                                {financialConfig.risk_level === level && <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)] self-center"></div>}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleGenerateAdvice}
                        disabled={isGenerateDisabled}
                        className={`w-full py-3 mt-4 rounded-xl font-bold text-sm transition-all shadow-lg flex justify-center items-center gap-2 ${isGenerateDisabled && generatedAdvice ? 'bg-green-600/20 text-green-400 cursor-not-allowed border border-green-500/30' : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white hover:shadow-blue-500/20'} ${!generatedAdvice && isGenerateDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isGeneratingAdvice ? <><FaSpinner className="animate-spin" /> Generating...</> :
                            (generatedAdvice && !isConfigChanged ? <><FaCheckCircle /> Advice Generated</> :
                                (generatedAdvice ? <><FaPaperPlane /> Generate New Advice</> : 'Generate Financial Advice')
                            )}
                    </button>
                    {isGeneratingAdvice && <p className="text-xs text-gray-500 text-center animate-pulse">Analyzing your financial profile...</p>}
                </div>
            );
        }

        // WellnessBot Config
        if (selectedAgent && selectedAgent.name === 'WellnessBot') {
            const isConfigChanged = !lastWellnessConfig ||
                wellnessConfig.emotional_wellness_score !== lastWellnessConfig.emotional_wellness_score ||
                wellnessConfig.financial_wellness_score !== lastWellnessConfig.financial_wellness_score ||
                wellnessConfig.current_mood_score !== lastWellnessConfig.current_mood_score ||
                wellnessConfig.stress_level !== lastWellnessConfig.stress_level ||
                wellnessConfig.concerns !== lastWellnessConfig.concerns;

            const isGenerateDisabled = isGeneratingSupport || (generatedSupport && !isConfigChanged);

            const getScoreColor = (score) => {
                if (score >= 7) return 'text-green-400';
                if (score >= 4) return 'text-yellow-400';
                return 'text-red-400';
            };

            return (
                <div className="space-y-4 p-6">
                    {/* Wellness Scores */}
                    <div className="space-y-4">
                        {/* Emotional Wellness */}
                        <div>
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider flex justify-between mb-2">
                                <span>Emotional Wellness</span>
                                <span className={`font-bold ${getScoreColor(wellnessConfig.emotional_wellness_score)}`}>
                                    {wellnessConfig.emotional_wellness_score}/10
                                </span>
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="10"
                                value={wellnessConfig.emotional_wellness_score}
                                onChange={e => setWellnessConfig({ ...wellnessConfig, emotional_wellness_score: parseInt(e.target.value) })}
                                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                                disabled={isGeneratingSupport}
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>Needs Attention</span>
                                <span>Excellent</span>
                            </div>
                        </div>

                        {/* Financial Wellness */}
                        <div>
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider flex justify-between mb-2">
                                <span>Financial Wellness</span>
                                <span className={`font-bold ${getScoreColor(wellnessConfig.financial_wellness_score)}`}>
                                    {wellnessConfig.financial_wellness_score}/10
                                </span>
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="10"
                                value={wellnessConfig.financial_wellness_score}
                                onChange={e => setWellnessConfig({ ...wellnessConfig, financial_wellness_score: parseInt(e.target.value) })}
                                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                                disabled={isGeneratingSupport}
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>Struggling</span>
                                <span>Thriving</span>
                            </div>
                        </div>

                        {/* Current Mood */}
                        <div>
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider flex justify-between mb-2">
                                <span>Current Mood</span>
                                <span className={`font-bold ${getScoreColor(wellnessConfig.current_mood_score)}`}>
                                    {wellnessConfig.current_mood_score}/10
                                </span>
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="10"
                                value={wellnessConfig.current_mood_score}
                                onChange={e => setWellnessConfig({ ...wellnessConfig, current_mood_score: parseInt(e.target.value) })}
                                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                                disabled={isGeneratingSupport}
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>Low</span>
                                <span>Great</span>
                            </div>
                        </div>

                        {/* Stress Level */}
                        <div>
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider flex justify-between mb-2">
                                <span>Stress Level</span>
                                <span className={`font-bold ${wellnessConfig.stress_level >= 7 ? 'text-red-400' : wellnessConfig.stress_level >= 4 ? 'text-yellow-400' : 'text-green-400'}`}>
                                    {wellnessConfig.stress_level}/10
                                </span>
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="10"
                                value={wellnessConfig.stress_level}
                                onChange={e => setWellnessConfig({ ...wellnessConfig, stress_level: parseInt(e.target.value) })}
                                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                                disabled={isGeneratingSupport}
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>Relaxed</span>
                                <span>Very Stressed</span>
                            </div>
                        </div>
                    </div>

                    {/* Concerns */}
                    <div>
                        <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Concerns (Optional)</label>
                        <textarea
                            value={wellnessConfig.concerns}
                            onChange={e => setWellnessConfig({ ...wellnessConfig, concerns: e.target.value })}
                            placeholder="Share any concerns or challenges you're facing..."
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white text-sm mt-1 outline-none focus:border-orange-500 resize-none"
                            rows="3"
                            disabled={isGeneratingSupport}
                        />
                    </div>

                    <button
                        onClick={handleGenerateSupport}
                        disabled={isGenerateDisabled}
                        className={`w-full py-3 mt-4 rounded-xl font-bold text-sm transition-all shadow-lg flex justify-center items-center gap-2 ${isGenerateDisabled && generatedSupport ? 'bg-green-600/20 text-green-400 cursor-not-allowed border border-green-500/30' : 'bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white hover:shadow-orange-500/20'} ${!generatedSupport && isGenerateDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isGeneratingSupport ? <><FaSpinner className="animate-spin" /> Generating...</> :
                            (generatedSupport && !isConfigChanged ? <><FaCheckCircle /> Support Generated</> :
                                (generatedSupport ? <><FaPaperPlane /> Generate New Support</> : 'Generate Wellness Support')
                            )}
                    </button>
                    {isGeneratingSupport && <p className="text-xs text-gray-500 text-center animate-pulse">Preparing your personalized wellness support...</p>}
                </div>
            );
        }

        return (
            <div className="flex-grow flex items-center justify-center text-center">
                <p className="text-gray-400 text-sm px-4">No configuration options for {selectedAgent.name}.</p>
            </div>
        );
    };


    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />

            <main className="flex-grow flex flex-col lg:flex-row gap-3 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>

                {/* Column 1: Config */}
                <div className="w-full lg:w-1/4 glass-panel no-hover p-4 sm:p-5 rounded-3xl border border-white/10 flex flex-col shadow-2xl h-auto lg:h-[calc(100vh-120px)] order-2 lg:order-1">
                    <div className="flex items-center justify-between mb-4 sm:mb-6 shrink-0">
                        <div className="flex items-center gap-2">
                            <FaCog className="text-orange-500 text-lg sm:text-xl" />
                            <h2 className="text-base sm:text-lg font-bold text-white">Config</h2>
                        </div>
                    </div>

                    <div className="flex-grow overflow-y-auto custom-scrollbar">
                        {renderConfigPanel()}
                    </div>
                </div>

                {/* Column 2: Interaction / Chat */}
                <div className="w-full lg:w-1/2 glass-panel no-hover p-4 sm:p-6 rounded-3xl border border-white/10 flex flex-col shadow-2xl relative overflow-hidden h-[500px] sm:h-[600px] lg:h-[calc(100vh-120px)] order-3 lg:order-2">

                    {/* Header */}
                    <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4 shrink-0 relative z-10 border-b border-white/5 pb-3 sm:pb-4">
                        <div className="flex items-center gap-2 sm:gap-3 flex-grow">
                            <FaCommentAlt className="text-orange-500 text-lg sm:text-xl" />
                            <h2 className="text-lg sm:text-xl font-bold text-white">
                                {selectedAgent ? selectedAgent.name : "Agent Interaction"}
                            </h2>
                            {isChatEnabled && <span className="text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">Active</span>}
                        </div>
                        {selectedAgent && (
                            <button
                                onClick={handleResetAgent}
                                className="text-xs text-gray-500 hover:text-red-400 flex items-center gap-1.5 transition-all bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg border border-white/10"
                                title="Reset Agent Session"
                            >
                                <FaTrashAlt className="text-[10px]" /> Reset Session
                            </button>
                        )}
                    </div>

                    {/* Content Area */}
                    <div className="flex-grow overflow-y-auto custom-scrollbar relative z-10 pr-2 space-y-6">
                        {!selectedAgent ? (
                            <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
                                <FaRobot className="text-6xl text-gray-600 mb-4" />
                                <p className="text-gray-400">Select an agent to begin.</p>
                            </div>
                        ) : (
                            <>
                                {/* Generated Lesson Display */}
                                {generatedLesson && (
                                    <div className="bg-black/40 backdrop-blur-md rounded-2xl p-6 border-l-4 border-orange-500 shadow-xl animate-fade-in-up">
                                        <div className="flex items-center gap-3 mb-4 text-orange-400 border-b border-white/5 pb-2">
                                            <FaBook className="text-lg" />
                                            <h3 className="font-bold text-sm uppercase tracking-wider">Generated Lesson</h3>
                                        </div>
                                        <div className="prose prose-invert max-w-none prose-sm marker:text-orange-500 prose-headings:text-white prose-a:text-blue-400 prose-strong:text-orange-200 prose-p:leading-relaxed prose-li:leading-relaxed prose-hr:border-white/10">
                                            <ReactMarkdown>{generatedLesson}</ReactMarkdown>
                                        </div>
                                    </div>
                                )}

                                {/* Generated Financial Advice Display */}
                                {generatedAdvice && (
                                    <div className="bg-black/40 backdrop-blur-md rounded-2xl p-6 border-l-4 border-blue-500 shadow-xl animate-fade-in-up">
                                        <div className="flex items-center gap-3 mb-4 text-blue-400 border-b border-white/5 pb-2">
                                            <FaDollarSign className="text-lg" />
                                            <h3 className="font-bold text-sm uppercase tracking-wider">Financial Advice</h3>
                                        </div>

                                        {/* Savings Summary */}
                                        <div className="grid grid-cols-3 gap-3 mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
                                            <div className="text-center">
                                                <p className="text-xs text-gray-400">Income</p>
                                                <p className="text-lg font-bold text-green-400">₹{generatedAdvice.monthly_income}</p>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-xs text-gray-400">Expenses</p>
                                                <p className="text-lg font-bold text-red-400">₹{generatedAdvice.monthly_expenses}</p>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-xs text-gray-400">Savings</p>
                                                <p className={`text-lg font-bold ${generatedAdvice.monthly_savings >= 0 ? 'text-blue-400' : 'text-red-400'}`}>
                                                    ₹{generatedAdvice.monthly_savings}
                                                </p>
                                            </div>
                                        </div>

                                        {/* AI Generated Advice */}
                                        <div className="prose prose-invert max-w-none prose-sm marker:text-blue-500 prose-headings:text-white prose-a:text-blue-400 prose-strong:text-blue-200 prose-p:leading-relaxed prose-li:leading-relaxed prose-hr:border-white/10">
                                            <ReactMarkdown>{generatedAdvice.financial_advice}</ReactMarkdown>
                                        </div>
                                    </div>
                                )}

                                {/* Generated Wellness Support Display */}
                                {generatedSupport && (
                                    <div className="bg-black/40 backdrop-blur-md rounded-2xl p-6 border-l-4 border-orange-500 shadow-xl animate-fade-in-up">
                                        <div className="flex items-center gap-3 mb-4 text-orange-400 border-b border-white/5 pb-2">
                                            <FaHeartbeat className="text-lg" />
                                            <h3 className="font-bold text-sm uppercase tracking-wider">Wellness Support</h3>
                                        </div>

                                        {/* Overall Assessment */}
                                        <div className="mb-4 p-4 bg-orange-500/10 rounded-lg border border-orange-500/20">
                                            <h4 className="text-xs font-bold text-orange-400 uppercase tracking-wider mb-2">Overall Assessment</h4>
                                            <p className="text-base text-gray-200 leading-relaxed">{generatedSupport.overall_assessment}</p>
                                        </div>

                                        {/* Emotional Support & Motivational Message */}
                                        <div className="prose prose-invert max-w-none prose-base marker:text-orange-500 prose-headings:text-white prose-a:text-orange-400 prose-strong:text-orange-200 prose-p:leading-relaxed prose-li:leading-relaxed prose-hr:border-white/10 mb-4">
                                            <ReactMarkdown>{generatedSupport.emotional_support}</ReactMarkdown>
                                            <ReactMarkdown>{generatedSupport.motivational_message}</ReactMarkdown>
                                        </div>

                                        {/* Positive Affirmations */}
                                        {generatedSupport.positive_affirmations && generatedSupport.positive_affirmations.length > 0 && (
                                            <div className="mb-4">
                                                <h4 className="text-xs font-bold text-orange-400 uppercase tracking-wider mb-2">✨ Positive Affirmations</h4>
                                                <ul className="space-y-2">
                                                    {generatedSupport.positive_affirmations.map((affirmation, idx) => (
                                                        <li key={idx} className="text-base text-gray-200 flex items-start gap-2">
                                                            <span className="text-orange-400 mt-1">•</span>
                                                            <span>{affirmation}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {/* Recommendations */}
                                        {generatedSupport.recommendations && generatedSupport.recommendations.length > 0 && (
                                            <div>
                                                <h4 className="text-xs font-bold text-orange-400 uppercase tracking-wider mb-2">💡 Recommendations</h4>
                                                <ul className="space-y-2">
                                                    {generatedSupport.recommendations.map((rec, idx) => (
                                                        <li key={idx} className="text-base text-gray-200 flex items-start gap-2">
                                                            <span className="text-orange-400 mt-1">•</span>
                                                            <span>{rec}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Chat History */}
                                {chatHistory.map((msg, i) => (
                                    <div key={i} className={`flex items-end gap-3 animate-fade-in-up ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>

                                        {/* Bot Avatar */}
                                        {msg.role !== 'user' && (
                                            <div className="w-8 h-8 rounded-full bg-black/50 border border-white/10 flex items-center justify-center shrink-0 mb-1 ring-1 ring-white/10 shadow-lg">
                                                {(() => {
                                                    const AgentIcon = selectedAgent?.icon || FaRobot;
                                                    return <AgentIcon className="text-orange-400 text-xs" />;
                                                })()}
                                            </div>
                                        )}

                                        <div className={`max-w-[75%] p-4 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-sm border ${msg.role === 'user'
                                            ? 'bg-gradient-to-tr from-orange-600 to-amber-600 text-white rounded-br-none border-orange-400/30'
                                            : 'bg-white/5 text-gray-100 rounded-bl-none border-white/10'
                                            }`}>
                                            <div className="prose prose-invert max-w-none prose-p:my-0 prose-ul:my-1 prose-sm">
                                                <ReactMarkdown
                                                    components={{
                                                        code({ node, inline, className, children, ...props }) {
                                                            return !inline ? (
                                                                <div className="bg-black/50 rounded-lg p-2 my-2 border border-white/10 font-mono text-xs overflow-x-auto">
                                                                    {children}
                                                                </div>
                                                            ) : (
                                                                <code className="bg-black/30 px-1 py-0.5 rounded text-orange-300 font-mono text-xs" {...props}>
                                                                    {children}
                                                                </code>
                                                            )
                                                        }
                                                    }}
                                                >
                                                    {msg.content}
                                                </ReactMarkdown>
                                            </div>
                                        </div>

                                        {/* User Avatar */}
                                        {msg.role === 'user' && (
                                            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 flex items-center justify-center shrink-0 mb-1 ring-2 ring-black shadow-lg">
                                                <FaUser className="text-white text-xs" />
                                            </div>
                                        )}
                                    </div>
                                ))}

                                {isChatLoading && (
                                    <div className="flex items-center gap-3 animate-pulse">
                                        <div className="w-8 h-8 rounded-full bg-black/50 border border-white/10 flex items-center justify-center shrink-0">
                                            <FaSpinner className="text-orange-400 text-xs animate-spin" />
                                        </div>
                                        <div className="bg-white/5 px-4 py-3 rounded-2xl rounded-bl-none border border-white/10 flex items-center gap-1.5">
                                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
                                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-75"></span>
                                            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-150"></span>
                                        </div>
                                    </div>
                                )}
                                <div ref={chatEndRef} />
                            </>
                        )}
                    </div>

                    {/* Chat Input */}
                    <div className="mt-4 pt-4 border-t border-white/5 shrink-0 relative z-20">
                        <div className={`bg-black/40 p-2 rounded-xl border border-white/10 flex items-center gap-3 transition-all ${!isChatEnabled ? 'opacity-50 grayscale' : 'opacity-100'}`}>
                            <input
                                type="text"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                disabled={!isChatEnabled} // Controlled by State
                                placeholder={isChatEnabled ? "Ask a follow-up question..." : (selectedAgent?.name === 'EduMentor' ? "Generate a lesson first to chat..." : "Select an agent...")}
                                className="flex-grow bg-transparent border-none outline-none text-white placeholder-gray-500 px-3 py-2 text-sm disabled:cursor-not-allowed"
                                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                            />
                            <button
                                onClick={handleSendMessage}
                                disabled={!isChatEnabled || !message.trim()}
                                className={`p-2.5 bg-orange-600 text-white rounded-lg transition-all shadow-lg ${!isChatEnabled ? 'cursor-not-allowed hidden' : 'hover:bg-orange-500 hover:scale-105'}`}
                            >
                                <FaPaperPlane />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Column 3: Agents List */}
                <div className="w-full lg:w-1/4 glass-panel no-hover p-4 sm:p-5 rounded-3xl border border-white/10 flex flex-col shadow-2xl h-auto lg:h-[calc(100vh-120px)] order-1 lg:order-3">
                    <div className="flex items-center gap-2 mb-4 sm:mb-6 shrink-0">
                        <FaRobot className="text-orange-500 text-lg sm:text-xl" />
                        <h2 className="text-base sm:text-lg font-bold text-white">Agents</h2>
                    </div>

                    <div className="flex-grow overflow-y-auto custom-scrollbar space-y-3 pr-1">
                        {agents.map((agent) => {
                            const AgentIcon = agent.icon || FaRobot;
                            return (
                                <div
                                    key={agent.id}
                                    onClick={() => setSelectedAgent(agent)}
                                    className={`bg-white/5 border rounded-xl p-4 transition-all cursor-pointer group relative ${selectedAgent?.id === agent.id ? 'border-orange-500 bg-orange-500/10 shadow-[0_0_15px_rgba(249,115,22,0.15)]' : 'border-white/10 hover:bg-white/10 hover:border-white/20'}`}
                                >
                                    {/* Status Badge (Absolute) */}
                                    <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-white/5 px-2 py-1 rounded text-[10px] text-gray-200 border border-white/5 font-medium">
                                        <FaCircle className={`text-[6px] ${selectedAgent?.id === agent.id ? 'text-green-400' : 'text-gray-500'}`} />
                                        {selectedAgent?.id === agent.id ? 'active' : 'idle'}
                                    </div>

                                    <div className="flex items-start gap-3 mb-4 mt-1">
                                        <div className={`w-12 h-12 rounded-full bg-white/5 flex items-center justify-center border border-white/10 flex-shrink-0`}>
                                            <AgentIcon className={`text-xl ${agent.color}`} />
                                        </div>
                                        <div className="pr-12">
                                            <h3 className="text-lg font-bold text-white leading-tight mb-1">{agent.name}</h3>
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${agent.tagBg} ${agent.tagText} uppercase tracking-wide inline-block`}>
                                                {agent.category}
                                            </span>
                                        </div>
                                    </div>

                                    <p className="text-gray-200 text-xs italic mb-4 leading-relaxed pl-3 border-l-2 border-white/20">
                                        "{agent.description}"
                                    </p>

                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wide">Confidence</span>
                                            <span className={`text-xs font-bold ${agent.color.replace('text-', 'text-')}`}>{agent.confidence}%</span>
                                        </div>
                                        <div className="w-full bg-black/70 rounded-full h-1.5 overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${agent.barColor}`}
                                                style={{ width: `${agent.confidence}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>


            </main>
        </div>
    );
};

export default AgentSimulator;
