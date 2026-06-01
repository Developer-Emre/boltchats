import type React from 'react';

interface AvatarProps {
  username: string;
  size?: 'xs' | 'sm' | 'md';
  isOnline?: boolean;
}

const SIZE = {
  xs: 'h-5 w-5 text-[9px]',
  sm: 'h-7 w-7 text-[11px]',
  md: 'h-9 w-9 text-sm',
} as const;

const DOT = {
  xs: 'h-1.5 w-1.5 -right-px -bottom-px',
  sm: 'h-2 w-2 -right-0.5 -bottom-0.5',
  md: 'h-2.5 w-2.5 -right-0.5 -bottom-0.5',
} as const;

export function Avatar({
  username,
  size = 'sm',
  isOnline,
}: AvatarProps): React.JSX.Element {
  const initial = username.slice(0, 1).toUpperCase();

  return (
    <span className="relative inline-flex flex-shrink-0">
      <span
        className={[
          SIZE[size],
          'flex items-center justify-center rounded-full bg-indigo-600/30 font-bold text-indigo-300',
        ].join(' ')}
      >
        {initial}
      </span>
      {isOnline !== undefined && (
        <span
          className={[
            DOT[size],
            'absolute rounded-full border border-[#111113]',
            isOnline ? 'bg-green-400' : 'bg-zinc-600',
          ].join(' ')}
        />
      )}
    </span>
  );
}
