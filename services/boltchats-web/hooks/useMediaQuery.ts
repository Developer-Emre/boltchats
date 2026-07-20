'use client';

import { useEffect, useState } from 'react';

/**
 * Hook to check if a media query matches.
 * Useful for responsive design without Tailwind's hidden/block.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(false);

  useEffect(() => {
    // Check on mount for SSR safety
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    // Listen for changes
    const handler = (e: MediaQueryListEvent): void => {
      setMatches(e.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
