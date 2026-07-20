import React from 'react';
import { AlertCircle, CheckCircle2, Info, XCircle, X } from 'lucide-react';
import { cn } from '@/utils/helpers';

export const Alert = ({ 
  className,
  variant = 'info',
  title,
  children,
  onClose,
  ...props 
}) => {
  const variants = {
    info: {
      container: 'bg-info/10 border-info text-info-foreground',
      icon: Info,
    },
    success: {
      container: 'bg-success/10 border-success text-success-foreground',
      icon: CheckCircle2,
    },
    warning: {
      container: 'bg-warning/10 border-warning text-warning-foreground',
      icon: AlertCircle,
    },
    destructive: {
      container: 'bg-destructive/10 border-destructive text-destructive-foreground',
      icon: XCircle,
    },
    error: {
      container: 'bg-destructive/10 border-destructive text-destructive-foreground',
      icon: XCircle,
    },
  };

  const config = variants[variant] || variants.info;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'relative rounded-lg border-l-4 p-4 transition-all duration-300',
        config.container,
        className
      )}
      {...props}
    >
      <div className="flex items-start gap-3">
        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          {title && (
            <h5 className="font-semibold mb-1">{title}</h5>
          )}
          <div className="text-sm">{children}</div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 rounded-md p-1 hover:bg-black/10 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default Alert;
