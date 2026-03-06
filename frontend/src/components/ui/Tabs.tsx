import { createContext, useContext, useState, ReactNode, HTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | undefined>(undefined);

const useTabsContext = () => {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs components must be used within a Tabs component');
  }
  return context;
};

interface TabsProps extends HTMLAttributes<HTMLDivElement> {
  defaultValue: string;
  children: ReactNode;
}

export const Tabs = ({ defaultValue, children, className, ...props }: TabsProps) => {
  const [activeTab, setActiveTab] = useState(defaultValue);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={cn('', className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

interface TabsListProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export const TabsList = ({ children, className, ...props }: TabsListProps) => {
  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded-lg bg-void-900/50 p-1 border border-void-700/50',
        className
      )}
      role="tablist"
      {...props}
    >
      {children}
    </div>
  );
};

interface TabsTriggerProps extends HTMLAttributes<HTMLButtonElement> {
  value: string;
  children: ReactNode;
}

export const TabsTrigger = ({ value, children, className, ...props }: TabsTriggerProps) => {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === value;

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => setActiveTab(value)}
      className={cn(
        'px-4 py-2 font-mono text-sm rounded-md transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-cyber-primary/50',
        isActive
          ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30'
          : 'text-gray-400 hover:text-gray-200 hover:bg-void-800/50',
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

interface TabsContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
  children: ReactNode;
}

export const TabsContent = ({ value, children, className, ...props }: TabsContentProps) => {
  const { activeTab } = useTabsContext();

  if (activeTab !== value) {
    return null;
  }

  return (
    <div
      role="tabpanel"
      className={cn('mt-4', className)}
      {...props}
    >
      {children}
    </div>
  );
};
