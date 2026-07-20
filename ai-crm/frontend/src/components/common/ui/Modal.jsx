import React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/utils/helpers';
import Button from './Button';

export const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  description,
  children,
  size = 'default',
  className,
  showCloseButton = true,
}) => {
  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-md',
    default: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-7xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div 
        className={cn(
          'relative bg-card rounded-lg shadow-xl p-6 m-4 w-full animate-scale-in',
          sizes[size],
          className
        )}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              {title && (
                <h2 className="text-2xl font-heading font-bold tracking-tight">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {description}
                </p>
              )}
            </div>
            {showCloseButton && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="ml-4"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
        
        {/* Content */}
        <div className="custom-scrollbar max-h-[calc(100vh-200px)] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

export const ModalFooter = ({ className, children, ...props }) => (
  <div className={cn('flex items-center justify-end gap-3 mt-6 pt-6 border-t', className)} {...props}>
    {children}
  </div>
);

export default Modal;
