import { TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            'px-4 py-2.5 font-mono text-sm min-h-[100px] resize-y rounded-lg',
            'bg-void-900/50 border border-void-700',
            'text-gray-100 placeholder:text-gray-600',
            'focus:outline-none focus:border-cyber-primary',
            'transition-all duration-200',
            error && 'border-cyber-accent focus:border-cyber-accent',
            className
          )}
          {...props}
        />
        {error && <span className="text-sm font-mono text-cyber-accent">{error}</span>}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
