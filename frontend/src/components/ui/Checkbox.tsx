import { forwardRef, HTMLAttributes, useState, MouseEvent } from 'react';
import { cn } from '@/utils/cn';
import { Check } from 'lucide-react';

interface CheckboxProps extends Omit<HTMLAttributes<HTMLButtonElement>, 'onChange' | 'checked'> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
}

export const Checkbox = forwardRef<HTMLButtonElement, CheckboxProps>(
  ({ className, checked: controlledChecked, onCheckedChange, disabled = false, ...props }, ref) => {
    const [uncontrolledChecked, setUncontrolledChecked] = useState(false);

    const isControlled = controlledChecked !== undefined;
    const isChecked = isControlled ? controlledChecked : uncontrolledChecked;

    const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
      if (disabled) return;

      const newChecked = !isChecked;
      if (!isControlled) {
        setUncontrolledChecked(newChecked);
      }
      onCheckedChange?.(newChecked);
      props.onClick?.(e);
    };

    return (
      <button
        type="button"
        ref={ref}
        role="checkbox"
        aria-checked={isChecked}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center w-4 h-4 rounded border transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-cyber-primary/50',
          isChecked
            ? 'bg-cyber-primary border-cyber-primary'
            : 'bg-void-900 border-void-600 hover:border-void-500',
          disabled && 'opacity-50 cursor-not-allowed',
          !disabled && 'cursor-pointer',
          className
        )}
        onClick={handleClick}
        {...props}
      >
        {isChecked && (
          <Check className="w-3 h-3 text-void-950" strokeWidth={3} />
        )}
      </button>
    );
  }
);

Checkbox.displayName = 'Checkbox';
