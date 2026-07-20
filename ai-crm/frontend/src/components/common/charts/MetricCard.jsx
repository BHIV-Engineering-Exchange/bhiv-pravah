import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/utils/helpers';
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card';

export const MetricCard = ({ 
  title, 
  value, 
  trend,
  trendValue,
  icon: Icon,
  variant = 'primary',
  className 
}) => {
  const isPositive = trend === 'up';
  const TrendIcon = isPositive ? TrendingUp : TrendingDown;

  const variantColors = {
    primary: 'border-primary',
    secondary: 'border-secondary',
    accent: 'border-accent',
    info: 'border-info',
    success: 'border-success',
    warning: 'border-warning',
  };

  return (
    <Card 
      className={cn(
        'border-l-4 border-transparent hover:border-primary transition-all duration-300 hover-lift',
        variantColors[variant],
        className
      )}
      gradient
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              {title}
            </p>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-3xl font-heading font-bold tracking-tight">
                {value}
              </p>
              {trendValue && (
                <span className={cn(
                  'flex items-center gap-1 text-sm font-medium',
                  isPositive ? 'text-success' : 'text-destructive'
                )}>
                  <TrendIcon className="h-4 w-4" />
                  {trendValue}
                </span>
              )}
            </div>
          </div>
          {Icon && (
            <div className={cn(
              'w-12 h-12 rounded-xl flex items-center justify-center shadow-lg',
              `gradient-${variant}`
            )}>
              <Icon className="h-6 w-6 text-white" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default MetricCard;
