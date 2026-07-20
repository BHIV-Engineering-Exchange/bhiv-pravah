import React, { useState } from 'react';
import { 
  Brain, Search, MessageSquare, Sparkles, Loader2, 
  AlertCircle, CheckCircle, RefreshCw, Lightbulb
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import Button from '../components/common/ui/Button';
import Input from '../components/common/forms/Input';
import Alert from '../components/common/ui/Alert';
import Badge from '../components/common/ui/Badge';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { llmQueryAPI } from '../services/api/llmQueryAPI';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/common/ui/Table';

export const AIQuery = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [currentResult, setCurrentResult] = useState(null);

  const exampleQueries = [
    'Show me all opportunities closing this month',
    'What are the pending tasks for TechCorp?',
    'Show me leads from website that are not converted',
    'Give me account summary for Acme Corp',
    'What is the pipeline analysis?',
    'Show recent activities',
  ];

  const handleQuery = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setCurrentResult(null);

      const response = await llmQueryAPI.processQuery(query);
      const result = response.data;

      setCurrentResult(result);
      
      // Add to history
      setQueryHistory(prev => [{
        id: Date.now(),
        query: query,
        timestamp: new Date(),
        result: result
      }, ...prev].slice(0, 10)); // Keep last 10 queries

      setQuery('');
    } catch (err) {
      console.error('Error processing query:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to process query');
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  const renderQueryResult = () => {
    if (!currentResult) return null;

    const result = currentResult.result || {};
    const naturalResponse = currentResult.natural_response || '';
    const queryType = result.query_type || 'unknown';
    const data = result.data || [];

    return (
      <div className="space-y-4">
        {/* Natural Language Response */}
        {naturalResponse && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                AI Response
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground whitespace-pre-wrap">{naturalResponse}</p>
            </CardContent>
          </Card>
        )}

        {/* Query Result Data */}
        {Array.isArray(data) && data.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                Results ({data.length} {data.length === 1 ? 'item' : 'items'})
                <Badge variant="outline" className="ml-2">
                  {queryType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  {Object.keys(data[0] || {}).length > 0 && (
                    <TableRow>
                      {Object.keys(data[0]).map((key) => (
                        <TableHead key={key}>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</TableHead>
                      ))}
                    </TableRow>
                  )}
                </TableHeader>
                <TableBody>
                  {data.map((item, index) => (
                    <TableRow key={index}>
                      {Object.entries(item).map(([key, value]) => (
                        <TableCell key={key}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        {/* Object Result */}
        {!Array.isArray(data) && typeof data === 'object' && Object.keys(data).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                Query Result
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                {JSON.stringify(data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* No Results */}
        {(!data || (Array.isArray(data) && data.length === 0) || (typeof data === 'object' && Object.keys(data).length === 0)) && (
          <Card>
            <CardContent className="pt-6 text-center py-12">
              <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No data found for your query.</p>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight">AI Query</h1>
          <p className="text-muted-foreground mt-1">
            Ask natural language questions about your CRM data
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => {
          setQuery('');
          setCurrentResult(null);
          setError(null);
        }}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Clear
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" onClose={() => setError(null)}>
          <AlertCircle className="h-4 w-4 mr-2" />
          {error}
        </Alert>
      )}

      {/* Query Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            Natural Language Query
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Ask a question about your CRM data... (e.g., Show me all opportunities closing this month)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleQuery()}
              icon={Search}
              className="flex-1"
            />
            <Button onClick={handleQuery} disabled={loading || !query.trim()}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Query
                </>
              )}
            </Button>
          </div>

          {/* Example Queries */}
          <div>
            <p className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Example queries:
            </p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((example, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleExampleClick(example)}
                  className="text-xs"
                >
                  {example}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <LoadingSpinner text="Processing your query..." />
          </CardContent>
        </Card>
      )}

      {/* Query Results */}
      {!loading && currentResult && renderQueryResult()}

      {/* Query History */}
      {queryHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              Recent Queries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {queryHistory.map((historyItem) => (
                <div
                  key={historyItem.id}
                  className="p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => {
                    setQuery(historyItem.query);
                    setCurrentResult(historyItem.result);
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{historyItem.query}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {historyItem.timestamp.toLocaleString()}
                      </p>
                    </div>
                    {historyItem.result?.result?.success && (
                      <CheckCircle className="h-4 w-4 text-success" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AIQuery;

