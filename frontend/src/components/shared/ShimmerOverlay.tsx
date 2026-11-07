import React from 'react';

interface ShimmerOverlayProps {
  /* Component logic */
  show: boolean;
  /* Component logic */
  opacity?: number;
  /* Component logic */
  rounded?: 'card' | 'lg' | 'md' | 'sm' | 'none';
}

/**
 * 
 * """"
 *  Skeleton 
 */
export const ShimmerOverlay: React.FC<ShimmerOverlayProps> = ({
  show,
  opacity = 0.4,
  rounded = 'card',
}) => {
  if (!show) return null;

  const roundedClass = {
    card: 'rounded-card',
    lg: 'rounded-lg',
    md: 'rounded-md',
    sm: 'rounded-sm',
    none: '',
  }[rounded];

  return (
    <div className={`absolute inset-0 ${roundedClass} overflow-hidden pointer-events-none z-10`}>
      <div 
        className="absolute inset-0 bg-gradient-to-r from-gray-200 via-banana-50 to-gray-200 animate-shimmer" 
        style={{ 
          backgroundSize: '200% 100%',
          opacity 
        }}
      />
    </div>
  );
};