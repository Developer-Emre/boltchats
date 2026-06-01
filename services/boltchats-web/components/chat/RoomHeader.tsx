import type React from 'react';
import type { Room } from '@/types';

interface RoomHeaderProps {
  room: Room | null;
  roomId: string;
  connected: boolean;
}

function StatusDot({ connected }: { connected: boolean }): React.JSX.Element {
  return (
    <span className="flex items-center gap-1.5 text-xs font-mono">
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          connected ? 'bg-green-400' : 'bg-zinc-600 animate-pulse'
        }`}
      />
      <span className={connected ? 'text-zinc-500' : 'text-zinc-700'}>
        {connected ? 'live' : 'connecting…'}
      </span>
    </span>
  );
}

export function RoomHeader({ room, roomId, connected }: RoomHeaderProps): React.JSX.Element {
  const name = room?.name ?? roomId;
  const description = room?.description;
  const memberCount = room?.member_ids.length ?? null;

  return (
    <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-zinc-800 px-4 gap-4">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex min-w-0 flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-zinc-600">#</span>
            <h1 className="truncate text-sm font-semibold text-zinc-200">{name}</h1>
            {memberCount !== null && (
              <span className="ml-1 text-[10px] font-mono text-zinc-700">
                {memberCount} {memberCount === 1 ? 'member' : 'members'}
              </span>
            )}
          </div>
          {description && (
            <p className="truncate text-[11px] text-zinc-600">{description}</p>
          )}
        </div>
      </div>
      <StatusDot connected={connected} />
    </header>
  );
}
