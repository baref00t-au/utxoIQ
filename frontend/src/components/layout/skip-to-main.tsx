'use client';

/**
 * Skip to Main Content Link
 * 
 * Provides keyboard users with a way to skip navigation and jump directly to main content.
 * Hidden by default, becomes visible when focused via keyboard navigation.
 * 
 * WCAG 2.1 AA Compliance: Bypass Blocks (2.4.1)
 */
export function SkipToMain() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-brand focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 focus:shadow-lg"
    >
      Skip to main content
    </a>
  );
}
