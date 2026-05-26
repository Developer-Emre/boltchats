import type React from 'react';
interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap: Record<NonNullable<LogoProps['size']>, string> = {
  sm: 'text-lg',
  md: 'text-xl',
  lg: 'text-3xl',
};

export function Logo({ size = 'md' }: LogoProps): React.JSX.Element {
  return (
    <span className={`select-none font-bold tracking-tight ${sizeMap[size]}`}>
      <span className="text-indigo-400">⚡</span>
      <span className="text-white">bolt</span>
      <span className="text-indigo-400">chats</span>
    </span>
  );
}
