import { cn } from '@/utils/cn';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Loading = ({ size = 'md', className }: LoadingProps) => {
  return (
    <div className={cn('flex items-center justify-center', className)}>
      <div
        className={cn('animate-spin rounded-full border-2 border-void-700 border-t-cyber-primary', {
          'w-4 h-4': size === 'sm',
          'w-8 h-8': size === 'md',
          'w-12 h-12': size === 'lg',
        })}
      />
    </div>
  );
};

export const PageLoading = () => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-void-950">
      <div className="flex flex-col items-center gap-4">
        <Loading size="lg" />
        <p className="font-mono text-sm text-gray-400 animate-pulse">Initializing...</p>
      </div>
    </div>
  );
};
