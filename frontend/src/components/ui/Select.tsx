import React, { createContext, useContext, useState, useCallback, forwardRef } from 'react';
import { cn } from '@/utils/cn';

interface SelectContextValue {
  value: string;
  onChange: (value: string) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
}

const SelectContext = createContext<SelectContextValue | undefined>(undefined);

const useSelectContext = () => {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('Select components must be used within a Select component');
  }
  return context;
};

export interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
  disabled?: boolean;
  children: React.ReactNode;
}

export const Select: React.FC<SelectProps> = ({
  value: controlledValue,
  onValueChange,
  defaultValue = '',
  disabled = false,
  children,
}) => {
  const [internalValue, setInternalValue] = useState(defaultValue);
  const [open, setOpen] = useState(false);

  const value = controlledValue !== undefined ? controlledValue : internalValue;

  const handleChange = useCallback(
    (newValue: string) => {
      if (controlledValue === undefined) {
        setInternalValue(newValue);
      }
      onValueChange?.(newValue);
      setOpen(false);
    },
    [controlledValue, onValueChange]
  );

  return (
    <SelectContext.Provider value={{ value, onChange: handleChange, open, setOpen }}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  );
};

export interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

export const SelectTrigger = forwardRef<HTMLButtonElement, SelectTriggerProps>(
  ({ className, children, disabled, ...props }, ref) => {
    const { value, onChange, open, setOpen } = useSelectContext();

    return (
      <>
        <button
          ref={ref}
          type="button"
          className={cn(
            'flex items-center justify-between w-full px-4 py-2.5 font-mono text-sm rounded-lg',
            'bg-void-900/50 border border-void-700 text-gray-100',
            'focus:outline-none focus:border-cyber-primary',
            'transition-all duration-200',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            className
          )}
          onClick={() => setOpen(!open)}
          disabled={disabled}
          {...props}
        >
          {children}
          <svg
            className={cn(
              'w-4 h-4 transition-transform duration-200',
              open && 'transform rotate-180'
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </>
    );
  }
);

SelectTrigger.displayName = 'SelectTrigger';

export interface SelectValueProps {
  placeholder?: string;
}

export const SelectValue: React.FC<SelectValueProps> = ({ placeholder = 'Select...' }) => {
  const { value } = useSelectContext();
  return <span>{value || placeholder}</span>;
};

export interface SelectContentProps {
  children: React.ReactNode;
}

export const SelectContent: React.FC<SelectContentProps> = ({ children }) => {
  const { open, setOpen } = useSelectContext();

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-10"
        onClick={() => setOpen(false)}
      />
      <div className="absolute z-20 w-full mt-1 bg-void-900 border border-void-700 rounded-lg shadow-lg max-h-60 overflow-auto">
        <div className="py-1">{children}</div>
      </div>
    </>
  );
};

export interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  disabled?: boolean;
}

export const SelectItem: React.FC<SelectItemProps> = ({ value, children, disabled }) => {
  const { value: selectedValue, onChange } = useSelectContext();

  return (
    <div
      className={cn(
        'px-4 py-2 font-mono text-sm cursor-pointer transition-colors duration-150',
        'hover:bg-void-800',
        selectedValue === value && 'bg-cyber-primary/10 text-cyber-primary',
        disabled && 'opacity-50 cursor-not-allowed hover:bg-transparent',
        disabled && 'text-gray-600'
      )}
      onClick={() => !disabled && onChange(value)}
    >
      {children}
    </div>
  );
};
