import React from 'react';
import { cn } from '@/utils/helpers';

export const Card = React.forwardRef(({ 
  className, 
  children,
  hover = false,
  gradient = false,
  borderColor = null,
  ...props 
}, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        'rounded-lg bg-card shadow-xl p-6 transition-all duration-300',
        gradient && 'bg-gradient-to-br from-card to-card/50',
        borderColor && `border-l-4 border-${borderColor}`,
        hover && 'hover-lift cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

Card.displayName = 'Card';

export const CardHeader = ({ className, children, ...props }) => (
  <div className={cn('flex flex-col space-y-1.5 pb-4', className)} {...props}>
    {children}
  </div>
);

export const CardTitle = ({ className, children, ...props }) => (
  <h3 className={cn('text-2xl font-heading font-bold tracking-tight', className)} {...props}>
    {children}
  </h3>
);

export const CardDescription = ({ className, children, ...props }) => (
  <p className={cn('text-sm text-muted-foreground', className)} {...props}>
    {children}
  </p>
);

export const CardContent = ({ className, children, ...props }) => (
  <div className={cn('pt-0', className)} {...props}>
    {children}
  </div>
);

export const CardFooter = ({ className, children, ...props }) => (
  <div className={cn('flex items-center pt-4', className)} {...props}>
    {children}
  </div>
);

export default Card;
