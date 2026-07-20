"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { RefreshCw, Download, Share2, Clock } from "lucide-react";
import { useOptimizeWorkflow } from "../../hooks/use-ai";
import { api } from "../../lib/api";
import { useToast } from "../../hooks/use-toast";

export function OptimizationActions({ tasks, setTasks, insights }) {
  const { optimizeWorkflow, isLoading } = useOptimizeWorkflow();
  const { toast } = useToast();

  // Calculate stats
  const stats = useMemo(() => {
    if (!insights || insights.length === 0) {
      return {
        total: 0,
        high: 0,
        medium: 0,
        low: 0,
        lastUpdated: "N/A",
      };
    }

    return {
      total: insights.length,
      high: insights.filter((i) => i.impact === "High").length,
      medium: insights.filter((i) => i.impact === "Medium").length,
      low: insights.filter((i) => i.impact === "Low").length,
      lastUpdated: insights.length > 0
        ? new Date(insights[insights.length - 1].createdAt).toLocaleString()
        : "N/A",
    };
  }, [insights]);

  const handleRefreshAnalysis = async () => {
    try {
      await optimizeWorkflow();
      toast({
        title: "Success",
        description: "AI analysis refreshed successfully",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: err.message || "Failed to refresh AI analysis",
        variant: "destructive",
      });
    }
  };

  const handleApplyAllRecommendations = async () => {
    try {
      const insightsData = await api.ai.getInsights();
      let appliedCount = 0;

      for (const insight of insightsData) {
        for (const action of insight.actions || []) {
          // Extract task title from description - try multiple patterns
          let taskTitle = insight.description?.match(/Task '([^']+)'/)?.[1] ||
                          insight.description?.match(/task "([^"]+)"/)?.[1] ||
                          insight.description?.match(/task ([A-Za-z0-9\s]+)/i)?.[1] ||
                          insight.title?.match(/Task '([^']+)'/)?.[1];
          
          let task = null;
          if (taskTitle) {
            task = tasks.find((t) => t.title === taskTitle || t._id === taskTitle);
          } else if (insight.taskId) {
            task = tasks.find((t) => t._id === insight.taskId);
          }
          
          if (task) {
            const actionLower = action.toLowerCase();
            let updates = {};
            
            // Handle "Reschedule due date" action
            if (actionLower.includes("reschedule") || actionLower.includes("due date")) {
              if (task.dueDate) {
                const newDueDate = new Date(task.dueDate);
                newDueDate.setDate(newDueDate.getDate() + 7);
                updates.dueDate = newDueDate.toISOString();
                await api.tasks.updateTask(task._id, updates);
                appliedCount++;
              }
            }
            // Handle "Prioritize task completion" or "Prioritize" action
            else if (actionLower.includes("prioritize") || actionLower.includes("priority")) {
              updates.priority = "High";
              await api.tasks.updateTask(task._id, updates);
              appliedCount++;
            }
            // Handle "Investigate reason for delay" action
            else if (actionLower.includes("investigate") || actionLower.includes("delay")) {
              updates.status = task.status || "In Progress";
              updates.notes = task.notes 
                ? `${task.notes}\n\n[AI Action] Investigation requested: ${new Date().toLocaleString()}`
                : `[AI Action] Investigation requested: ${new Date().toLocaleString()}`;
              await api.tasks.updateTask(task._id, updates);
              appliedCount++;
            }
            // Legacy handlers
            else if (actionLower.includes("reassign")) {
              await api.tasks.updateTask(task._id, { assignee: null });
              appliedCount++;
            } else if (actionLower.includes("adjust deadlines") || actionLower.includes("extend deadlines")) {
              if (task.dueDate) {
              const newDueDate = new Date(task.dueDate);
              newDueDate.setDate(newDueDate.getDate() + 7);
              await api.tasks.updateTask(task._id, { dueDate: newDueDate.toISOString() });
              appliedCount++;
              }
            }
          }
        }
      }

      const updatedTasks = await api.tasks.getTasks();
      setTasks(updatedTasks);
      
      toast({
        title: "Success",
        description: `Applied ${appliedCount} AI recommendations`,
      });
    } catch (err) {
      console.error("Error applying recommendations:", err);
      toast({
        title: "Error",
        description: err.message || "Failed to apply recommendations",
        variant: "destructive",
      });
    }
  };

  const handleExportInsights = async () => {
    try {
      const insightsData = await api.ai.getInsights();
      const exportData = {
        exportDate: new Date().toISOString(),
        totalInsights: insightsData.length,
        insights: insightsData,
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: "application/json" 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ai-insights-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: "Success",
        description: "Insights exported successfully",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: err.message || "Failed to export insights",
        variant: "destructive",
      });
    }
  };

  const handleShareInsights = () => {
    navigator.clipboard.writeText(window.location.href)
      .then(() => {
        toast({
          title: "Success",
          description: "Link copied to clipboard",
        });
      })
      .catch(() => {
        toast({
          title: "Error",
          description: "Failed to copy link",
          variant: "destructive",
        });
      });
  };

  return (
    <div className="space-y-4">
      {/* Primary Action */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Apply AI recommendations to your workflow</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            className="w-full" 
            onClick={handleApplyAllRecommendations} 
            disabled={isLoading || !insights || insights.length === 0}
          >
            Apply All Recommendations
          </Button>

          <div className="grid grid-cols-1 gap-2">
            <Button
              variant="outline"
              className="justify-start"
              onClick={handleRefreshAnalysis}
              disabled={isLoading}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              {isLoading ? "Refreshing..." : "Refresh Analysis"}
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={handleExportInsights}
              disabled={!insights || insights.length === 0}
            >
              <Download className="mr-2 h-4 w-4" />
              Export Insights
            </Button>
            <Button
              variant="outline"
              className="justify-start"
              onClick={handleShareInsights}
            >
              <Share2 className="mr-2 h-4 w-4" />
              Share Insights
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Analysis Summary</CardTitle>
          <CardDescription>Overview of AI-generated insights</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Total Insights</span>
              <span className="font-semibold">{stats.total}</span>
            </div>
            <div className="h-px bg-border" />
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-red-500" />
                High Impact
              </span>
              <span className="font-semibold text-red-500">{stats.high}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-amber-500" />
                Medium Impact
              </span>
              <span className="font-semibold text-amber-500">{stats.medium}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                Low Impact
              </span>
              <span className="font-semibold text-green-500">{stats.low}</span>
            </div>
            
            <div className="h-px bg-border" />
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-2">
                <Clock className="h-3 w-3" />
                Last Updated
              </span>
              <span className="text-xs font-medium">{stats.lastUpdated}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}