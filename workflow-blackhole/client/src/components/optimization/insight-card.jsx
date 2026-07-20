import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { ArrowRight, Loader2 } from "lucide-react";

export function InsightCard({ insight, onApplyAction }) {
  const [loadingActions, setLoadingActions] = useState({});
  const getImpactColor = (impact) => {
    switch (impact) {
      case "High":
        return "bg-red-500/10 text-red-500 hover:bg-red-500/20";
      case "Medium":
        return "bg-amber-500/10 text-amber-500 hover:bg-amber-500/20";
      case "Low":
        return "bg-green-500/10 text-green-500 hover:bg-green-500/20";
      default:
        return "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20";
    }
  };

  const getImpactBorderColor = (impact) => {
    switch (impact) {
      case "High":
        return "border-l-red-500";
      case "Medium":
        return "border-l-amber-500";
      case "Low":
        return "border-l-green-500";
      default:
        return "border-l-primary";
    }
  };

  return (
    <Card className={`border-l-4 ${getImpactBorderColor(insight.impact)} transition-all hover:shadow-md`}>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start gap-4">
          <div className="flex-1">
            <CardTitle className="text-base font-semibold">{insight.title}</CardTitle>
            <CardDescription className="mt-1 flex items-center gap-2">
              <span>{insight.category}</span>
            </CardDescription>
          </div>
          <Badge className={getImpactColor(insight.impact)}>
            {insight.impact} Impact
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
          {insight.description}
        </p>
        {insight.actions && insight.actions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {insight.actions.map((action, actionIndex) => {
              const isLoading = loadingActions[actionIndex];
              return (
                <Button
                  key={actionIndex}
                  variant="outline"
                  size="sm"
                  className="transition-all hover:shadow-sm"
                  disabled={isLoading || !onApplyAction}
                  onClick={async () => {
                    if (!onApplyAction) {
                      console.error("onApplyAction is not defined");
                      return;
                    }
                    setLoadingActions(prev => ({ ...prev, [actionIndex]: true }));
                    try {
                      await onApplyAction(action, insight);
                    } catch (error) {
                      console.error("Error in onApplyAction:", error);
                    } finally {
                      setLoadingActions(prev => ({ ...prev, [actionIndex]: false }));
                    }
                  }}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      {action}
                      <ArrowRight className="ml-2 h-3 w-3" />
                    </>
                  )}
                </Button>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
