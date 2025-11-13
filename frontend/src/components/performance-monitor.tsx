'use client';

import { useEffect } from 'react';
import { logPerformanceMetrics } from '@/lib/performance';

/**
 * Performance monitoring component
 * Only active in development mode
 */
export function PerformanceMonitor() {
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // Log performance metrics after page load
      const timer = setTimeout(() => {
        logPerformanceMetrics();
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, []);

  return null;
}
