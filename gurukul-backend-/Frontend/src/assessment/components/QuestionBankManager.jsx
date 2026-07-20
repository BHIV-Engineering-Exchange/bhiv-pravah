import React, { useState, useEffect, useMemo } from 'react';
import { toast } from 'react-hot-toast';
import { supabase } from '../lib/supabaseClient';
import { Plus, Settings, Search, Filter, Brain, Code, Calculator, MessageCircle, Globe, Scroll, Newspaper, BookOpen, HelpCircle, AlertCircle, Users, Edit2, Trash2, ChevronDown } from 'lucide-react';
import { createPortal } from 'react-dom';
import { DynamicQuestionCategoryService } from '../lib/dynamicQuestionCategoryService';
import { aiSettingsService } from '../lib/aiSettingsService';

// Icon mapping for question categories (supports dynamic categories)
const DEFAULT_CATEGORY_ICONS = {
  Code,
  Brain,
  Calculator,
  BookOpen,
  Globe,
  Scroll,
  Newspaper,
  MessageCircle,
  HelpCircle
};

// Helper function to get icon component by name
const getIconComponent = (iconName, category) => {
  if (iconName && DEFAULT_CATEGORY_ICONS[iconName]) {
    return DEFAULT_CATEGORY_ICONS[iconName];
  }
  // Fallback to category-based mapping for backward compatibility
  const legacyIcons = {
    'Coding': Code,
    'Logic': Brain,
    'Mathematics': Calculator,
    'Language': MessageCircle,
    'Culture': Globe,
    'Vedic Knowledge': Scroll,
    'Current Affairs': Newspaper
  };
  return legacyIcons[category] || BookOpen;
};

const DIFFICULTY_LEVELS = {
  EASY: 'Easy',
  MEDIUM: 'Medium',
  HARD: 'Hard'
};

// Supported school grades for targeting (extend as needed)
const GRADES = ['1','2','3','4','5','6','7','8','9','10','11','12'];

const DIFFICULTY_COLORS = {
  [DIFFICULTY_LEVELS.EASY]: 'text-green-400 bg-green-400/10 border-green-400/20',
  [DIFFICULTY_LEVELS.MEDIUM]: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  [DIFFICULTY_LEVELS.HARD]: 'text-red-400 bg-red-400/10 border-red-400/20'
};

const FIELD_COLORS = [
  'text-blue-400 bg-blue-400/10 border-blue-400/20',
  'text-green-400 bg-green-400/10 border-green-400/20',
  'text-purple-400 bg-purple-400/10 border-purple-400/20',
  'text-red-400 bg-red-400/10 border-red-400/20',
  'text-pink-400 bg-pink-400/10 border-pink-400/20',
  'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  'text-indigo-400 bg-indigo-400/10 border-indigo-400/20',
  'text-teal-400 bg-teal-400/10 border-teal-400/20',
  'text-orange-400 bg-orange-400/10 border-orange-400/20',
  'text-cyan-400 bg-cyan-400/10 border-cyan-400/20'
];

