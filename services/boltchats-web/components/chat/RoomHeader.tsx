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
          connected ? 'bg-presence-active' : 'bg-text-tertiary animate-pulse'
        }`}
      />
      <span className={connected ? 'text-text-secondary' : 'text-text-tertiary'}>
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
    <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-border px-4 gap-4">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex min-w-0 flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-text-tertiary">#</span>
            <h1 className="truncate text-sm font-semibold text-text-primary">{name}</h1>
            {memberCount !== null && (
              <span className="ml-1 text-[10px] font-mono text-text-tertiary">
                {memberCount} {memberCount === 1 ? 'member' : 'members'}
              </span>
            )}
          </div>
          {description && (
            <p className="truncate text-[11px] text-text-tertiary">{description}</p>
          )}
        </div>
      </div>
      <StatusDot connected={connected} />
    </header>
  );
}
