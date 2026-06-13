'use client';

import type React from 'react';
import { useRef } from 'react';
import * as TooltipPrimitive from '@radix-ui/react-tooltip';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
  delayDuration?: number;
}

const TooltipProvider = TooltipPrimitive.Provider;

export { TooltipProvider };

export function Tooltip({
  content,
  children,
  side = 'left',
  delayDuration = 200,
}: TooltipProps): React.JSX.Element {
  const triggerRef = useRef<HTMLButtonElement>(null);

  return (
    <TooltipPrimitive.Root delayDuration={delayDuration}>
      <TooltipPrimitive.Trigger ref={triggerRef} asChild>
        {children}
      </TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          side={side}
          sideOffset={8}
          className="relative z-50 bg-zinc-900 text-zinc-100 text-xs px-2 py-1 rounded shadow-md border border-zinc-700 pointer-events-none animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=left]:translate-x-[-4px] data-[side=right]:translate-x-[4px]"
        >
          {content}
          <TooltipPrimitive.Arrow className="fill-zinc-900" />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}
