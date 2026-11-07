import React from 'react';
import { cn } from '@/utils';
import type { Page } from '@/types';
import { usePageStatus, type PageStatusContext } from '@/hooks/usePageStatus';

interface ContextualStatusBadgeProps {
  page: Page;
  /* Component logic */
  context?: PageStatusContext;
  /* Component logic */
  showDescription?: boolean;
}

/**
 * 
 * 
 * - : 
 * - : 
 * - : 
 */
export const ContextualStatusBadge: React.FC<ContextualStatusBadgeProps> = ({
  page,
  context = 'full',
  showDescription = true,
}) => {
  const { status, label, description } = usePageStatus(page, context);

  const statusConfig: Record<string, string> = {
    DRAFT: 'bg-gray-100 dark:bg-background-secondary text-gray-600 dark:text-foreground-tertiary',
    GENERATING_DESCRIPTION: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 animate-pulse',
    DESCRIPTION_GENERATED: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    QUEUED: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 animate-pulse',
    GENERATING: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 animate-pulse',
    COMPLETED: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    FAILED: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium',
        statusConfig[status]
      )}
      title={showDescription ? description : undefined}
    >
      {label}
    </span>
  );
};