function QuestionCard({ question, questionFields, studyFields, onEdit, onDelete, onManageFields, aiEnabled, categories }) {
  const IconComponent = getIconComponent(categories?.find(cat => cat.name === question.category)?.icon, question.category);
  const difficultyClass = DIFFICULTY_COLORS[question.difficulty] || DIFFICULTY_COLORS[DIFFICULTY_LEVELS.EASY];
  const isAiQuestion = question.created_by === 'ai';

  return (
    <div 
      className={`rounded-xl border border-white/20 ${isAiQuestion && !aiEnabled ? 'bg-gray-800/30' : 'bg-white/10'} p-4 space-y-4`}
      style={{
        // When AI is disabled and this is an AI question, use a dimmer background
        backgroundColor: isAiQuestion && !aiEnabled ? 'rgba(100, 116, 139, 0.3)' : undefined
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <IconComponent className="h-5 w-5 text-orange-400" />
          <span className="text-sm font-medium text-orange-400">{question.category}</span>
          <span className={`text-xs px-2 py-1 rounded-full border ${difficultyClass}`}>
            {question.difficulty}
          </span>
          {isAiQuestion && (
            <span 
              className={`text-xs px-2 py-1 rounded-full ${aiEnabled ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-gray-500/20 text-gray-300 border border-gray-500/30'}`}
            >
              {aiEnabled ? 'AI Generated' : 'AI Disabled'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onManageFields(question)}
            className="p-1 rounded hover:bg-white/10 text-white/70 hover:text-blue-400"
            title="Manage Fields"
          >
            <Users className="w-4 h-4" />
          </button>
          <button
            onClick={() => onEdit(question)}
            className="p-1 rounded hover:bg-white/10 text-white/70 hover:text-white"
            title="Edit Question"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(question)}
            className="p-1 rounded hover:bg-white/10 text-white/70 hover:text-red-400"
            title="Delete Question"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Field Tags */}
      {questionFields && questionFields.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {questionFields.map(fieldId => {
            const field = studyFields.find(f => f.field_id === fieldId);
            if (!field) return null;
            return (
              <span
                key={fieldId}
                className={`text-xs px-2 py-1 rounded-full border ${field.color}`}
                title={`Assigned to ${field.name} students`}
              >
                {field.icon} {field.name}
              </span>
            );
          })}
        </div>
      )}

      {/* Question Content */}
      <div className="space-y-3">
        <h4 className="text-white font-medium">{question.question_text}</h4>
        
        <div className="space-y-1">
          {question.options?.map((option, index) => (
            <div
              key={index}
              className={`text-sm p-2 rounded ${
                option === question.correct_answer
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'text-white/70'
              }`}
            >
              {option}
            </div>
          ))}
        </div>

        {question.explanation && (
          <div className="text-sm text-white/60">
            <strong>Explanation:</strong> {question.explanation}
          </div>
        )}

        {question.vedic_connection && (
          <div className="text-sm text-orange-400/80">
            <strong>Vedic Connection:</strong> {question.vedic_connection}
          </div>
        )}

        {question.modern_application && (
          <div className="text-sm text-blue-400/80">
            <strong>Modern Application:</strong> {question.modern_application}
          </div>
        )}
      </div>
    </div>
  );
}

export default function QuestionBankManager() {
  const [questions, setQuestions] = useState([]);
  const [studyFields, setStudyFields] = useState([]);
  const [questionCategories, setQuestionCategories] = useState([]);
  const [questionFieldMappings, setQuestionFieldMappings] = useState({});
  const [filteredQuestions, setFilteredQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [selectedField, setSelectedField] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [showFieldManager, setShowFieldManager] = useState(false);
  const [managingQuestion, setManagingQuestion] = useState(null);
  const [showFieldSettings, setShowFieldSettings] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [fieldDeleteConfirm, setFieldDeleteConfirm] = useState(null);
  const [stats, setStats] = useState({});
  const [aiEnabled, setAiEnabled] = useState(true); // This will be updated with global setting
  const [showTooltip, setShowTooltip] = useState(false); // Tooltip state
  // Question form state
  const [qForm, setQForm] = useState({
    question_text: '',
    options: ['', '', '', ''],
    correct_answer: '',
    category: '',
    difficulty: DIFFICULTY_LEVELS.EASY,
    explanation: '',
    vedic_connection: '',
    modern_application: '',
    selectedFieldIds: [],
    selectedLevel: '' // '9','10','11','12','undergraduate','graduate','postgraduate'
  });

  // Load AI settings on component mount
  useEffect(() => {
    const loadAISettings = async () => {
      try {
        const isEnabled = await aiSettingsService.isAIEnabled();
        setAiEnabled(isEnabled);
      } catch (error) {
        console.error('Error loading AI settings:', error);
      }
    };

    loadAISettings();
  }, []);

  // Toggle AI enabled state
  const toggleAIEnabled = async () => {
    try {
      const newEnabledState = !aiEnabled;
      await aiSettingsService.setAIEnabled(newEnabledState);
      setAiEnabled(newEnabledState);
      toast.success(`AI question generation ${newEnabledState ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Error toggling AI settings:', error);
      toast.error('Failed to update AI settings');
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  // Filter questions when filters or AI state change
  useEffect(() => {
    filterQuestions();
  }, [questions, searchTerm, selectedCategory, selectedDifficulty, selectedField, aiEnabled]);

  // Calculate stats when filtered questions change
  useEffect(() => {
    calculateStats();
  }, [filteredQuestions, questionFieldMappings, questionCategories, studyFields]);

  async function loadData() {
    try {
      setLoading(true);
      
      // Load questions
      const { data: questionsData, error: questionsError } = await supabase
        .from('question_banks')
        .select('*')
        .eq('is_active', true)
        .order('created_at', { ascending: false });

      if (questionsError) throw questionsError;
      setQuestions(questionsData || []);

      // Load study fields
      const { data: fieldsData, error: fieldsError } = await supabase
        .from('study_fields')
        .select('*')
        .eq('is_active', true)
        .order('name');

      if (fieldsError) throw fieldsError;
      setStudyFields(fieldsData || []);

      // Load question categories
      const categories = await DynamicQuestionCategoryService.getAllCategories();
      setQuestionCategories(categories);

      // Load question field mappings
      const { data: mappingsData, error: mappingsError } = await supabase
        .from('question_field_mapping')
        .select('question_id, field_id');

      if (mappingsError) throw mappingsError;
      
      // Group by question_id
      const mappings = {};
      (mappingsData || []).forEach(mapping => {
        if (!mappings[mapping.question_id]) {
          mappings[mapping.question_id] = [];
        }
        mappings[mapping.question_id].push(mapping.field_id);
      });
      setQuestionFieldMappings(mappings);

    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  function filterQuestions() {
    let result = [...questions];
    
    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(q => 
        q.question_text?.toLowerCase().includes(term) ||
        q.category?.toLowerCase().includes(term) ||
        q.explanation?.toLowerCase().includes(term)
      );
    }
    
    // Apply category filter
    if (selectedCategory) {
      result = result.filter(q => q.category === selectedCategory);
    }
    
    // Apply difficulty filter
    if (selectedDifficulty) {
      result = result.filter(q => q.difficulty === selectedDifficulty);
    }
    
    // Apply field filter
    if (selectedField) {
      result = result.filter(q => 
        questionFieldMappings[q.question_id] && 
        questionFieldMappings[q.question_id].includes(selectedField)
      );
    }
    
    // When AI is disabled, filter out AI-generated questions
    if (!aiEnabled) {
      result = result.filter(q => q.created_by !== 'ai');
    }
    
    setFilteredQuestions(result);
  }

  function calculateStats() {
    const newStats = {};
    
    // Initialize stats for dynamic categories
    questionCategories.forEach(category => {
      newStats[category.name] = { total: 0, easy: 0, medium: 0, hard: 0 };
    });
    
    // Add field stats
    studyFields.forEach(field => {
      newStats[`field_${field.field_id}`] = { total: 0, easy: 0, medium: 0, hard: 0 };
    });

    // Calculate stats based on filtered questions (which respect AI toggle)
    (filteredQuestions || []).forEach(q => {
      // Category stats
      if (newStats[q.category]) {
        newStats[q.category].total++;
        const diff = (q.difficulty || '').toLowerCase();
        if (diff === 'easy') newStats[q.category].easy++;
        else if (diff === 'medium') newStats[q.category].medium++;
        else if (diff === 'hard') newStats[q.category].hard++;
      }

      // Field stats - only for active questions
      const fields = questionFieldMappings[q.question_id] || [];
      fields.forEach(fieldId => {
        const key = `field_${fieldId}`;
        if (newStats[key]) {
          newStats[key].total++;
          const diff = (q.difficulty || '').toLowerCase();
          if (diff === 'easy') newStats[key].easy++;
          else if (diff === 'medium') newStats[key].medium++;
          else if (diff === 'hard') newStats[key].hard++;
        }
      });
    });

    setStats(newStats);
  }

  async function handleAddQuestion(questionData) {
    try {
      // Merge education level tag(s) into tags array
      const level = questionData.selectedLevel || '';
      const tagsToAdd = [];
      if (level) {
        if (/^(9|10|11|12)$/.test(level)) {
          // Add both new and legacy tags for numeric grades
          tagsToAdd.push(`level_${level}`);
          tagsToAdd.push(`grade_${level}`);
        } else {
          // Add education level tags
          tagsToAdd.push(`level_${level}`);
        }
      }
      const mergedTags = Array.from(new Set([...(questionData.tags || []), ...tagsToAdd]));

      // Whitelist permitted columns for question_banks upsert
      const payload = {
        question_id: questionData.question_id || `${(questionData.category || 'question').toLowerCase().replace(/\s+/g,'_')}_${Date.now()}`,
        category: String(questionData.category || '').trim(),
        difficulty: String(questionData.difficulty || DIFFICULTY_LEVELS.EASY),
        question_text: String(questionData.question_text || '').trim(),
        options: Array.isArray(questionData.options) ? questionData.options.map(o => String(o || '')) : [],
        correct_answer: String(questionData.correct_answer || '').trim(),
        explanation: String(questionData.explanation || '').trim(),
        vedic_connection: String(questionData.vedic_connection || ''),
        modern_application: String(questionData.modern_application || ''),
        tags: Array.isArray(mergedTags) ? mergedTags : [],
        is_active: true,
        created_by: 'admin',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      // Upsert the question
      const { error } = await supabase
        .from('question_banks')
        .upsert(payload);

      if (error) throw error;

      // Manage field mappings if provided
      if (Array.isArray(questionData.selectedFieldIds)) {
        // Clear existing mappings first
        await supabase
          .from('question_field_mapping')
          .delete()
          .eq('question_id', payload.question_id);

        if (questionData.selectedFieldIds.length > 0) {
          const mappings = questionData.selectedFieldIds.map(fieldId => ({
            question_id: payload.question_id,
            field_id: fieldId
          }));
          const { error: mapErr } = await supabase
            .from('question_field_mapping')
            .insert(mappings);
          if (mapErr) throw mapErr;
        }
      }

      toast.success(editingQuestion ? 'Question updated successfully' : 'Question added successfully');
      setShowForm(false);
      setEditingQuestion(null);
      // Reset form state
      setQForm({
        question_text: '', options: ['', '', '', ''], correct_answer: '',
        category: '', difficulty: DIFFICULTY_LEVELS.EASY,
        explanation: '', vedic_connection: '', modern_application: '',
        selectedFieldIds: [], selectedLevel: ''
      });
      loadData();
    } catch (error) {
      console.error('Error saving question:', error);
      toast.error('Failed to save question');
    }
  }

  async function handleDeleteQuestion(question) {
    try {
      const { error } = await supabase
        .from('question_banks')
        .update({ is_active: false })
        .eq('question_id', question.question_id);

      if (error) throw error;

      toast.success('Question deleted successfully');
      setDeleteConfirm(null);
      loadData();
    } catch (error) {
      console.error('Error deleting question:', error);
      toast.error('Failed to delete question');
    }
  }

  async function handleManageFields(question) {
    setManagingQuestion(question);
    setShowFieldManager(true);
  }

  async function saveFieldMappings() {
    try {
      if (!managingQuestion) return;

      // Get selected fields
      const selectedFields = [];
      studyFields.forEach(field => {
        const checkbox = document.getElementById(`field-manager-${field.field_id}`);
        if (checkbox?.checked) {
          selectedFields.push(field.field_id);
        }
      });

      // Delete existing mappings
      await supabase
        .from('question_field_mapping')
        .delete()
        .eq('question_id', managingQuestion.question_id);

      // Insert new mappings
      if (selectedFields.length > 0) {
        const mappings = selectedFields.map(fieldId => ({
          question_id: managingQuestion.question_id,
          field_id: fieldId
        }));

        const { error } = await supabase
          .from('question_field_mapping')
          .insert(mappings);

        if (error) throw error;
      }

      toast.success('Field assignments saved successfully');
      setShowFieldManager(false);
      setManagingQuestion(null);
      loadData(); // Reload to update mappings
    } catch (error) {
      console.error('Error saving field mappings:', error);
      toast.error('Failed to save field assignments');
    }
  }

  const uniqueCategories = useMemo(() => {
    const categories = [...new Set(questions.map(q => q.category))];
    return categories.filter(Boolean).sort();
  }, [questions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Question Bank</h1>
            <div className="flex items-center gap-2">
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${aiEnabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                <div className={`w-2 h-2 rounded-full ${aiEnabled ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                AI Questions: {aiEnabled ? 'Enabled' : 'Disabled'}
              </div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            {/* AI Toggle */}
            <div className="relative">
              <button
                onClick={toggleAIEnabled}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  aiEnabled 
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30' 
                    : 'bg-gray-500/20 text-gray-400 border border-gray-500/30 hover:bg-gray-500/30'
                }`}
              >
                <Brain className="w-4 h-4" />
                AI Questions: {aiEnabled ? 'ON' : 'OFF'}
              </button>
              
              {showTooltip && (
                <div 
                  className="absolute top-full mt-2 left-0 bg-gray-800 text-white text-xs p-2 rounded-lg border border-gray-700 shadow-lg z-10"
                  style={{
                    minWidth: '200px',
                    maxWidth: '200px',
                    textAlign: 'center'
                  }}
                >
                  {aiEnabled 
                    ? 'AI-generated questions are included in assignments' 
                    : 'Only admin-created questions are shown to students'}
                </div>
              )}
            </div>
            
            <button
              onClick={() => {
                setEditingQuestion(null);
                setQForm({
                  question_text: '',
                  options: ['', '', '', ''],
                  correct_answer: '',
                  category: '',
                  difficulty: DIFFICULTY_LEVELS.EASY,
                  explanation: '',
                  vedic_connection: '',
                  modern_application: '',
                  selectedFieldIds: [],
                  selectedLevel: ''
                });
                setShowForm(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-medium hover:from-orange-600 hover:to-red-600 transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Question
            </button>
            
            <button
              onClick={() => setShowFieldSettings(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-lg font-medium border border-white/20 hover:bg-white/20 transition-all"
            >
              <Settings className="w-4 h-4" />
              Manage Fields
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white/10 rounded-xl p-4 border border-white/20">
            <div className="text-2xl font-bold text-white">{filteredQuestions.length}</div>
            <div className="text-white/70 text-sm">Total Questions</div>
          </div>
          
          {uniqueCategories.slice(0, 3).map(category => (
            <div key={category} className="bg-white/10 rounded-xl p-4 border border-white/20">
              <div className="text-2xl font-bold text-white">{stats[category]?.total || 0}</div>
              <div className="text-white/70 text-sm">{category}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="bg-white/10 rounded-xl p-4 border border-white/20 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-4 h-4" />
              <input
                type="text"
                placeholder="Search questions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-500/50"
              />
            </div>
            
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
            >
              <option value="">All Categories</option>
              {uniqueCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
            
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
            >
              <option value="">All Difficulties</option>
              {Object.values(DIFFICULTY_LEVELS).map(difficulty => (
                <option key={difficulty} value={difficulty}>{difficulty}</option>
              ))}
            </select>
            
            <select
              value={selectedField}
              onChange={(e) => setSelectedField(e.target.value)}
              className="px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white"
            >
              <option value="">All Fields</option>
              {studyFields.map(field => (
                <option key={field.field_id} value={field.field_id}>{field.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Questions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredQuestions.map(question => (
            <QuestionCard
              key={question.question_id}
              question={question}
              questionFields={questionFieldMappings[question.question_id] || []}
              studyFields={studyFields}
              categories={questionCategories}
              onEdit={(q) => {
                setEditingQuestion(q);
                // Initialize form with existing question
                const mappedFields = questionFieldMappings[q.question_id] || [];
                setQForm({
                  question_text: q.question_text || '',
                  options: Array.isArray(q.options) ? q.options : ['', '', '', ''],
                  correct_answer: q.correct_answer || '',
                  category: q.category || '',
                  difficulty: q.difficulty || DIFFICULTY_LEVELS.EASY,
                  explanation: q.explanation || '',
                  vedic_connection: q.vedic_connection || '',
                  modern_application: q.modern_application || '',
                  selectedFieldIds: mappedFields,
                  selectedLevel: (() => {
                    const tags = Array.isArray(q.tags) ? q.tags : [];
                    const levelTag = tags.find(t => /^level_/.test(t));
                    if (levelTag) return levelTag.replace('level_','');
                    const gradeTag = tags.find(t => /^grade_\d+$/.test(t));
                    return gradeTag ? gradeTag.replace('grade_','') : '';
                  })()
                });
                setShowForm(true);
              }}
              onDelete={(q) => setDeleteConfirm(q)}
              onManageFields={handleManageFields}
              aiEnabled={aiEnabled}
            />
          ))}
        </div>

        {filteredQuestions.length === 0 && (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 text-white/30 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No questions found</h3>
            <p className="text-white/70 mb-4">
              {searchTerm || selectedCategory || selectedDifficulty || selectedField
                ? 'Try adjusting your filters'
                : 'Get started by adding your first question'}
            </p>
            {!searchTerm && !selectedCategory && !selectedDifficulty && !selectedField && (
              <button
                onClick={() => {
                  setEditingQuestion(null);
                  setShowForm(true);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-medium hover:from-orange-600 hover:to-red-600 transition-all"
              >
                <Plus className="w-4 h-4" />
                Add Question
              </button>
            )}
          </div>
        )}
      </div>

      {/* Question Form Modal */}
      {showForm && createPortal(
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => {
            setShowForm(false);
            setEditingQuestion(null);
          }}
          >
          <div 
          className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl border border-white/20 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl ring-1 ring-white/10"
          onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">
                  {editingQuestion ? 'Edit Question' : 'Add New Question'}
                </h2>
                <button
                  onClick={() => {
                    setShowForm(false);
                    setEditingQuestion(null);
                  }}
                  className="p-2 rounded-lg hover:bg-white/10 text-white/70"
                >
                  ×
                </button>
              </div>
              
              {/* Question Form */}
              <div className="text-white space-y-6">
                <div className="grid grid-cols-1 gap-4">
                  {/* Targeting Section */}
                  <div className="space-y-4">
                    <h4 className="text-white/90 font-semibold">Targeting</h4>
                    {/* Study Fields */}
                    <div>
                      <label className="block text-sm text-white/80 mb-2">Assign to Study Fields</label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {studyFields.map(field => {
                          const checked = qForm.selectedFieldIds.includes(field.field_id);
                          return (
                            <label key={field.field_id} className="flex items-center gap-2 p-2 rounded-lg border border-white/20 bg-white/5 hover:bg-white/10 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={(e) => {
                                  setQForm(f => ({
                                    ...f,
                                    selectedFieldIds: e.target.checked
                                      ? [...f.selectedFieldIds, field.field_id]
                                      : f.selectedFieldIds.filter(id => id !== field.field_id)
                                  }));
                                }}
                              />
                              <span className="text-lg">{field.icon}</span>
                              <span className="text-white">{field.name}</span>
                            </label>
                          );
                        })}
                      </div>
                    </div>

                    {/* Category and Education Level */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-white/80 mb-1">Category</label>
                        <div className="relative">
                          <select
                            value={qForm.category}
                            onChange={(e) => setQForm(f => ({ ...f, category: e.target.value }))}
                            className="w-full appearance-none pr-10 px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
                          >
                            <option value="">Select category</option>
                            {questionCategories.map(cat => (
                              <option key={cat.category_id} value={cat.name}>{cat.name}</option>
                            ))}
                          </select>
                          <ChevronDown className="w-4 h-4 text-white/60 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm text-white/80 mb-1">Education Level</label>
                        <div className="relative">
                          <select
                            value={qForm.selectedLevel}
                            onChange={(e) => setQForm(f => ({ ...f, selectedLevel: e.target.value }))}
                            className="w-full appearance-none pr-10 px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
                          >
                            <option value="">Select level</option>
                            <option value="9">9th Grade</option>
                            <option value="10">10th Grade</option>
                            <option value="11">11th Grade</option>
                            <option value="12">12th Grade</option>
                            <option value="undergraduate">Undergraduate</option>
                            <option value="graduate">Graduate</option>
                            <option value="postgraduate">Postgraduate</option>
                          </select>
                          <ChevronDown className="w-4 h-4 text-white/60 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Question Text */}
                  <div>
                    <label className="block text-sm text-white/80 mb-1">Question Text</label>
                    <textarea
                      value={qForm.question_text}
                      onChange={(e) => setQForm(f => ({ ...f, question_text: e.target.value }))}
                      rows={3}
                      className="w-full p-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
                      placeholder="Enter the question..."
                    />
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <label className="block text-sm text-white/80 mb-1">Difficulty</label>
                      <div className="relative">
                        <select
                          value={qForm.difficulty}
                          onChange={(e) => setQForm(f => ({ ...f, difficulty: e.target.value }))}
                          className="w-full appearance-none pr-10 px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
                        >
                          {Object.values(DIFFICULTY_LEVELS).map(d => (
                            <option key={d} value={d}>{d}</option>
                          ))}
                        </select>
                        <ChevronDown className="w-4 h-4 text-white/60 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                      </div>
                    </div>
                  </div>

                  {/* Options */}
                  <div className="space-y-2">
                    <label className="block text-sm text-white/80">Options (4)</label>
                    {qForm.options.map((opt, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={opt}
                          onChange={(e) => {
                            const opts = [...qForm.options];
                            opts[idx] = e.target.value;
                            setQForm(f => ({ ...f, options: opts }));
                          }}
                          className="flex-1 px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
                          placeholder={`Option ${idx + 1}`}
                        />
                        <label className="flex items-center gap-1 text-xs text-white/70">
                          <input
                            type="radio"
                            name="correct"
                            checked={qForm.correct_answer === opt && !!opt}
                            onChange={() => setQForm(f => ({ ...f, correct_answer: opt }))}
                          />
                          Correct
                        </label>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-white/80 mb-1">Explanation</label>
                      <textarea
                        value={qForm.explanation}
                        onChange={(e) => setQForm(f => ({ ...f, explanation: e.target.value }))}
                        rows={2}
                        className="w-full p-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-400"
                        placeholder="Provide explanation for the correct answer"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-white/80 mb-1">Vedic Connection (optional)</label>
                      <textarea
                        value={qForm.vedic_connection}
                        onChange={(e) => setQForm(f => ({ ...f, vedic_connection: e.target.value }))}
                        rows={2}
                        className="w-full p-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50"
                        placeholder="Any traditional connection?"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-white/80 mb-1">Modern Application (optional)</label>
                    <textarea
                      value={qForm.modern_application}
                      onChange={(e) => setQForm(f => ({ ...f, modern_application: e.target.value }))}
                      rows={2}
                      className="w-full p-3 rounded-lg bg-white/5 border border-white/20 text-white placeholder-white/50"
                      placeholder="Any modern application?"
                    />
                  </div>

                  
                                  </div>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => {
                      setShowForm(false);
                      setEditingQuestion(null);
                    }}
                    className="flex-1 px-4 py-2 rounded-lg border border-white/20 bg-white/10 text-white hover:bg-white/20 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      // Validate
                      const errors = [];
                      if (!qForm.category) errors.push('Category');
                      if (!qForm.question_text.trim()) errors.push('Question Text');
                      const filledOptions = qForm.options.filter(o => o && o.trim());
                      if (filledOptions.length !== 4) errors.push('All 4 Options');
                      if (!filledOptions.includes(qForm.correct_answer)) errors.push('Valid Correct Answer');
                      if (qForm.selectedFieldIds.length === 0) errors.push('At least one Study Field');
                      if (!qForm.selectedLevel) errors.push('Education Level');
                      if (errors.length) {
                        toast.error(`Please provide: ${errors.join(', ')}`);
                        return;
                      }

                      handleAddQuestion({
                        question_id: editingQuestion?.question_id,
                        question_text: qForm.question_text,
                        options: qForm.options,
                        correct_answer: qForm.correct_answer,
                        category: qForm.category,
                        difficulty: qForm.difficulty,
                        explanation: qForm.explanation,
                        vedic_connection: qForm.vedic_connection,
                        modern_application: qForm.modern_application,
                        selectedFieldIds: qForm.selectedFieldIds,
                        selectedLevel: qForm.selectedLevel
                      });
                    }}
                    className="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-red-500 text-white hover:from-orange-600 hover:to-red-600 transition-all"
                  >
                    {editingQuestion ? 'Save Changes' : 'Create Question'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Field Manager Modal */}
      {showFieldManager && managingQuestion && createPortal(
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowFieldManager(false)}
        >
          <div 
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl border border-white/20 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="mb-6">
                <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Manage Field Assignments
                </h3>
                <p className="text-white/70 text-sm">
                  Select which study fields should see this question
                </p>
                <div className="text-white/60 text-xs mt-2 p-2 bg-white/5 rounded">
                  <strong>Question:</strong> {managingQuestion.question_text.substring(0, 100)}...
                </div>
              </div>
              
              <div className="mb-6 space-y-2">
                {studyFields.map(field => {
                  const isAssigned = (questionFieldMappings[managingQuestion.question_id] || []).includes(field.field_id);
                  return (
                    <label
                      key={field.field_id}
                      className="flex items-center gap-3 p-3 rounded-lg border border-white/20 bg-white/5 hover:bg-white/10 cursor-pointer transition-all"
                    >
                      <input
                        type="checkbox"
                        id={`field-manager-${field.field_id}`}
                        defaultChecked={isAssigned}
                        className="rounded text-orange-500 focus:ring-orange-500"
                      />
                      <span className="text-lg">{field.icon}</span>
                      <span className="text-white font-medium">{field.name}</span>
                    </label>
                  );
                })}
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowFieldManager(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-white/20 bg-white/10 text-white hover:bg-white/20 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={saveFieldMappings}
                  className="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-red-500 text-white hover:from-orange-600 hover:to-red-600 transition-all"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && createPortal(
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setDeleteConfirm(null)}
        >
          <div 
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl border border-white/20 w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 text-center">
              <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-8 h-8 text-red-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Delete Question?</h3>
              <p className="text-white/70 mb-6">
                This action cannot be undone. The question will be permanently removed.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="flex-1 px-4 py-2 rounded-lg border border-white/20 bg-white/10 text-white hover:bg-white/20 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteQuestion(deleteConfirm)}
                  className="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 transition-all"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Field Settings Modal */}
      {showFieldSettings && createPortal(
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowFieldSettings(false)}
        >
          <div 
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl border border-white/20 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Field Settings
                </h2>
                <button
                  onClick={() => setShowFieldSettings(false)}
                  className="p-2 rounded-lg hover:bg-white/10 text-white/70"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-white mb-4">Study Fields</h3>
                  <div className="space-y-3">
                    {studyFields.map(field => (
                      <div key={field.field_id} className="flex items-center justify-between p-3 rounded-lg border border-white/20 bg-white/5">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{field.icon}</span>
                          <div>
                            <div className="text-white font-medium">{field.name}</div>
                            <div className="text-white/70 text-sm">{field.description}</div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              setEditingField(field);
                              setShowFieldSettings(false);
                              // Would open edit form in a real implementation
                            }}
                            className="px-3 py-1 rounded bg-white/10 text-white text-sm hover:bg-white/20"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setFieldDeleteConfirm(field)}
                            className="px-3 py-1 rounded bg-red-500/20 text-red-400 text-sm hover:bg-red-500/30"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <button
                  onClick={() => {
                    setEditingField(null);
                    setShowFieldSettings(false);
                    // Would open add form in a real implementation
                  }}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-white/10 text-white rounded-lg border border-white/20 hover:bg-white/20 transition-all"
                >
                  <Plus className="w-4 h-4" />
                  Add New Field
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}