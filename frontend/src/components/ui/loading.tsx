import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingSpinner({ className, size = 'md' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-neutral-300 border-t-primary-600',
        sizeClasses[size],
        className
      )}
    />
  );
}

interface LoadingSkeletonProps {
  className?: string;
  lines?: number;
}

export function LoadingSkeleton({ className, lines = 3 }: LoadingSkeletonProps) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="h-4 bg-neutral-200 rounded animate-pulse"
          style={{
            width: `${Math.random() * 40 + 60}%`,
          }}
        />
      ))}
    </div>
  );
}

interface LoadingCardProps {
  className?: string;
}

export function LoadingCard({ className }: LoadingCardProps) {
  return (
    <div className={cn('p-6 border border-neutral-200 rounded-xl bg-white', className)}>
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-neutral-200 rounded w-3/4" />
        <div className="space-y-2">
          <div className="h-4 bg-neutral-200 rounded" />
          <div className="h-4 bg-neutral-200 rounded w-5/6" />
        </div>
        <div className="flex space-x-2">
          <div className="h-6 bg-neutral-200 rounded w-16" />
          <div className="h-6 bg-neutral-200 rounded w-20" />
        </div>
      </div>
    </div>
  );
}

interface LoadingPageProps {
  title?: string;
  description?: string;
}

export function LoadingPage({ title = 'Loading...', description }: LoadingPageProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
      <LoadingSpinner size="lg" />
      <div className="text-center">
        <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>
        {description && (
          <p className="text-sm text-neutral-600 mt-1">{description}</p>
        )}
      </div>
    </div>
  );
}

// Export principal pour compatibilité
export const Loading = LoadingSpinner;