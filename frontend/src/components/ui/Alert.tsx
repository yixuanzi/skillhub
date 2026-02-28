import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'danger';
}

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'flex items-start gap-3 rounded-lg border px-4 py-3',
          {
            'bg-cyber-secondary/5 border-cyber-secondary/20 text-cyber-secondary': variant === 'info',
            'bg-cyber-primary/5 border-cyber-primary/20 text-cyber-primary': variant === 'success',
            'bg-cyber-warning/5 border-cyber-warning/20 text-cyber-warning': variant === 'warning',
            'bg-cyber-accent/5 border-cyber-accent/20 text-cyber-accent': variant === 'danger',
          },
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Alert.displayName = 'Alert';
