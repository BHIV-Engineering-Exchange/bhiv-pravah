import clsx from 'clsx';

const Card = ({ children, className, padding = true, variant = 'default', ...props }) => {
  const variants = {
    default: 'bg-card border-border/30',
    glass: 'bg-card/80 backdrop-blur-xl border-border/50',
    elevated: 'bg-card border-border/30 shadow-lg',
  };

  return (
    <div
      className={clsx(
        'rounded-2xl border transition-all duration-300',
        variants[variant] || variants.default,
        padding && 'p-6',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader = ({ children, className, ...props }) => {
  return (
    <div
      className={clsx('px-6 py-4 border-b border-border/30', className)}
      {...props}
    >
      {children}
    </div>
  );
};

const CardTitle = ({ children, className, ...props }) => {
  return (
    <h3
      className={clsx('text-lg font-semibold text-foreground font-display', className)}
      {...props}
    >
      {children}
    </h3>
  );
};

const CardDescription = ({ children, className, ...props }) => {
  return (
    <p
      className={clsx('text-sm text-muted-foreground mt-1', className)}
      {...props}
    >
      {children}
    </p>
  );
};

const CardContent = ({ children, className, ...props }) => {
  return (
    <div className={clsx('px-6 py-4', className)} {...props}>
      {children}
    </div>
  );
};

const CardFooter = ({ children, className, ...props }) => {
  return (
    <div
      className={clsx('px-6 py-4 border-t border-border/30 bg-muted/50 rounded-b-2xl', className)}
      {...props}
    >
      {children}
    </div>
  );
};

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Description = CardDescription;
Card.Content = CardContent;
Card.Footer = CardFooter;

export default Card;
