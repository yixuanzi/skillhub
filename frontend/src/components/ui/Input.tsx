import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, type = 'text', ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label className="text-sm font-mono text-gray-400 uppercase tracking-wider">
            {label}
          </label>
        )}
        <input
          ref={ref}
          type={type}
          className={cn(
            'cyber-card px-4 py-2.5 font-mono text-sm',
            'bg-void-900/50 border border-void-700',
            'text-gray-100 placeholder:text-gray-600',
            'focus:outline-none focus:border-cyber-primary focus:border-glow',
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

Input.displayName = 'Input';
