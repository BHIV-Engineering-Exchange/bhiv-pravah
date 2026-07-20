import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { fieldBasedQuestionService } from '../lib/fieldBasedQuestionService';
import { ASSIGNMENT_CATEGORIES, DIFFICULTY_LEVELS } from '../data/assignment';
import { Play, Clock, CheckCircle, XCircle } from 'lucide-react';

export default function RateLimitTest() {
  const [testing, setTesting] = useState(false);
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState(0);

  const runPerformanceTest = async () => {
    setTesting(true);
    setResults([]);
    setProgress(0);
    
    const testResults = [];
    const testCases = [
      { field: 'Computer Science', category: 'Coding', difficulty: 'medium' },
      { field: 'Mathematics', category: 'Mathematics', difficulty: 'hard' },
      { field: 'Psychology', category: 'Logic', difficulty: 'easy' }
    ];
    
    try {
      toast.loading('Testing field-based question generation performance...');
      
      for (let i = 0; i < testCases.length; i++) {
        const testCase = testCases[i];
        const startTime = Date.now();
        
        try {
          console.log(`🧪 Testing ${testCase.field} question generation...`);
          setProgress(((i) / testCases.length) * 100);
          
          // Create mock student data
          const mockStudent = {
            field_of_study: testCase.field,
            education_level: 'Bachelor',
            current_skills: [testCase.field],
            interests: [testCase.field]
          };
          
          const questions = await fieldBasedQuestionService.generateQuestionsForStudent(mockStudent, 5);
          const endTime = Date.now();
          const duration = endTime - startTime;
          
          testResults.push({
            field: testCase.field,
            success: true,
            duration,
            message: `Generated ${questions.length} questions in ${duration}ms`,
            questions: questions.length,
            averagePerQuestion: Math.round(duration / questions.length)
          });
          
          console.log(`✅ ${testCase.field} test completed in ${duration}ms`);
          
        } catch (error) {
          const endTime = Date.now();
          const duration = endTime - startTime;
          
          testResults.push({
            field: testCase.field,
            success: false,
            duration,
            message: error.message,
            error: true
          });
          
          console.error(`❌ ${testCase.field} test failed:`, error);
        }
        
        setResults([...testResults]);
        
        // Small delay to show progress
        if (i < testCases.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }
      
      setProgress(100);
      toast.success('Performance test completed!');
      
    } catch (error) {
      console.error('Test suite failed:', error);
      toast.error('Test suite failed: ' + error.message);
    } finally {
      setTesting(false);
    }
  };

  const TestResult = ({ result }) => {
    const Icon = result.success ? CheckCircle : XCircle;
    const colorClass = result.success ? 'text-green-400' : 'text-red-400';
    const bgClass = result.success ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30';
    
    return (
      <div className={`p-4 rounded-lg border ${bgClass}`}>
        <div className="flex items-center gap-3 mb-2">
          <Icon className={`h-5 w-5 ${colorClass}`} />
          <span className="font-medium text-white">{result.field}</span>
          <div className="flex items-center gap-1 text-sm text-white/60">
            <Clock className="h-4 w-4" />
            <span>{result.duration}ms</span>
          </div>
        </div>
        <div className={`text-sm ${result.success ? 'text-green-300' : 'text-red-300'}`}>
          {result.message}
        </div>
        {result.questions && (
          <div className="text-xs text-white/60 mt-1">
            Generated {result.questions} question(s) • Avg: {result.averagePerQuestion}ms per question
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-bold text-white">Field-Based Question Performance Test</h2>
        <p className="text-white/70">
          Test the performance of field-based question generation (should be instant!)
        </p>
        
        <button
          onClick={runPerformanceTest}
          disabled={testing}
          className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
        >
          <Play className="h-4 w-4" />
          {testing ? 'Running Test...' : 'Test Performance'}
        </button>
      </div>

      {testing && (
        <div className="space-y-4">
          <div className="text-center space-y-3">
            <div className="text-white/70">Testing in progress...</div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="text-sm text-purple-400">{Math.round(progress)}% Complete</div>
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Test Results</h3>
          <div className="space-y-3">
            {results.map((result, index) => (
              <TestResult key={index} result={result} />
            ))}
          </div>
          
          {results.length > 0 && !testing && (
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="text-sm font-medium text-white/90 mb-2">Analysis:</div>
              <ul className="text-xs text-white/70 space-y-1">
                <li>• Average response time: {Math.round(results.reduce((sum, r) => sum + r.duration, 0) / results.length)}ms</li>
                <li>• Success rate: {Math.round((results.filter(r => r.success).length / results.length) * 100)}%</li>
                <li>• Field-based generation is {results.every(r => r.duration < 100) ? 'extremely fast' : 'performing well'}</li>
                <li>• Total questions generated: {results.reduce((sum, r) => sum + (r.questions || 0), 0)}</li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
