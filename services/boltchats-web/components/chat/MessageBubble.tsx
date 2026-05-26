import type React from 'react';
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

export function MessageBubble({
  message,
  isMine,
}: MessageBubbleProps): React.JSX.Element {
  return (
    <div className={`flex gap-2 ${isMine ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar dot */}
      <div
        className={`mt-1 h-6 w-6 flex-shrink-0 rounded flex items-center justify-center text-[10px] font-bold
          ${isMine ? 'bg-indigo-600/30 text-indigo-300' : 'bg-zinc-700 text-zinc-400'}`}
      >
        {message.sender_id.slice(0, 1).toUpperCase()}
      </div>

      <div
        className={`flex max-w-[68%] flex-col gap-1 ${isMine ? 'items-end' : 'items-start'}`}
      >
        {!isMine && (
          <span className="text-[11px] font-mono text-zinc-500 px-1">
            {message.sender_id}
          </span>
        )}

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
