import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import api from "../lib/api";
import { Button } from "../components/ui/button";
import { CreateTaskDialog } from "../components/tasks/create-task-dialog";
import { 
  AlertCircle, 
  Users, 
  BarChart, 
  Zap, 
  TrendingUp, 
  Target,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  UserCheck,
  Activity,
  Flame
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Progress } from "../components/ui/progress";
import { Badge } from "../components/ui/badge";

export default function ProcurementDashboard() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const fetchAnalysis = async () => {
    try {
      const response = await api.procurement.runAnalysis();
      if (response.success) {
        setAnalysis(response.data);
      }
    } catch (error) {
      console.error('Error running procurement analysis:', error);
      setError(error.message || "Failed to run analysis");
    }
  };

  const handleRefreshAnalysis = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await fetchAnalysis();
      setSuccess("Analysis refreshed successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (error) {
      setError(error.message || "Failed to refresh analysis");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-8">
      {/* Header Section - Separated */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Procurement Agent</h1>
              <p className="text-muted-foreground">
                AI-powered employee availability analysis and task optimization
              </p>
            </div>
          </div>
          <Button
            onClick={handleRefreshAnalysis}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Refreshing..." : "Refresh Analysis"}
          </Button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Available Employees</p>
                <p className="text-2xl font-bold">{analysis?.availableEmployees?.length || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">Team Workload</p>
                <p className="text-2xl font-bold">{analysis?.teamWorkload || 0}%</p>
              </div>
            </div>
          </div>
          
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-sm text-muted-foreground">Low Task Employees</p>
                <p className="text-2xl font-bold">{analysis?.lowTaskEmployees?.length || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Low Task Alert - Enhanced with Glassmorphism */}
        {analysis?.lowTaskEmployees?.length > 0 && (
          <div className="space-y-4 bg-white/10 dark:bg-black/20 backdrop-blur-2xl border border-white/30 dark:border-white/10 rounded-3xl p-6 shadow-2xl animate-fade-in" 
            style={{backdropFilter: 'blur(20px)'}}>
            <div className="space-y-3">
              {/* Header Section */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1 h-10 w-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center flex-shrink-0 shadow-lg">
                    <AlertTriangle className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-orange-900 dark:text-orange-100">
                      🚨 Urgent: Low Task Alert
                    </h3>
                    <p className="text-sm text-orange-800 dark:text-orange-200 mt-1">
                      <span className="font-bold">{analysis.lowTaskEmployees.length} employee{analysis.lowTaskEmployees.length > 1 ? 's' : ''}</span> need{analysis.lowTaskEmployees.length > 1 ? '' : 's'} immediate task assignment
                    </p>
                  </div>
                </div>
                <Badge className="bg-gradient-to-r from-orange-500 to-red-500 text-white border-0 px-3 py-1 font-semibold text-xs">
                  PRIORITY
                </Badge>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-orange-700 dark:text-orange-300 font-medium">Alert Coverage</span>
                  <span className="text-orange-600 dark:text-orange-400">{analysis.lowTaskEmployees.length} of {analysis.lowTaskEmployees.length}</span>
                </div>
                <Progress 
                  value={100} 
                  className="h-2.5 bg-orange-100/30 dark:bg-orange-900/30"
                />
              </div>

              {/* Employee List */}
              <div className="mt-4">
                <p className="text-xs font-semibold text-orange-700 dark:text-orange-300 mb-3 uppercase tracking-wide">Employees Requiring Assignment</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[420px] overflow-y-auto pr-2 custom-scrollbar">
                  {analysis.lowTaskEmployees.map((emp, index) => (
                    <div 
                      key={emp.employeeId}
                      className="group rounded-xl bg-white/20 dark:bg-white/10 backdrop-blur-lg border border-white/40 dark:border-white/20 hover:bg-white/30 dark:hover:bg-white/20 hover:border-white/60 dark:hover:border-white/30 transition-all duration-200 shadow-md hover:shadow-lg p-4"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-orange-400 to-red-400 flex items-center justify-center flex-shrink-0 font-semibold text-white text-sm shadow-md">
                          {(index + 1).toString().padStart(2, '0')}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm text-orange-950 dark:text-white truncate">
                            {emp.name}
                          </p>
                          <p className="text-xs text-orange-700 dark:text-orange-300">
                            {emp.activeTasks === 0 ? '⏸️ No active tasks' : `${emp.activeTasks} active task${emp.activeTasks !== 1 ? 's' : ''}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/20">
                        <Badge 
                          className="bg-red-500/20 dark:bg-red-500/30 text-red-700 dark:text-red-200 border border-red-300 dark:border-red-600 font-medium text-xs px-2 py-0.5"
                        >
                          {emp.activeTasks} task{emp.activeTasks !== 1 ? 's' : ''}
                        </Badge>
                        <Button
                          size="sm"
                          className="h-7 px-3 bg-green-600 hover:bg-green-700 text-white dark:bg-green-700 dark:hover:bg-green-800 font-medium shadow-sm"
                          onClick={() => {
                            setSelectedEmployee({
                              id: emp.employeeId,
                              name: emp.name,
                              department: emp.department
                            });
                            setIsCreateTaskOpen(true);
                          }}
                        >
                          Assign
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end pt-3 border-t border-white/20 dark:border-white/10">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-orange-600 dark:text-orange-400 hover:bg-orange-500/10 gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Alerts */}
      {success && (
        <Alert className="bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-900 animate-fade-in">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertTitle className="text-green-800 dark:text-green-200">Success</AlertTitle>
          <AlertDescription className="text-green-700 dark:text-green-300">{success}</AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-900 animate-fade-in">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800 dark:text-red-200">Error</AlertTitle>
          <AlertDescription className="text-red-700 dark:text-red-300">{error}</AlertDescription>
        </Alert>
      )}

      {/* Tabs Navigation - Separated */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="flex flex-wrap gap-3 mb-6">
          <TabsList className="h-auto p-0 bg-transparent">
            <TabsTrigger 
              value="overview"
              className="flex items-center justify-center gap-2 py-3 px-5 rounded-xl border-2 border-muted data-[state=active]:bg-green-500 data-[state=active]:border-green-500 data-[state=active]:text-white transition-all duration-200 hover:border-green-500/50"
            >
              <BarChart className="h-4 w-4" />
              <span className="font-semibold">Overview</span>
            </TabsTrigger>
          </TabsList>
          
          <TabsList className="h-auto p-0 bg-transparent">
            <TabsTrigger 
              value="available"
              className="flex items-center justify-center gap-2 py-3 px-5 rounded-xl border-2 border-muted data-[state=active]:bg-green-500 data-[state=active]:border-green-500 data-[state=active]:text-white transition-all duration-200 hover:border-green-500/50"
            >
              <UserCheck className="h-4 w-4" />
              <span className="font-semibold">All Employees</span>
              <span className="ml-1 text-xs opacity-70">({analysis?.allEmployees?.length || 0})</span>
            </TabsTrigger>
          </TabsList>
          
          <TabsList className="h-auto p-0 bg-transparent">
            <TabsTrigger 
              value="recommendations"
              className="flex items-center justify-center gap-2 py-3 px-5 rounded-xl border-2 border-muted data-[state=active]:bg-green-500 data-[state=active]:border-green-500 data-[state=active]:text-white transition-all duration-200 hover:border-green-500/50"
            >
              <Target className="h-4 w-4" />
              <span className="font-semibold">Recommendations</span>
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content */}
        <TabsContent value="overview" className="mt-0">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="border-l-4 border-l-green-500">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Workload Distribution</CardTitle>
                  <Activity className="h-5 w-5 text-green-500" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Team Average</span>
                      <span className="font-medium">{analysis?.teamWorkload || 0}%</span>
                    </div>
                    <Progress value={analysis?.teamWorkload || 0} className="h-2" />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Current team workload distribution across all employees
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">Resource Allocation</CardTitle>
                  <Users className="h-5 w-5 text-blue-500" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Available</span>
                    <Badge variant="outline" className="bg-green-500/10 text-green-700 dark:text-green-400">
                      {analysis?.availableEmployees?.length || 0}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Low Tasks</span>
                    <Badge variant="outline" className="bg-orange-500/10 text-orange-700 dark:text-orange-400">
                      {analysis?.lowTaskEmployees?.length || 0}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="available" className="mt-0">
          {/* Task Distribution Summary */}
          {analysis?.allEmployees?.length > 0 && (
            <Card className="mb-6 border-l-4 border-l-primary">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Task Distribution Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-3 bg-red-50 dark:bg-red-950/20 rounded-lg border border-red-200 dark:border-red-800">
                    <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {analysis.allEmployees.filter(e => e.activeTasks === 0).length}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">No Tasks</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {analysis.allEmployees.filter(e => e.activeTasks === 1).length}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">1 Task</div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {analysis.allEmployees.filter(e => e.activeTasks === 2).length}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">2 Tasks</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                    <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {analysis.allEmployees.filter(e => e.activeTasks === 3).length}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">3 Tasks</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
                    <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {analysis.allEmployees.filter(e => e.activeTasks > 3).length}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">4+ Tasks</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {analysis?.allEmployees?.length > 0 ? (
              // Sort employees by task count (ascending - least busy first)
              [...analysis.allEmployees]
                .sort((a, b) => a.activeTasks - b.activeTasks)
                .map((employee) => {
                  // Determine badge color based on task load
                  const getBadgeStyle = (tasks) => {
                    if (tasks === 0) return { bg: "bg-red-500/10", text: "text-red-700 dark:text-red-400", label: "No Tasks", border: "border-l-red-500" };
                    if (tasks === 1) return { bg: "bg-green-500/10", text: "text-green-700 dark:text-green-400", label: "Available", border: "border-l-green-500" };
                    if (tasks === 2) return { bg: "bg-blue-500/10", text: "text-blue-700 dark:text-blue-400", label: "Moderate", border: "border-l-blue-500" };
                    if (tasks === 3) return { bg: "bg-yellow-500/10", text: "text-yellow-700 dark:text-yellow-400", label: "Busy", border: "border-l-yellow-500" };
                    return { bg: "bg-orange-500/10", text: "text-orange-700 dark:text-orange-400", label: "Overloaded", border: "border-l-orange-500" };
                  };

                  const badgeStyle = getBadgeStyle(employee.activeTasks);

                  return (
                    <Card 
                      key={employee.employeeId}
                      className={`border-l-4 ${badgeStyle.border} transition-all hover:shadow-md`}
                    >
                      <CardContent className="pt-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-sm truncate">{employee.name}</h3>
                            <Badge variant="outline" className={`${badgeStyle.bg} ${badgeStyle.text} text-xs`}>
                              {badgeStyle.label}
                            </Badge>
                          </div>
                          <div className="space-y-2 text-xs">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Active Tasks:</span>
                              <span className="font-bold text-base">{employee.activeTasks}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Completed:</span>
                              <span className="font-medium">{employee.completedTasks || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Completion Rate:</span>
                              <span className="font-medium">{employee.completionRate}%</span>
                            </div>
                            {employee.overdueTasks > 0 && (
                              <div className="flex justify-between text-red-600 dark:text-red-400">
                                <span>Overdue:</span>
                                <span className="font-medium">{employee.overdueTasks}</span>
                              </div>
                            )}
                          </div>
                          <div className="pt-2 border-t">
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-muted-foreground">Availability Score</span>
                              <span className="text-sm font-bold text-primary">{employee.availabilityScore}</span>
                            </div>
                            <Progress value={employee.availabilityScore} className="h-1.5 mt-2" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Users className="h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="font-semibold text-lg mb-2">No Employees Found</h3>
                  <p className="text-sm text-muted-foreground text-center max-w-sm">
                    No employee data available. Try refreshing the analysis.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="recommendations" className="mt-0">
          <div className="space-y-4">
            {analysis?.recommendations?.length > 0 ? (
              analysis.recommendations.map((rec, index) => (
                <Card 
                  key={index}
                  className="border-l-4 border-l-primary transition-all hover:shadow-md"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{rec.taskType}</CardTitle>
                      <Target className="h-5 w-5 text-primary" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <UserCheck className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Recommended Assignee:</span>
                        <span className="font-medium">{rec.recommendedEmployee}</span>
                      </div>
                      <p className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-lg">
                        {rec.reason}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Target className="h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="font-semibold text-lg mb-2">No Recommendations Available</h3>
                  <p className="text-sm text-muted-foreground text-center max-w-sm">
                    Run an analysis to get AI-powered task assignment recommendations.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Task Dialog */}
      <CreateTaskDialog 
        open={isCreateTaskOpen} 
        onOpenChange={(open) => {
          setIsCreateTaskOpen(open);
          if (!open) {
            setSelectedEmployee(null);
          }
        }}
        defaultAssignee={selectedEmployee}
      />
    </div>
  );
}