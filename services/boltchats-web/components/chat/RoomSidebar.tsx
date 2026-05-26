import type React from 'react';
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { Room } from '@/types';
import { Logo } from '@/components/ui/Logo';

interface RoomSidebarProps {
  rooms: Room[];
  onLogout: () => void;
  username: string;
}

export function RoomSidebar({
  rooms,
  onLogout,
  username,
}: RoomSidebarProps): React.JSX.Element {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-56 flex-shrink-0 flex-col border-r border-zinc-800 bg-[#0c0c0e]">
      {/* Header */}
      <div className="flex h-14 items-center border-b border-zinc-800 px-4">
        <Logo size="sm" />
      </div>

      {/* Room list */}
      <nav className="flex flex-1 flex-col overflow-y-auto px-2 py-3">
        <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-widest text-zinc-600">
          Channels
        </p>

        <div className="flex flex-col gap-0.5">
          {rooms.map((room) => {
            const isActive = pathname === `/rooms/${room.id}`;
            return (
              <Link
                key={room.id}
                href={`/rooms/${room.id}`}
                className={[
                  'flex items-center gap-1.5 rounded px-2 py-1.5 text-sm transition-colors',
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-300'
                    : 'text-zinc-500 hover:bg-white/5 hover:text-zinc-200',
                ].join(' ')}
              >
                <span
                  className={`text-xs ${isActive ? 'text-indigo-500' : 'text-zinc-700'}`}
                >
                  #
                </span>
                <span className="truncate">{room.name}</span>
              </Link>
            );
          })}

          {rooms.length === 0 && (
            <p className="px-2 py-1 text-xs text-zinc-700">No rooms yet</p>
          )}
        </div>
      </nav>

      {/* User footer */}
      <div className="flex h-12 items-center justify-between border-t border-zinc-800 px-3 gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <div className="h-5 w-5 flex-shrink-0 rounded bg-indigo-600/30 flex items-center justify-center text-[9px] font-bold text-indigo-300">
            {username.slice(0, 1).toUpperCase()}
          </div>
          <span className="truncate text-xs font-mono text-zinc-500">
            {username}
          </span>
        </div>

        <button
          onClick={onLogout}
          className="flex-shrink-0 text-[11px] text-zinc-700 hover:text-red-400 transition-colors"
        >
          out
        </button>
      </div>
    </aside>
  );
}
