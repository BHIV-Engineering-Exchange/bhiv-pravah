import { forwardRef } from 'react';
import clsx from 'clsx';
import { ChevronDown } from 'lucide-react';

const Select = forwardRef(({
  label,
  error,
  helperText,
  options = [],
  placeholder = 'Select an option',
  className,
  containerClassName,
  ...props
}, ref) => {
  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-sm font-medium text-foreground mb-1">
          {label}
          {props.required && <span className="text-destructive ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <select
          ref={ref}
          className={clsx(
            'block w-full rounded-xl border-2 px-4 py-3 text-foreground bg-card appearance-none',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-0 sm:text-sm pr-10',
            'transition-all duration-300',
            error
              ? 'border-destructive focus:border-destructive focus:ring-destructive'
              : 'border-border focus:border-primary',
            props.disabled && 'bg-muted text-muted-foreground cursor-not-allowed',
            className
          )}
          {...props}
        >
          <option value="" className="bg-card text-muted-foreground">{placeholder}</option>
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-card text-foreground">
              {option.label}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        </div>
      </div>
      {error && (
        <p className="mt-1 text-sm text-destructive">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm text-muted-foreground">{helperText}</p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;
