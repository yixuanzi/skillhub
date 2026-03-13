import { createContext, useContext, ReactNode, HTMLAttributes, MouseEvent } from 'react';
import { cn } from '@/utils/cn';
import { X } from 'lucide-react';

interface DialogContextValue {
  isOpen: boolean;
  setOpen: (open: boolean) => void;
}

const DialogContext = createContext<DialogContextValue | undefined>(undefined);

const useDialogContext = () => {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error('Dialog components must be used within a Dialog component');
  }
  return context;
};

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}

export const Dialog = ({ open, onOpenChange, children }: DialogProps) => {
  return (
    <DialogContext.Provider value={{ isOpen: open, setOpen: onOpenChange }}>
      {children}
    </DialogContext.Provider>
  );
};

interface DialogContentProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export const DialogContent = ({ children, className, ...props }: DialogContentProps) => {
  const { isOpen, setOpen } = useDialogContext();

  if (!isOpen) return null;

  const handleBackdropClick = (e: MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      setOpen(false);
    }
  };

  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  // Add escape listener
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', handleEscape);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={handleBackdropClick}
    >
      <div
        className={cn(
          'relative w-full max-w-md bg-void-900 border border-void-700 rounded-lg shadow-xl p-6 animate-slide-in',
          className
        )}
        {...props}
      >
        <button
          onClick={() => setOpen(false)}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
        {children}
      </div>
    </div>
  );
};

interface DialogHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export const DialogHeader = ({ children, className, ...props }: DialogHeaderProps) => {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  );
};

interface DialogTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  children: ReactNode;
}

export const DialogTitle = ({ children, className, ...props }: DialogTitleProps) => {
  return (
    <h2 className={cn('text-lg font-semibold text-gray-100', className)} {...props}>
      {children}
    </h2>
  );
};

interface DialogDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {
  children: ReactNode;
}

export const DialogDescription = ({ children, className, ...props }: DialogDescriptionProps) => {
  return (
    <p className={cn('text-sm text-gray-400 mt-1', className)} {...props}>
      {children}
    </p>
  );
};
