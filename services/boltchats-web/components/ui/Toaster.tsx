'use client';

import { useEffect, useState } from 'react';
import type React from 'react';
import { subscribeToasts, type ToastItem } from '@/lib/toast';

const STYLES: Record<ToastItem['type'], string> = {
  success: 'border-green-700/50 bg-green-950/80 text-green-300',
  error:   'border-red-700/50   bg-red-950/80   text-red-300',
  info:    'border-zinc-700/50  bg-zinc-900/90  text-zinc-300',
};

const ICON: Record<ToastItem['type'], string> = {
  success: '✓',
  error:   '✕',
  info:    'i',
};

export function Toaster(): React.JSX.Element {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => subscribeToasts(setToasts), []);

  if (toasts.length === 0) return <></>;

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={[
            'pointer-events-auto flex items-center gap-2.5 rounded border px-3.5 py-2.5',
            'text-sm shadow-lg backdrop-blur-sm animate-in slide-in-from-right-4 fade-in',
            STYLES[t.type],
          ].join(' ')}
        >
          <span className="flex-shrink-0 text-xs font-bold">{ICON[t.type]}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}
