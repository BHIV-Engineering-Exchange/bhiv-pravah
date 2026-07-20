import { Sparkles, TrendingUp, Zap } from "lucide-react";

export function OptimizationHeader({ insightsCount, highImpactCount }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-primary" />
            AI Optimization
          </h1>
          <p className="text-muted-foreground">
            AI-driven insights and recommendations to optimize your workflow
          </p>
        </div>
      </div>

      {/* Stats Overview */}
      {insightsCount > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Total Insights</p>
                <p className="text-2xl font-bold">{insightsCount}</p>
              </div>
            </div>
          </div>
          
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-muted-foreground">High Impact</p>
                <p className="text-2xl font-bold">{highImpactCount}</p>
              </div>
            </div>
          </div>
          
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Optimization Score</p>
                <p className="text-2xl font-bold">
                  {Math.round(((insightsCount - highImpactCount) / Math.max(insightsCount, 1)) * 100)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
  