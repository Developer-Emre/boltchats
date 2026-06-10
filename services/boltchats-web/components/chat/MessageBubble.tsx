'use client';

import type React from 'react';
import { useState } from 'react';
import { Avatar } from '@/components/ui/Avatar';
import { useUserById } from '@/hooks/useUser';
import type { Message } from '@/types';
import { MessageActionMenu } from '@/components/chat/MessageActionMenu';

interface MessageBubbleProps {
  message: Message;
  isMine: boolean;
  currentUserId?: string;
  onEdit?: (messageId: string, content: string) => Promise<void>;
  onDelete?: (messageId: string) => Promise<void>;
  onAddReaction?: (messageId: string, emoji: string) => Promise<void>;
  onRemoveReaction?: (messageId: string, emoji: string) => Promise<void>;
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
  currentUserId,
  onEdit,
  onDelete,
  onAddReaction,
  onRemoveReaction,
}: MessageBubbleProps): React.JSX.Element {
  const { user: sender } = useUserById(message.sender_id);
  const displayName = sender?.username ?? message.sender_id.slice(0, 8);
  const [showActions, setShowActions] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

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
    setError(null);
    try {
      setIsDeleting(true);
      await onDelete(message.id);
      setShowDeleteConfirm(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete message';
      setError(msg);
      console.error('Delete error:', msg);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleAddReaction = async (emoji: string): Promise<void> => {
    if (!onAddReaction) return;
    try {
      await onAddReaction(message.id, emoji);
    } catch (err) {
      console.error('Failed to add reaction:', err);
    }
  };

  const handleRemoveReaction = async (emoji: string): Promise<void> => {
    if (!onRemoveReaction) return;
    try {
      await onRemoveReaction(message.id, emoji);
    } catch (err) {
      console.error('Failed to remove reaction:', err);
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

              {showActions && message.confirmed !== false && (
                <div className="absolute -right-8 top-0">
                  <MessageActionMenu
                    messageId={message.id}
                    isMine={isMine}
                    onEdit={() => setIsEditing(true)}
                    onDelete={() => setShowDeleteConfirm(true)}
                    onAddReaction={handleAddReaction}
                  />
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

        {message.reactions && message.reactions.length > 0 && (
          <div className="flex gap-1 mt-1 flex-wrap px-1">
            {message.reactions.map((reaction) => {
              const hasReacted = currentUserId && reaction.users.includes(currentUserId);
              return (
                <button
                  key={reaction.emoji}
                  onClick={() => {
                    if (hasReacted) {
                      handleRemoveReaction(reaction.emoji);
                    } else {
                      handleAddReaction(reaction.emoji);
                    }
                  }}
                  className={`text-xs px-2 py-1 rounded transition-colors ${
                    hasReacted
                      ? 'bg-indigo-600/50 text-yellow-300 border border-indigo-500'
                      : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
                  }`}
                >
                  {reaction.emoji} {reaction.users.length}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-800 rounded-lg p-6 max-w-sm mx-auto shadow-xl border border-zinc-700">
            <h3 className="text-white font-semibold mb-2">Delete message?</h3>
            <p className="text-zinc-400 text-sm mb-6">
              This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="px-4 py-2 text-sm bg-zinc-700 hover:bg-zinc-600 text-white rounded disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-500 text-white rounded disabled:opacity-50"
              >
                {isDeleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
