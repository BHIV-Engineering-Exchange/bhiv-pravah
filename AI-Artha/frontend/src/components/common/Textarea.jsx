import { forwardRef } from 'react';
import clsx from 'clsx';

const Textarea = forwardRef(({
  label,
  error,
  helperText,
  className,
  containerClassName,
  rows = 4,
  ...props
}, ref) => {
  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-sm font-medium text-foreground mb-1">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        ref={ref}
        rows={rows}
        className={clsx(
          'block w-full rounded-lg border px-3 py-2 text-foreground placeholder:text-muted-foreground',
          'focus:outline-none focus:ring-2 focus:ring-offset-0 sm:text-sm resize-none',
          error
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
            : 'border-border focus:border-blue-500 focus:ring-blue-500',
          props.disabled && 'bg-muted text-muted-foreground cursor-not-allowed',
          className
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm text-muted-foreground">{helperText}</p>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';

export default Textarea;
