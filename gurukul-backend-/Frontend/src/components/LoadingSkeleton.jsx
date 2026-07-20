import React from 'react';

/**
 * Reusable loading skeleton component
 * Provides visual feedback while content is loading
 */
export const SkeletonBox = ({ className = '', height = 'h-4', width = 'w-full' }) => (
  <div className={`animate-pulse bg-white/10 rounded ${height} ${width} ${className}`}></div>
);

export const SkeletonCard = () => (
  <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/5 animate-pulse">
    <SkeletonBox height="h-6" width="w-3/4" className="mb-4" />
    <SkeletonBox height="h-4" className="mb-2" />
    <SkeletonBox height="h-4" width="w-5/6" />
  </div>
);

export const SkeletonGrid = ({ count = 3 }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} />
    ))}
  </div>
);

export const PageSkeleton = () => (
  <div className="flex flex-col gap-4 sm:gap-6 animate-fade-in">
    {/* Header skeleton */}
    <div className="mb-6">
      <SkeletonBox height="h-8" width="w-1/3" className="mb-2" />
      <SkeletonBox height="h-4" width="w-1/2" />
    </div>
    
    {/* Content skeleton */}
    <SkeletonGrid count={6} />
  </div>
);

export default PageSkeleton;

