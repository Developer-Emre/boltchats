'use client';

import type React from 'react';
import { Avatar } from '@/components/ui/Avatar';
import { useRoomPresence } from '@/hooks/usePresence';
import { useUserById } from '@/hooks/useUser';

interface MemberItemProps {
  userId: string;
  isOnline: boolean;
}

function MemberItem({ userId, isOnline }: MemberItemProps): React.JSX.Element {
  const { user } = useUserById(userId);

  return (
    <li className="flex items-center gap-2 px-3 py-1.5">
      <Avatar username={user?.username ?? '?'} size="xs" isOnline={isOnline} />
      <span className="truncate text-xs text-zinc-400">
        {user?.username ?? <span className="text-zinc-700">loading…</span>}
      </span>
    </li>
  );
}

interface MemberListProps {
  roomId: string;
  memberIds: string[];
}

export function MemberList({ roomId, memberIds }: MemberListProps): React.JSX.Element {
  const { presence, isLoading } = useRoomPresence(roomId);

  const onlineSet = new Set(presence?.online_user_ids ?? []);

  // Sort: online first, then offline
  const sorted = [...memberIds].sort((a, b) => {
    const aOn = onlineSet.has(a) ? 0 : 1;
    const bOn = onlineSet.has(b) ? 0 : 1;
    return aOn - bOn;
  });

  const onlineCount = isLoading ? null : (presence?.count ?? 0);

  return (
    <aside className="flex h-full w-48 flex-shrink-0 flex-col border-l border-zinc-800 bg-[#0c0c0e]">
      <div className="flex h-14 items-center border-b border-zinc-800 px-4">
        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">
          Members
          {onlineCount !== null && (
            <span className="ml-1.5 font-mono text-green-500">{onlineCount} online</span>
          )}
        </span>
      </div>

      <ul className="flex flex-col overflow-y-auto py-2">
        {sorted.map((id) => (
          <MemberItem key={id} userId={id} isOnline={onlineSet.has(id)} />
        ))}

        {memberIds.length === 0 && (
          <li className="px-4 py-2 text-xs text-zinc-700">No members yet</li>
        )}
      </ul>
    </aside>
  );
}
