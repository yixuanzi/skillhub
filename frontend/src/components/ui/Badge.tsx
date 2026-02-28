import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium uppercase tracking-wider',
          {
            'bg-void-800 text-gray-300 border border-void-600': variant === 'default',
            'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30': variant === 'success',
            'bg-cyber-warning/10 text-cyber-warning border border-cyber-warning/30': variant === 'warning',
            'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/30': variant === 'danger',
            'bg-cyber-secondary/10 text-cyber-secondary border border-cyber-secondary/30': variant === 'info',
          },
          className
        )}
        {...props}
      >
        {variant !== 'default' && (
          <span className={cn('w-1.5 h-1.5 rounded-full animate-pulse-slow', {
            'bg-cyber-primary': variant === 'success',
            'bg-cyber-warning': variant === 'warning',
            'bg-cyber-accent': variant === 'danger',
            'bg-cyber-secondary': variant === 'info',
          })}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
