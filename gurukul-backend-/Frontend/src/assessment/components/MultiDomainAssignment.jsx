import { useState } from 'react';
import DomainSelector from './DomainSelector';
import Assignment from './Assignment';
import MultiDomainResults from './MultiDomainResults';
import MultiDomainAssessmentService from '../lib/multiDomainAssessmentService';
import AIAssistanceDetector from '../lib/aiAssistanceDetector';

/**
 * Multi-Domain Assessment Wrapper
 * 
 * Flow:
 * 1. Domain Selection → Student picks domains
 * 2. Assessment → Questions from selected domains
 * 3. Results → Performance breakdown with AI detection
 */
export default function MultiDomainAssignment({ userId, userEmail, onComplete }) {
  const [stage, setStage] = useState('domain_selection'); // 'domain_selection' | 'assessment' | 'results'
  const [selectedDomains, setSelectedDomains] = useState([]);
  const [assessmentData, setAssessmentData] = useState(null);
  const [resultsData, setResultsData] = useState(null);

  /**
   * Handle domain selection completion
   */
  const handleDomainsSelected = async (domains) => {
    console.log('✅ Domains selected:', domains);
    setSelectedDomains(domains);
    
    try {
      // Generate multi-domain assessment
      const assessment = await MultiDomainAssessmentService.generateMultiDomainAssessment(
        domains,
        20, // Total questions
        userId || 'guest'
      );
      
      console.log('📝 Generated assessment:', assessment);
      setAssessmentData(assessment);
      setStage('assessment');
      
    } catch (error) {
      console.error('❌ Error generating assessment:', error);
      alert('Failed to generate assessment. Please try again.');
    }
  };

  /**
   * Handle assessment completion
   */
  const handleAssessmentComplete = async (results) => {
    console.log('✅ Assessment completed:', results);
    
    try {
      // Analyze responses for AI assistance
      const aiAnalysis = AIAssistanceDetector.analyzeMultipleResponses(
        results.userAnswers,
        results.questions,
        results.timeSpent || []
      );
      
      console.log('🤖 AI Detection results:', aiAnalysis);
      
      // Combine results with AI analysis
      const enhancedResults = {
        ...results,
        aiDetection: aiAnalysis,
        selectedDomains,
        assessmentMetadata: assessmentData?.metadata
      };
      
      setResultsData(enhancedResults);
      setStage('results');
      
    } catch (error) {
      console.error('❌ Error processing results:', error);
      setResultsData(results);
      setStage('results');
    }
  };

  /**
   * Handle retake
   */
  const handleRetake = () => {
    setStage('domain_selection');
    setSelectedDomains([]);
    setAssessmentData(null);
    setResultsData(null);
  };

  /**
   * Render based on current stage
   */
  if (stage === 'domain_selection') {
    return (
      <DomainSelector
        onDomainsSelected={handleDomainsSelected}
        userId={userId}
      />
    );
  }

  if (stage === 'assessment') {
    return (
      <Assignment
        onComplete={handleAssessmentComplete}
        userId={userId}
        userEmail={userEmail}
        preloadedQuestions={assessmentData?.questions} // Pass pre-generated questions
        assessmentMetadata={assessmentData?.metadata} // Pass metadata for context
      />
    );
  }

  if (stage === 'results') {
    return (
      <MultiDomainResults
        results={resultsData}
        questions={assessmentData?.questions || []}
        userResponses={resultsData?.userAnswers || {}}
        onRetake={handleRetake}
        onDashboard={() => onComplete && onComplete(resultsData)}
      />
    );
  }

  return null;
}
