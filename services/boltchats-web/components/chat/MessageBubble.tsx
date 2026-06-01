'use client';

import type React from 'react';
import { Avatar } from '@/components/ui/Avatar';
import { useUserById } from '@/hooks/useUser';
import type { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
  isMine: boolean;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

function SenderLabel({ userId }: { userId: string }): React.JSX.Element {
  const { user } = useUserById(userId);
  return (
    <span className="text-[11px] font-mono text-zinc-500 px-1">
      {user?.username ?? <span className="text-zinc-700">…</span>}
    </span>
  );
}

export function MessageBubble({
  message,
  isMine,
}: MessageBubbleProps): React.JSX.Element {
  const { user: sender } = useUserById(message.sender_id);
  const displayName = sender?.username ?? message.sender_id.slice(0, 8);

  return (
    <div className={`flex gap-2 ${isMine ? 'flex-row-reverse' : 'flex-row'}`}>
      <Avatar
        username={displayName}
        size="xs"
        /* no online dot in message bubbles — presence is shown in MemberList */
      />

      <div
        className={`flex max-w-[68%] flex-col gap-1 ${isMine ? 'items-end' : 'items-start'}`}
      >
        {!isMine && <SenderLabel userId={message.sender_id} />}

        <div
          className={[
            'rounded px-3 py-2 text-sm leading-relaxed break-words',
            isMine
              ? 'bg-indigo-600 text-white'
              : 'bg-zinc-800 text-zinc-100 border border-zinc-700/60',
          ].join(' ')}
        >
          {message.content}
        </div>

        <span className="px-1 text-[10px] font-mono text-zinc-700">
          {formatTime(message.created_at)}
        </span>
      </div>
    </div>
  );
}
