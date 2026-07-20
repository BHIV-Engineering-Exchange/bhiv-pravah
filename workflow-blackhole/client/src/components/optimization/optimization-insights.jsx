"use client";

import { useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Sparkles, AlertCircle } from "lucide-react";
import { api } from "../../lib/api";
import { useToast } from "../../hooks/use-toast";
import { InsightCard } from "./insight-card";

export function OptimizationInsights({ insights }) {
  const { toast } = useToast();

  // Categorize insights for better performance
  const categorizedInsights = useMemo(() => {
    if (!insights || insights.length === 0) return {};
    
    return {
      resources: insights.filter((i) => i.category === "Resources"),
      dependencies: insights.filter((i) => i.category === "Dependencies"),
      deadlines: insights.filter((i) => i.category === "Deadlines"),
      workflow: insights.filter((i) => i.category === "Workflow"),
    };
  }, [insights]);

  const handleApplyAction = async (action, insight) => {
    try {
      // Extract task title from description - try multiple patterns
      let taskTitle = insight.description.match(/Task '([^']+)'/)?.[1] ||
                      insight.description.match(/task "([^"]+)"/)?.[1] ||
                      insight.description.match(/task ([A-Za-z0-9\s]+)/i)?.[1] ||
                      insight.title?.match(/Task '([^']+)'/)?.[1];
      
      if (!taskTitle) {
        // If we can't extract from description, try to get task ID from insight
        if (insight.taskId) {
          const allTasks = await api.tasks.getTasks();
          const task = allTasks.find((t) => t._id === insight.taskId);
          if (task) {
            await applyActionToTask(action, task);
            return;
          }
        }
        throw new Error("Task not found in insight description");
      }

      const allTasks = await api.tasks.getTasks();
      const task = allTasks.find((t) => t.title === taskTitle || t._id === taskTitle);
      if (!task) {
        throw new Error(`Task "${taskTitle}" not found`);
      }

      await applyActionToTask(action, task);
    } catch (err) {
      console.error("Error applying action:", err);
      toast({
        title: "Error",
        description: err.message || `Failed to apply action "${action}"`,
        variant: "destructive",
      });
    }
  };

  const applyActionToTask = async (action, task) => {
    let updates = {};
    const actionLower = action.toLowerCase();
    
    // Handle "Reschedule due date" action
    if (actionLower.includes("reschedule") || actionLower.includes("due date")) {
      if (!task.dueDate) {
        throw new Error("Task does not have a due date to reschedule");
      }
      const newDueDate = new Date(task.dueDate);
      newDueDate.setDate(newDueDate.getDate() + 7); // Extend by 7 days
      updates.dueDate = newDueDate.toISOString();
    }
    // Handle "Prioritize task completion" or "Prioritize" action
    else if (actionLower.includes("prioritize") || actionLower.includes("priority")) {
      updates.priority = "High";
    }
    // Handle "Investigate reason for delay" action
    else if (actionLower.includes("investigate") || actionLower.includes("delay")) {
      // Add a note or comment about investigation
      updates.status = task.status || "In Progress";
      updates.notes = task.notes 
        ? `${task.notes}\n\n[AI Action] Investigation requested: ${new Date().toLocaleString()}`
        : `[AI Action] Investigation requested: ${new Date().toLocaleString()}`;
    }
    // Legacy handlers for backward compatibility
    else if (actionLower.includes("reassign")) {
      updates.assignee = null;
    } else if (actionLower.includes("adjust deadlines") || actionLower.includes("extend deadlines")) {
      const newDueDate = new Date(task.dueDate);
      newDueDate.setDate(newDueDate.getDate() + 7);
      updates.dueDate = newDueDate.toISOString();
    } else {
      throw new Error(`Unknown action: "${action}"`);
    }

    // Update the task
    await api.tasks.updateTask(task._id, updates);

    toast({
      title: "Success",
      description: `Action "${action}" applied to task "${task.title || task._id}"`,
    });
  };

  // Empty state
  if (!insights || insights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            AI-Generated Insights
          </CardTitle>
          <CardDescription>
            Optimization suggestions based on AI analysis of your workflow data
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <AlertCircle className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="font-semibold text-lg mb-2">No Insights Available</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Generate AI insights by clicking "Refresh Analysis" in the Actions panel. 
            Our AI will analyze your workflow data to provide optimization suggestions.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Render insights list
  const renderInsightsList = (insightsList) => {
    if (!insightsList || insightsList.length === 0) {
      return (
        <div className="text-center py-8 text-muted-foreground">
          <p>No insights in this category</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {insightsList.map((insight, index) => (
          <InsightCard
            key={insight.id || index}
            insight={insight}
            onApplyAction={handleApplyAction}
          />
        ))}
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          AI-Generated Insights
        </CardTitle>
        <CardDescription>
          Optimization suggestions based on AI analysis of your workflow data
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="mb-4 w-full grid grid-cols-5">
            <TabsTrigger value="all">
              All ({insights.length})
            </TabsTrigger>
            <TabsTrigger value="resources">
              Resources ({categorizedInsights.resources?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="dependencies">
              Dependencies ({categorizedInsights.dependencies?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="deadlines">
              Deadlines ({categorizedInsights.deadlines?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="workflow">
              Workflow ({categorizedInsights.workflow?.length || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-0">
            {renderInsightsList(insights)}
          </TabsContent>

          <TabsContent value="resources" className="mt-0">
            {renderInsightsList(categorizedInsights.resources)}
          </TabsContent>

          <TabsContent value="dependencies" className="mt-0">
            {renderInsightsList(categorizedInsights.dependencies)}
          </TabsContent>

          <TabsContent value="deadlines" className="mt-0">
            {renderInsightsList(categorizedInsights.deadlines)}
          </TabsContent>

          <TabsContent value="workflow" className="mt-0">
            {renderInsightsList(categorizedInsights.workflow)}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}