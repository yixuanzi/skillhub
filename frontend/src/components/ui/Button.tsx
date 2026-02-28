import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center gap-2 font-mono font-medium transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-cyber-primary/50',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          {
            'bg-cyber-primary/10 border border-cyber-primary text-cyber-primary hover:bg-cyber-primary/20 hover:border-glow':
              variant === 'primary',
            'bg-void-800 border border-void-600 text-gray-200 hover:border-cyber-secondary/50 hover:text-cyber-secondary':
              variant === 'secondary',
            'bg-transparent border border-transparent text-gray-400 hover:text-gray-200 hover:bg-void-800/50':
              variant === 'ghost',
            'bg-cyber-accent/10 border border-cyber-accent text-cyber-accent hover:bg-cyber-accent/20':
              variant === 'danger',
          },
          {
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-base': size === 'md',
            'px-6 py-3 text-lg': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
