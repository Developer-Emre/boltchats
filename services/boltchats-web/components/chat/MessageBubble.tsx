'use client';

import type React from 'react';
import { useState } from 'react';
import { Avatar } from '@/components/ui/Avatar';
import { useUserById } from '@/hooks/useUser';
import type { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
  isMine: boolean;
  onEdit?: (messageId: string, content: string) => Promise<void>;
  onDelete?: (messageId: string) => Promise<void>;
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
  onEdit,
  onDelete,
}: MessageBubbleProps): React.JSX.Element {
  const { user: sender } = useUserById(message.sender_id);
  const displayName = sender?.username ?? message.sender_id.slice(0, 8);
  const [showActions, setShowActions] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEdit = async (): Promise<void> => {
    if (!onEdit || !editContent.trim()) return;
    setError(null);
    try {
      setIsDeleting(true);
      await onEdit(message.id, editContent);
      setIsEditing(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to edit message';
      setError(msg);
      console.error('Edit error:', msg);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDelete = async (): Promise<void> => {
    if (!onDelete) return;
    if (!confirm('Delete this message?')) return;
    setError(null);
    try {
      setIsDeleting(true);
      await onDelete(message.id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete message';
      setError(msg);
      console.error('Delete error:', msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className={`flex gap-2 ${isMine ? 'flex-row-reverse' : 'flex-row'}`}>
      <Avatar
        username={displayName}
        size="xs"
      />

      <div
        className={`flex max-w-[68%] flex-col gap-1 ${isMine ? 'items-end' : 'items-start'}`}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        {!isMine && <SenderLabel userId={message.sender_id} />}

        {isEditing ? (
          <div className="flex gap-1 w-full flex-col">
            {error && (
              <div className="text-xs bg-red-900/50 text-red-300 px-2 py-1 rounded">
                {error}
              </div>
            )}
            <div className="flex gap-1">
              <input
                type="text"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="flex-1 rounded px-2 py-1 text-sm bg-zinc-700 text-white border border-indigo-500"
                disabled={isDeleting}
                autoFocus
              />
              <button
                onClick={handleEdit}
                disabled={isDeleting}
                className="px-2 py-1 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded disabled:opacity-50"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setError(null);
                }}
                disabled={isDeleting}
                className="px-2 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 text-white rounded disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div
              className={[
                'rounded px-3 py-2 text-sm leading-relaxed break-words relative group',
                isMine
                  ? 'bg-indigo-600 text-white'
                  : 'bg-zinc-800 text-zinc-100 border border-zinc-700/60',
              ].join(' ')}
            >
              {message.content}

              {isMine && showActions && message.confirmed !== false && (
                <div className="absolute -right-14 top-0 flex gap-1 bg-zinc-900 rounded p-1 shadow-lg z-10">
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-2 py-1 text-xs hover:bg-zinc-700 text-zinc-300 rounded"
                  >
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    className="px-2 py-1 text-xs hover:bg-red-900/50 text-red-400 rounded"
                  >
                    Delete
                  </button>
                </div>
              )}
              {isMine && message.confirmed === false && (
                <div className="absolute -right-20 top-0 text-xs text-zinc-500 font-mono">
                  saving…
                </div>
              )}
            </div>
          </>
        )}

        <span className="px-1 text-[10px] font-mono text-zinc-700">
          {formatTime(message.created_at)}
          {message.edited_at && <span className="ml-1">(edited)</span>}
        </span>
      </div>
    </div>
  );
}
