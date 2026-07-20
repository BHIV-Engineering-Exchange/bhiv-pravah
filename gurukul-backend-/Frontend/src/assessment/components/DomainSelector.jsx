import React, { useState, useEffect } from 'react';
import { 
  Cpu, Link, Bot, Brain, Plane, Dna, Pill, 
  Gamepad2, Glasses, Shield, Code, Box, Atom,
  CheckCircle, Circle, AlertCircle
} from 'lucide-react';
import MultiDomainAssessmentService, { DOMAINS } from '../lib/multiDomainAssessmentService';

const ICON_MAP = {
  'Cpu': Cpu,
  'Link': Link,
  'Bot': Bot,
  'Brain': Brain,
  'Plane': Plane,
  'Dna': Dna,
  'Pill': Pill,
  'Gamepad2': Gamepad2,
  'Glasses': Glasses,
  'Shield': Shield,
  'Code': Code,
  'Box': Box,
  'Atom': Atom
};

const COLOR_MAP = {
  'blue': 'bg-blue-500/10 border-blue-500 text-blue-400 hover:bg-blue-500/20',
  'purple': 'bg-purple-500/10 border-purple-500 text-purple-400 hover:bg-purple-500/20',
  'green': 'bg-green-500/10 border-green-500 text-green-400 hover:bg-green-500/20',
  'pink': 'bg-pink-500/10 border-pink-500 text-pink-400 hover:bg-pink-500/20',
  'cyan': 'bg-cyan-500/10 border-cyan-500 text-cyan-400 hover:bg-cyan-500/20',
  'lime': 'bg-lime-500/10 border-lime-500 text-lime-400 hover:bg-lime-500/20',
  'rose': 'bg-rose-500/10 border-rose-500 text-rose-400 hover:bg-rose-500/20',
  'orange': 'bg-orange-500/10 border-orange-500 text-orange-400 hover:bg-orange-500/20',
  'violet': 'bg-violet-500/10 border-violet-500 text-violet-400 hover:bg-violet-500/20',
  'red': 'bg-red-500/10 border-red-500 text-red-400 hover:bg-red-500/20',
  'yellow': 'bg-yellow-500/10 border-yellow-500 text-yellow-400 hover:bg-yellow-500/20',
  'indigo': 'bg-indigo-500/10 border-indigo-500 text-indigo-400 hover:bg-indigo-500/20',
  'fuchsia': 'bg-fuchsia-500/10 border-fuchsia-500 text-fuchsia-400 hover:bg-fuchsia-500/20'
};

export default function DomainSelector({ onDomainsSelected, initialDomains = [] }) {
  const [selectedDomains, setSelectedDomains] = useState(initialDomains);
  const [error, setError] = useState('');
  const [questionCounts, setQuestionCounts] = useState({});

  useEffect(() => {
    loadQuestionCounts();
  }, []);

  const loadQuestionCounts = async () => {
    try {
      const counts = await MultiDomainAssessmentService.getDomainQuestionCounts();
      setQuestionCounts(counts);
    } catch (err) {
      console.error('Error loading question counts:', err);
    }
  };

  const toggleDomain = (domainId) => {
    setError('');
    
    if (selectedDomains.includes(domainId)) {
      setSelectedDomains(selectedDomains.filter(id => id !== domainId));
    } else {
      setSelectedDomains([...selectedDomains, domainId]);
    }
  };

  const handleContinue = () => {
    const validation = MultiDomainAssessmentService.validateDomainSelection(selectedDomains);
    
    if (!validation.valid) {
      setError(validation.error);
      return;
    }

    onDomainsSelected(selectedDomains);
  };

  const getAdaptiveInfo = () => {
    const count = selectedDomains.length;
    if (count === 0) return { level: '', description: '', color: 'gray' };
    if (count === 1) return { 
      level: 'Depth Focus', 
      description: 'Deep dive into single domain with harder questions',
      color: 'purple'
    };
    if (count === 2) return { 
      level: 'Balanced', 
      description: 'Balanced assessment across two domains',
      color: 'blue'
    };
    if (count <= 4) return { 
      level: 'Multi-Disciplinary', 
      description: 'Test knowledge across multiple related domains',
      color: 'green'
    };
    return { 
      level: 'Breadth Focus', 
      description: 'Survey knowledge across many domains with easier questions',
      color: 'orange'
    };
  };

  const adaptiveInfo = getAdaptiveInfo();

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Select Your Assessment Domains
        </h1>
        <p className="text-gray-400">
          Choose at least one domain. Multiple selections create adaptive assessments.
        </p>
      </div>

      {/* Adaptive Mode Indicator */}
      {selectedDomains.length > 0 && (
        <div className={`mb-6 p-4 rounded-lg border-2 bg-${adaptiveInfo.color}-500/10 border-${adaptiveInfo.color}-500/30`}>
          <div className="flex items-center gap-3">
            <Brain className={`w-6 h-6 text-${adaptiveInfo.color}-400`} />
            <div>
              <h3 className={`font-semibold text-${adaptiveInfo.color}-400`}>
                {adaptiveInfo.level} Mode
              </h3>
              <p className="text-sm text-gray-400">{adaptiveInfo.description}</p>
            </div>
          </div>
          <div className="mt-3 text-sm text-gray-400">
            <strong>{selectedDomains.length}</strong> domain{selectedDomains.length !== 1 ? 's' : ''} selected
          </div>
        </div>
      )}

      {/* Domain Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {Object.values(DOMAINS).map((domain) => {
          const Icon = ICON_MAP[domain.icon] || Cpu;
          const isSelected = selectedDomains.includes(domain.id);
          const colorClass = COLOR_MAP[domain.color] || COLOR_MAP.blue;
          const questionCount = questionCounts[domain.name] || 0;

          return (
            <button
              key={domain.id}
              onClick={() => toggleDomain(domain.id)}
              className={`
                relative p-5 rounded-xl border-2 transition-all duration-200
                ${isSelected 
                  ? colorClass + ' ring-2 ring-offset-2 ring-offset-gray-900 transform scale-105' 
                  : 'bg-gray-800/30 border-gray-700 text-gray-400 hover:bg-gray-800/50 hover:border-gray-600'
                }
              `}
            >
              {/* Selection Indicator */}
              <div className="absolute top-3 right-3">
                {isSelected ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <Circle className="w-5 h-5 opacity-30" />
                )}
              </div>

              {/* Icon */}
              <div className="flex justify-center mb-3">
                <Icon className="w-10 h-10" />
              </div>

              {/* Domain Name */}
              <h3 className="font-semibold text-center mb-1">
                {domain.name}
              </h3>

              {/* Full Name */}
              <p className="text-xs text-center opacity-70 mb-2">
                {domain.fullName}
              </p>

              {/* Question Count */}
              {questionCount > 0 && (
                <div className="text-xs text-center opacity-50">
                  {questionCount} questions
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Continue Button */}
      <div className="flex justify-center">
        <button
          onClick={handleContinue}
          disabled={selectedDomains.length === 0}
          className={`
            px-8 py-3 rounded-lg font-semibold transition-all duration-200
            ${selectedDomains.length > 0
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          Continue to Assessment
          {selectedDomains.length > 0 && ` (${selectedDomains.length} domain${selectedDomains.length !== 1 ? 's' : ''})`}
        </button>
      </div>

      {/* Domain Count Info */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>💡 Select more domains for broader knowledge assessment</p>
        <p>💡 Select fewer domains for deeper, more challenging questions</p>
      </div>
    </div>
  );
}
