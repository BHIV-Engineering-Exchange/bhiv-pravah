import React, { useState, useEffect, useCallback } from 'react';
import { 
  Bot, Play, Pause, RefreshCw, Settings, Activity, 
  TrendingUp, Zap, CheckCircle, AlertCircle, Clock, AlertTriangle
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import MetricCard from '../components/common/charts/MetricCard';
import Button from '../components/common/ui/Button';
import Badge from '../components/common/ui/Badge';
import { Alert } from '../components/common/ui/Alert';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/common/ui/Table';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { agentAPI } from '../services/api/agentAPI';
import { logisticsAPI } from '../services/api/logisticsAPI';
import { formatRelativeTime } from '@/utils/dateUtils';

export const Agents = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [agents, setAgents] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [metrics, setMetrics] = useState({
    totalAgents: 0,
    activeAgents: 0,
    pausedAgents: 0,
    totalActions: 0,
    successRate: 0,
  });

  // Fetch agent data
  const fetchAgentData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch agents
      try {
        const agentsResponse = await agentAPI.getAgents();
        const agentsData = agentsResponse.data?.agents || agentsResponse.data || [];
        setAgents(agentsData.map(agent => ({
          id: agent.id || agent.agent_id,
          name: agent.name || agent.agent_name || 'Unknown Agent',
          type: agent.type || agent.agent_type || 'general',
          status: agent.status || 'active',
          description: agent.description || agent.purpose || 'No description',
          lastRun: agent.last_run ? new Date(agent.last_run) : new Date(),
          actionsToday: agent.actions_today || agent.actions_count || 0,
          successRate: parseFloat(agent.success_rate || 0),
          avgExecutionTime: agent.avg_execution_time || '0s',
        })));

        // Calculate metrics
        const totalAgents = agentsData.length;
        const activeAgents = agentsData.filter(a => (a.status || 'active') === 'active').length;
        const pausedAgents = agentsData.filter(a => (a.status || 'active') === 'paused').length;
        const totalActions = agentsData.reduce((sum, a) => sum + (a.actions_today || 0), 0);
        const avgSuccessRate = agentsData.length > 0 
          ? agentsData.reduce((sum, a) => sum + parseFloat(a.success_rate || 0), 0) / agentsData.length 
          : 0;

        setMetrics({
          totalAgents,
          activeAgents,
          pausedAgents,
          totalActions,
          successRate: Math.round(avgSuccessRate * 10) / 10,
        });
      } catch (err) {
        console.warn('Failed to fetch agents:', err);
        // Try alternative endpoint
        try {
          const statusResponse = await fetch('/api/agent/status');
          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            // Transform status data to agents format
          }
        } catch (e) {
          console.warn('Alternative endpoint also failed:', e);
        }
      }

      // Fetch agent logs
      try {
        const logsResponse = await logisticsAPI.getAgentLogs({ limit: 100 });
        const logsData = logsResponse.data?.logs || logsResponse.data || [];
        setAgentLogs(logsData.map(log => ({
          id: log.id || log.log_id,
          agent: log.agent || log.agent_name || 'Unknown',
          action: log.action || log.message || 'Action performed',
          status: log.status || 'success',
          timestamp: log.timestamp ? new Date(log.timestamp) : new Date(),
        })));
      } catch (err) {
        console.warn('Failed to fetch agent logs:', err);
        // Try agentAPI logs endpoint
        try {
          const agentLogsResponse = await agentAPI.getAgentLogs({ limit: 100 });
          const agentLogsData = agentLogsResponse.data?.logs || agentLogsResponse.data || [];
          setAgentLogs(agentLogsData.map(log => ({
            id: log.id || log.log_id,
            agent: log.agent || log.agent_name || 'Unknown',
            action: log.action || log.message || 'Action performed',
            status: log.status || 'success',
            timestamp: log.timestamp ? new Date(log.timestamp) : new Date(),
          })));
        } catch (e) {
          console.warn('Agent logs endpoint also failed:', e);
        }
      }

    } catch (err) {
      console.error('Error fetching agent data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load agent data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgentData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAgentData();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchAgentData]);

  const getStatusVariant = (status) => {
    const variants = {
      active: 'success',
      paused: 'warning',
      error: 'destructive',
    };
    return variants[status] || 'default';
  };

  const handleRunAgent = async (agentId) => {
    try {
      setLoading(true);
      await agentAPI.triggerAgent(agentId, {});
      // Refresh data after triggering
      setTimeout(() => {
        fetchAgentData();
      }, 2000);
    } catch (error) {
      console.error('Error running agent:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to run agent');
    } finally {
      setLoading(false);
    }
  };

  const handlePauseAgent = async (agentId) => {
    try {
      setLoading(true);
      await agentAPI.pauseAgent(agentId);
      // Refresh data after pausing
      setTimeout(() => {
        fetchAgentData();
      }, 1000);
    } catch (error) {
      console.error('Error pausing agent:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to pause agent');
    } finally {
      setLoading(false);
    }
  };

  const handleResumeAgent = async (agentId) => {
    try {
      setLoading(true);
      await agentAPI.resumeAgent(agentId);
      // Refresh data after resuming
      setTimeout(() => {
        fetchAgentData();
      }, 1000);
    } catch (error) {
      console.error('Error resuming agent:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to resume agent');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading agents..." />;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight">AI Agents Control</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your AI agents
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchAgentData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button>
            <Settings className="h-4 w-4 mr-2" />
            Agent Settings
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" onClose={() => setError(null)}>
          <AlertTriangle className="h-4 w-4 mr-2" />
          {error}
        </Alert>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <MetricCard
          title="Total Agents"
          value={metrics.totalAgents.toLocaleString()}
          icon={Bot}
          variant="primary"
        />
        <MetricCard
          title="Active Agents"
          value={metrics.activeAgents.toLocaleString()}
          icon={Zap}
          variant="success"
        />
        <MetricCard
          title="Paused Agents"
          value={metrics.pausedAgents.toLocaleString()}
          icon={Pause}
          variant="warning"
        />
        <MetricCard
          title="Total Actions"
          value={metrics.totalActions.toLocaleString()}
          icon={Activity}
          variant="accent"
        />
        <MetricCard
          title="Success Rate"
          value={`${metrics.successRate}%`}
          icon={TrendingUp}
          variant="success"
        />
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <Card key={agent.id} className="border-l-4 border-primary/50">
            <CardHeader>
              <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Bot className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{agent.id}</p>
                  </div>
                </div>
                <Badge variant={getStatusVariant(agent.status)}>
                  {agent.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">{agent.description}</p>
              
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Last Run:</span>
                  <span className="font-medium">{formatRelativeTime(agent.lastRun)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Actions Today:</span>
                  <span className="font-medium">{agent.actionsToday}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Success Rate:</span>
                  <span className="font-medium">{agent.successRate}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Avg Time:</span>
                  <span className="font-medium">{agent.avgExecutionTime}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {agent.status === 'active' ? (
                  <>
                    <Button 
                      size="sm" 
                      className="flex-1"
                      onClick={() => handleRunAgent(agent.id)}
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Run Now
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handlePauseAgent(agent.id)}
                    >
                      <Pause className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <Button 
                    size="sm" 
                    className="flex-1"
                    onClick={() => handleResumeAgent(agent.id)}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Resume
                  </Button>
                )}
                <Button variant="ghost" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Agent Activity Log */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Agent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agentLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-medium">{log.agent}</TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell>
                    <Badge variant={log.status === 'success' ? 'success' : 'warning'}>
                      {log.status === 'success' ? (
                        <CheckCircle className="h-3 w-3 mr-1" />
                      ) : (
                        <AlertCircle className="h-3 w-3 mr-1" />
                      )}
                      {log.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelativeTime(log.timestamp)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Agents;
