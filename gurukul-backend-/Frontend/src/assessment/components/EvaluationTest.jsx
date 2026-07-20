import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { scoringService } from '../lib/scoringService';
import { Play, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export default function EvaluationTest() {
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);

  const sampleQuestion = {
    id: 'test-q1',
    category: 'Coding',
    difficulty: 'medium',
    question_text: 'What is the time complexity of binary search in a sorted array?',
    options: ['A) O(n)', 'B) O(log n)', 'C) O(n log n)', 'D) O(1)'],
    correct_answer: 'B) O(log n)',
    explanation: 'Binary search divides the search space in half with each comparison, resulting in logarithmic time complexity.',
    vedic_connection: '',
    modern_application: 'Binary search is fundamental in computer science and used in databases, search engines, and optimization algorithms.'
  };

  const testCases = [
    {
      name: 'Correct Answer with Excellent Explanation',
      userAnswer: 'B) O(log n)',
      userExplanation: 'Binary search works by repeatedly dividing the search space in half. Since we eliminate half of the remaining elements with each comparison, the maximum number of comparisons needed is log base 2 of n, therefore the time complexity is O(log n).'
    },
    {
      name: 'Correct Answer with Basic Explanation',
      userAnswer: 'B) O(log n)',
      userExplanation: 'Binary search divides the array in half each time, so it is log n.'
    },
    {
      name: 'Correct Answer with Minimal Explanation',
      userAnswer: 'B) O(log n)',
      userExplanation: 'It is log n because of halving.'
    },
    {
      name: 'Wrong Answer with Good Reasoning',
      userAnswer: 'A) O(n)',
      userExplanation: 'I believe we need to check each element in the worst case to find the target, therefore it should be linear time complexity O(n).'
    },
    {
      name: 'Wrong Answer with Poor Explanation',
      userAnswer: 'D) O(1)',
      userExplanation: 'I think it is constant time.'
    },
    {
      name: 'Wrong Answer with No Explanation',
      userAnswer: 'C) O(n log n)',
      userExplanation: ''
    }
  ];

  const runEvaluationTest = async () => {
    setTesting(true);
    setTestResults(null);
    
    const results = {
      scoringServiceTest: null,
      testCaseResults: [],
      performanceTest: null,
      errors: []
    };

    try {
      toast.loading('Testing field-based evaluation system...');

      // Test 1: Basic Scoring Service functionality
      console.log('\n🧪 === Testing Field-Based Scoring Service ===');
      try {
        const basicEvaluation = await scoringService.evaluateResponse(
          sampleQuestion,
          'B) O(log n)',
          'Binary search divides the array in half each time, leading to logarithmic complexity.'
        );
        
        results.scoringServiceTest = {
          success: true,
          data: basicEvaluation,
          message: 'Field-based scoring service working correctly'
        };
        console.log('✅ Basic scoring service test passed');
      } catch (error) {
        results.scoringServiceTest = {
          success: false,
          error: error.message,
          message: 'Scoring service evaluation failed'
        };
        results.errors.push(`Scoring Service: ${error.message}`);
        console.error('❌ Basic scoring service test failed:', error);
      }

      // Test 2: Multiple test cases with different scenarios
      console.log('\n🧪 === Testing Multiple Evaluation Scenarios ===');
      for (let i = 0; i < testCases.length; i++) {
        const testCase = testCases[i];
        console.log(`\n📝 Testing: ${testCase.name}`);
        
        try {
          const result = await scoringService.evaluateResponse(
            sampleQuestion,
            testCase.userAnswer,
            testCase.userExplanation
          );
          
          results.testCaseResults.push({
            name: testCase.name,
            success: true,
            input: testCase,
            output: result,
            message: `Accuracy: ${result.accuracy_score}/10, Explanation: ${result.explanation_score}/10, Reasoning: ${result.reasoning_score}/10`
          });
          
          console.log(`✅ ${testCase.name} completed`);
          
        } catch (error) {
          results.testCaseResults.push({
            name: testCase.name,
            success: false,
            input: testCase,
            error: error.message,
            message: 'Evaluation failed'
          });
          
          results.errors.push(`${testCase.name}: ${error.message}`);
          console.error(`❌ ${testCase.name} failed:`, error);
        }
      }

      // Test 3: Performance test
      console.log('\n🧪 === Testing Performance ===');
      try {
        const startTime = Date.now();
        
        // Run 5 evaluations simultaneously to test performance
        const performancePromises = Array(5).fill(null).map(() => 
          scoringService.evaluateResponse(
            sampleQuestion,
            'B) O(log n)',
            'Binary search has logarithmic time complexity.'
          )
        );
        
        await Promise.all(performancePromises);
        const endTime = Date.now();
        const totalTime = endTime - startTime;
        
        results.performanceTest = {
          success: true,
          message: `5 evaluations completed in ${totalTime}ms (avg: ${Math.round(totalTime/5)}ms per evaluation)`,
          totalTime,
          averageTime: Math.round(totalTime/5)
        };
        
        console.log('✅ Performance test passed');
      } catch (error) {
        results.performanceTest = {
          success: false,
          error: error.message,
          message: 'Performance test failed'
        };
        results.errors.push(`Performance: ${error.message}`);
        console.error('❌ Performance test failed:', error);
      }

      setTestResults(results);
      
      if (results.errors.length === 0) {
        toast.success('All evaluation tests passed! 🎉');
      } else {
        toast.error(`${results.errors.length} test(s) failed`);
      }
      
    } catch (error) {
      console.error('Test suite failed:', error);
      toast.error('Test suite failed: ' + error.message);
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
        <div className={`text-sm ${result.success ? 'text-green-300' : 'text-red-300'} mb-2`}>
          {result.message}
        </div>
        {result.data && (
          <div className="text-xs text-white/60 bg-white/5 p-2 rounded">
            <pre>{JSON.stringify(result.data, null, 2)}</pre>
          </div>
        )}
        {result.error && (
          <div className="text-xs text-red-300 bg-red-500/10 p-2 rounded">
            Error: {result.error}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold text-white">Field-Based Evaluation Test</h2>
        <p className="text-white/70">
          Test the field-based scoring system to ensure accurate and fast evaluation
        </p>
        
        <button
          onClick={runEvaluationTest}
          disabled={testing}
          className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
        >
          <Play className="h-4 w-4" />
          {testing ? 'Running Tests...' : 'Test Evaluation Pipeline'}
        </button>
      </div>

      {testing && (
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto"></div>
          <div className="text-white/70">Testing evaluation pipeline...</div>
          <div className="text-sm text-white/60">Check console for detailed logs</div>
        </div>
      )}

      {testResults && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-white">Test Results</h3>
          
          <div className="grid gap-4 md:grid-cols-2">
            <TestResult
              title="Field-Based Scoring Service"
              result={testResults.scoringServiceTest}
              icon={testResults.scoringServiceTest?.success ? CheckCircle : XCircle}
            />
            
            <TestResult
              title="Performance Test"
              result={testResults.performanceTest}
              icon={testResults.performanceTest?.success ? CheckCircle : XCircle}
            />
          </div>
          
          <div className="space-y-3">
            <h4 className="font-medium text-white">Test Case Results</h4>
            {testResults.testCaseResults.map((result, index) => (
              <TestResult
                key={index}
                title={result.name}
                result={result}
                icon={result.success ? CheckCircle : XCircle}
              />
            ))}
          </div>
          
          {testResults.errors.length > 0 && (
            <div className="p-4 rounded-lg border border-orange-500/30 bg-orange-500/10">
              <div className="flex items-center gap-3 mb-2">
                <AlertTriangle className="h-5 w-5 text-orange-400" />
                <span className="font-medium text-white">Issues Found</span>
              </div>
              <ul className="text-sm text-orange-300 space-y-1">
                {testResults.errors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
