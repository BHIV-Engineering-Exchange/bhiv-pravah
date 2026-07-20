import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { schoolAdminAPI } from '../../services/api';

const AdminStudentContent = () => {
  const { studentId } = useParams();
  const [activeTab, setActiveTab] = useState('all');
  const [summaries, setSummaries] = useState([]);
  const [flashcards, setFlashcards] = useState([]);
  const [testResults, setTestResults] = useState([]);
  const [subjectData, setSubjectData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (studentId) {
      fetchAllContent();
    }
  }, [studentId]);

  const fetchAllContent = async () => {
    try {
      setLoading(true);
      setError('');
      const [summariesData, flashcardsData, testResultsData, subjectDataData] = await Promise.all([
        schoolAdminAPI.getStudentSummaries(studentId),
        schoolAdminAPI.getStudentFlashcards(studentId),
        schoolAdminAPI.getStudentTestResults(studentId),
        schoolAdminAPI.getStudentSubjectData(studentId)
      ]);
      setSummaries(summariesData || []);
      setFlashcards(flashcardsData || []);
      setTestResults(testResultsData || []);
      setSubjectData(subjectDataData || []);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load content';
      setError(`Failed to load content: ${errorMessage}`);
      console.error('Error fetching content:', err);
    } finally {
      setLoading(false);
    }
  };

  const totalItems = summaries.length + flashcards.length + testResults.length + subjectData.length;

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading content...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box p-6">
        <p className="text-red-400">{error}</p>
        <button
          data-ems-interaction="true"
          onClick={fetchAllContent}
          className="mt-4 px-4 py-2 bg-red-600/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-600/30 transition text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Student Generated Content</h1>
        <button
          data-ems-interaction="true"
          onClick={fetchAllContent}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-[#2A2A3E]">
        <nav className="-mb-px flex space-x-8">
          {['all', 'summaries', 'flashcards', 'tests', 'subjects'].map((tab) => (
            <button
              key={tab}
              data-ems-interaction="true"
              onClick={() => setActiveTab(tab)}
              className={`${
                activeTab === tab
                  ? 'border-accent-green text-accent-green'
                  : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-[#2A2A3E]'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize`}
            >
              {tab === 'all' ? `All (${totalItems})` : 
               tab === 'summaries' ? `Summaries (${summaries.length})` :
               tab === 'flashcards' ? `Flashcards (${flashcards.length})` :
               tab === 'tests' ? `Tests (${testResults.length})` :
               `Subjects (${subjectData.length})`}
            </button>
          ))}
        </nav>
      </div>

      {/* Content - Same structure as other content components */}
      <div className="space-y-6">
        {(activeTab === 'all' || activeTab === 'summaries') && summaries.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Summaries ({summaries.length})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {summaries.map((summary) => (
                <div key={summary.id} className="card-dark p-6 border border-[#2A2A3E]">
                  <h3 className="text-lg font-semibold text-white mb-2">{summary.title}</h3>
                  <p className="text-sm text-gray-400 mb-2 line-clamp-3">{summary.content}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-4">
                    <span>Source: {summary.source || 'Manual'}</span>
                    <span>{new Date(summary.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(activeTab === 'all' || activeTab === 'flashcards') && flashcards.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Flashcards ({flashcards.length})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {flashcards.map((flashcard) => (
                <div key={flashcard.id} className="card-dark p-6 border border-[#2A2A3E]">
                  <div className="mb-4">
                    <p className="font-medium text-white mb-2">Q: {flashcard.question}</p>
                    <p className="text-sm text-gray-300">A: {flashcard.answer}</p>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-4">
                    <span>Confidence: {flashcard.confidence.toFixed(1)}%</span>
                    <span>{new Date(flashcard.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(activeTab === 'all' || activeTab === 'tests') && testResults.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Test Results ({testResults.length})</h2>
            <div className="space-y-4">
              {testResults.map((test) => (
                <div key={test.id} className="card-dark p-6 border border-[#2A2A3E]">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{test.subject} - {test.topic}</h3>
                      <p className="text-sm text-gray-400 mt-1">
                        {test.correct_answers}/{test.total_questions} correct
                      </p>
                    </div>
                    <div className={`px-4 py-2 rounded-lg font-semibold ${
                      test.score_percentage >= 80 ? 'bg-green-100 text-accent-green' :
                      test.score_percentage >= 60 ? 'bg-accent-amber/15 text-accent-amber' :
                      'bg-red-100 text-red-400'
                    }`}>
                      {test.score_percentage.toFixed(1)}%
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Difficulty: {test.difficulty || 'N/A'}</span>
                    <span>{new Date(test.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(activeTab === 'all' || activeTab === 'subjects') && subjectData.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Subject Explorer ({subjectData.length})</h2>
            <div className="space-y-4">
              {subjectData.map((data) => (
                <div key={data.id} className="card-dark p-6 border border-[#2A2A3E]">
                  <h3 className="text-lg font-semibold text-white mb-2">{data.subject} - {data.topic}</h3>
                  <p className="text-sm text-gray-300 mb-4 line-clamp-4">{data.notes}</p>
                  {data.youtube_recommendations && data.youtube_recommendations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-[#2A2A3E]">
                      <p className="text-xs font-medium text-gray-400 mb-2">YouTube Recommendations:</p>
                      <ul className="list-disc list-inside text-xs text-gray-400">
                        {data.youtube_recommendations.slice(0, 3).map((rec, idx) => (
                          <li key={idx}>{rec.title || rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-4">
                    <span>Provider: {data.provider || 'N/A'}</span>
                    <span>{new Date(data.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {totalItems === 0 && (
          <div className="card-dark p-12 text-center">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-semibold text-white mb-2">No Content Generated Yet</h2>
            <p className="text-gray-400">This student hasn't generated any content in Gurukul yet.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminStudentContent;

