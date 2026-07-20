import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { fieldBasedQuestionService } from '../lib/fieldBasedQuestionService';
import { CheckCircle, XCircle, AlertCircle, Play } from 'lucide-react';

export default function ApiTest() {
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);

  const runSystemTest = async () => {
    setTesting(true);
    setTestResults(null);
    
    const results = {
      questionBanks: null,
      fieldDetection: null,
      questionGeneration: null,
      errors: []
    };

    try {
      // Test 1: Question bank availability
      console.log('🔧 Step 1: Checking question bank availability...');
      try {
        const summary = await fieldBasedQuestionService.getQuestionBankSummary();
        const totalQuestions = Object.values(summary).reduce((total, categories) => {
          return total + Object.values(categories).reduce((sum, count) => sum + count, 0);
        }, 0);
        
        if (totalQuestions > 0) {
          results.questionBanks = { 
            success: true, 
            message: `${totalQuestions} questions available across ${Object.keys(summary).length} categories`
          };
        } else {
          results.questionBanks = { success: false, message: 'No questions found in question banks' };
          results.errors.push('Question banks are empty');
        }
      } catch (error) {
        results.questionBanks = { success: false, message: error.message };
        results.errors.push(`Question Banks: ${error.message}`);
      }

      // Test 2: Field detection
      if (results.questionBanks?.success) {
        console.log('🔧 Step 2: Testing field detection...');
        try {
          const testStudentData = {
            field_of_study: 'Computer Science',
            current_skills: 'JavaScript, Python',
            interests: 'Web development, AI',
            goals: 'Become a software engineer'
          };
          
          const questions = await fieldBasedQuestionService.generateQuestionsForStudent(testStudentData, 5);
          
          if (questions && questions.length > 0) {
            results.fieldDetection = { 
              success: true, 
              message: `Generated ${questions.length} field-appropriate questions`,
              sample: questions[0]?.question_text?.substring(0, 100) + '...'
            };
          } else {
            results.fieldDetection = { success: false, message: 'No questions generated for test profile' };
            results.errors.push('Field-based question generation failed');
          }
        } catch (error) {
          results.fieldDetection = { success: false, message: error.message };
          results.errors.push(`Field Detection: ${error.message}`);
        }
      }

      // Test 3: Question generation for different fields
      if (results.fieldDetection?.success) {
        console.log('🔧 Step 3: Testing question generation for different fields...');
        try {
          const testFields = [
            { field_of_study: 'Business Administration' },
            { field_of_study: 'Psychology' },
            { field_of_study: 'Medicine' }
          ];
          
          let allFieldsWork = true;
          const fieldResults = [];
          
          for (const testData of testFields) {
            try {
              const questions = await fieldBasedQuestionService.generateQuestionsForStudent(testData, 3);
              fieldResults.push({ field: testData.field_of_study, count: questions.length });
              if (questions.length === 0) allFieldsWork = false;
            } catch (error) {
              fieldResults.push({ field: testData.field_of_study, error: error.message });
              allFieldsWork = false;
            }
          }
          
          if (allFieldsWork) {
            results.questionGeneration = { 
              success: true, 
              message: `All test fields generated questions successfully`,
              details: fieldResults
            };
          } else {
            results.questionGeneration = { 
              success: false, 
              message: 'Some fields failed to generate questions',
              details: fieldResults
            };
            results.errors.push('Question generation inconsistent across fields');
          }
        } catch (error) {
          results.questionGeneration = { success: false, message: error.message };
          results.errors.push(`Question Generation: ${error.message}`);
        }
      }

      setTestResults(results);
      
      if (results.errors.length === 0) {
        toast.success('All system tests passed! 🎉');
      } else {
        toast.error(`${results.errors.length} test(s) failed`);
      }
      
    } catch (error) {
      console.error('Test suite failed:', error);
      toast.error('Test suite failed: ' + error.message);
      setTestResults({
        questionBanks: { success: false, message: 'Test suite failed' },
        fieldDetection: null,
        questionGeneration: null,
        errors: [error.message]
      });
    } finally {
      setTesting(false);
    }
  };

  const TestResult = ({ title, result, icon: Icon }) => {
    if (!result) return null;
    
    return (
      <div className={`p-4 rounded-lg border ${
        result.success 
          ? 'border-green-500/30 bg-green-500/10' 
          : 'border-red-500/30 bg-red-500/10'
      }`}>
        <div className="flex items-center gap-3 mb-2">
          <Icon className={`h-5 w-5 ${result.success ? 'text-green-400' : 'text-red-400'}`} />
          <span className="font-medium text-white">{title}</span>
        </div>
        <div className={`text-sm ${result.success ? 'text-green-300' : 'text-red-300'}`}>
          {result.message}
        </div>
        {result.sample && (
          <div className="mt-2 text-xs text-white/60 bg-white/5 p-2 rounded">
            Sample: {result.sample}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold text-white">Field-Based Assessment Test Suite</h2>
        <p className="text-white/70">
          Test the field-based question system to ensure all components are working correctly
        </p>
        
        <button
          onClick={runSystemTest}
          disabled={testing}
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
        >
          <Play className="h-4 w-4" />
          {testing ? 'Running Tests...' : 'Run System Tests'}
        </button>
      </div>

      {testing && (
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <div className="text-white/70">Testing field-based question system...</div>
        </div>
      )}

      {testResults && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Test Results</h3>
          
          <TestResult
            title="Question Bank Availability"
            result={testResults.questionBanks}
            icon={testResults.questionBanks?.success ? CheckCircle : XCircle}
          />
          
          <TestResult
            title="Field Detection & Question Selection"
            result={testResults.fieldDetection}
            icon={testResults.fieldDetection?.success ? CheckCircle : XCircle}
          />
          
          <TestResult
            title="Multi-Field Question Generation"
            result={testResults.questionGeneration}
            icon={testResults.questionGeneration?.success ? CheckCircle : XCircle}
          />
          
          {testResults.errors.length > 0 && (
            <div className="p-4 rounded-lg border border-orange-500/30 bg-orange-500/10">
              <div className="flex items-center gap-3 mb-2">
                <AlertCircle className="h-5 w-5 text-orange-400" />
                <span className="font-medium text-white">Issues Found</span>
              </div>
              <ul className="text-sm text-orange-300 space-y-1">
                {testResults.errors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="p-4 rounded-lg bg-white/5 border border-white/10">
            <div className="text-sm font-medium text-white/90 mb-2">System Status:</div>
            <ul className="text-xs text-white/70 space-y-1">
              <li>• Field-based question system active</li>
              <li>• No external API dependencies</li>
              <li>• Instant question generation</li>
              <li>• Check browser console for detailed logs</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
