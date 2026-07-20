import { useState, useRef, useEffect } from 'react';
import toast from 'react-hot-toast';

interface SalaryRangeInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  name?: string;
  required?: boolean;
  onError?: (hasError: boolean) => void;
}

export default function SalaryRangeInput({ 
  value, 
  onChange, 
  placeholder = "e.g., 80000 - 120000", 
  className = "",
  name = "salary_range",
  required = false,
  onError
}: SalaryRangeInputProps) {
  const [localValue, setLocalValue] = useState(value);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Notify parent component of error state
  useEffect(() => {
    if (onError) {
      onError(hasError);
    }
  }, [hasError, onError]);

  // Sync local state with external value
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const validateInput = (inputValue: string): boolean => {
    // Allow empty input if not required
    if (!required && inputValue.trim() === "") {
      setHasError(false);
      setErrorMessage("");
      return true;
    }
    
    // Check for valid characters (numbers and dashes only)
    if (!/^[\d\s\-]*$/.test(inputValue)) {
      setHasError(true);
      setErrorMessage("Please enter only numbers and dashes");
      return false;
    }
    
    // Check for valid format (numbers with optional dash)
    const trimmed = inputValue.trim();
    if (trimmed !== "") {
      // Valid patterns: "123456", "123456 - 789012", "123456-", "123456 -"
      if (!/^\d+(\s*-\s*\d*)?$/.test(trimmed)) {
        setHasError(true);
        setErrorMessage("Please enter a valid salary range format (e.g., 500000 or 500000 - 800000)");
        return false;
      }
    }
    
    setHasError(false);
    setErrorMessage("");
    return true;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    const target = e.target as HTMLInputElement;
    const cursorPosition = target.selectionStart || 0;
    const currentValue = target.value;
    
    // Prevent invalid characters
    if (e.key.length === 1 && !/^[\d\-\s]$/.test(e.key)) {
      e.preventDefault();
      toast.error("Please enter only numbers and dashes", {
        duration: 2000,
        position: "top-center"
      });
      return;
    }
    
    // Handle space key for auto-dash insertion
    if (e.key === ' ' && cursorPosition > 0) {
      const textBeforeCursor = currentValue.substring(0, cursorPosition).trim();
      
      // Check if the text before cursor is a number
      if (/^\d+$/.test(textBeforeCursor)) {
        e.preventDefault();
        const textAfterCursor = currentValue.substring(cursorPosition);
        const newValue = `${textBeforeCursor} - ${textAfterCursor}`.trim();
        
        // Validate the new value
        if (validateInput(newValue)) {
          setLocalValue(newValue);
          onChange(newValue);
          
          // Set cursor position after the dash and space
          setTimeout(() => {
            if (inputRef.current) {
              const newCursorPosition = textBeforeCursor.length + 3; // position after " - "
              inputRef.current.setSelectionRange(newCursorPosition, newCursorPosition);
            }
          }, 0);
        }
        return;
      }
    }
    
    // Handle backspace to remove dash when appropriate
    if (e.key === 'Backspace' && cursorPosition > 0) {
      const textBeforeCursor = currentValue.substring(0, cursorPosition);
      const textAfterCursor = currentValue.substring(cursorPosition);
      
      // If we're at the dash position, remove the dash and surrounding spaces
      if (textBeforeCursor.endsWith(' -') && textAfterCursor.startsWith(' ')) {
        e.preventDefault();
        const newValue = `${textBeforeCursor.slice(0, -2)}${textAfterCursor.substring(1)}`;
        setLocalValue(newValue);
        onChange(newValue);
        
        // Set cursor position to remove the dash
        setTimeout(() => {
          if (inputRef.current) {
            const newCursorPosition = cursorPosition - 2;
            inputRef.current.setSelectionRange(newCursorPosition, newCursorPosition);
          }
        }, 0);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    // Validate input and only update if valid
    if (validateInput(newValue)) {
      setLocalValue(newValue);
      onChange(newValue);
    }
  };

  const handleBlur = () => {
    // Validate on blur
    if (!validateInput(localValue)) {
      return;
    }
    
    // Handle single number input - convert to range if needed
    const trimmedValue = localValue.trim();
    
    // If it's a single number, treat it as both min and max
    if (/^\d+$/.test(trimmedValue)) {
      const singleValue = parseInt(trimmedValue);
      if (singleValue > 0) {
        const rangeValue = `${singleValue} - ${singleValue}`;
        setLocalValue(rangeValue);
        onChange(rangeValue);
      }
    }
    // If it's a number followed by dash but no max value, treat as minimum only
    else if (/^\d+\s*-$/.test(trimmedValue)) {
      const minValue = trimmedValue.replace(/\s*-\s*$/, '').trim();
      if (minValue && parseInt(minValue) > 0) {
        const rangeValue = `${minValue} - `;
        setLocalValue(rangeValue);
        onChange(rangeValue);
      }
    }
  };

  // Combine base classes with error state
  const inputClasses = `${className} ${hasError ? 'border-red-500 focus:ring-red-500' : ''}`;
  
  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        name={name}
        value={localValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        className={inputClasses}
        placeholder={placeholder}
        required={required}
      />
      {hasError && (
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
      )}
      {hasError && errorMessage && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
      )}
    </div>
  );
}