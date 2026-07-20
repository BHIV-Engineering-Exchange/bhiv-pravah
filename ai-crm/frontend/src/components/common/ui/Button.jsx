import React from 'react';
import { cn } from '@/utils/helpers';

export const Button = React.forwardRef(({ 
  className, 
  variant = 'primary', 
  size = 'default',
  children,
  ...props 
}, ref) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50';
  
  const variants = {
    primary: 'gradient-primary text-primary-foreground shadow-glow-primary hover:shadow-lg hover:scale-105',
    secondary: 'gradient-secondary text-secondary-foreground shadow-glow-secondary hover:shadow-lg hover:scale-105',
    accent: 'gradient-accent text-accent-foreground shadow-glow-accent hover:shadow-lg hover:scale-105',
    outline: 'border-2 border-primary text-primary hover:bg-primary hover:text-primary-foreground',
    ghost: 'hover:bg-accent hover:text-accent-foreground',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  };
  
  const sizes = {
    default: 'h-10 px-4 py-2',
    sm: 'h-9 rounded-md px-3 text-sm',
    lg: 'h-11 rounded-lg px-8 text-lg',
    icon: 'h-10 w-10',
  };

  return (
    <button
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      ref={ref}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;
