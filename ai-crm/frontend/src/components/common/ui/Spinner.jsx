import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/helpers';

export const Spinner = ({ 
  className,
  size = 'default',
  variant = 'primary',
  ...props 
}) => {
  const sizes = {
    sm: 'h-4 w-4',
    default: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  const variants = {
    primary: 'text-primary',
    secondary: 'text-secondary',
    accent: 'text-accent',
    muted: 'text-muted-foreground',
  };

  return (
    <Loader2 
      className={cn('animate-spin', sizes[size], variants[variant], className)} 
      {...props}
    />
  );
};

export const LoadingSpinner = ({ text = 'Loading...' }) => (
  <div className="flex flex-col items-center justify-center p-8 gap-4">
    <Spinner size="xl" />
    <p className="text-muted-foreground">{text}</p>
  </div>
);

export default Spinner;
