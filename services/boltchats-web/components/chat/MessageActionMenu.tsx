'use client';

import type React from 'react';
import { useEffect, useRef, useState } from 'react';
import EmojiPicker from 'emoji-picker-react';
import { Tooltip } from '../ui/Tooltip';

interface MessageActionMenuProps {
  messageId: string;
  isMine: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
  onAddReaction?: (emoji: string) => Promise<void>;
}

export function MessageActionMenu({
  messageId,
  isMine,
  onEdit,
  onDelete,
  onAddReaction,
}: MessageActionMenuProps): React.JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent): void {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowEmojiPicker(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleReaction = async (emoji: string): Promise<void> => {
    if (onAddReaction) {
      await onAddReaction(emoji);
    }
    setShowEmojiPicker(false);
    setIsOpen(false);
  };

  return (
    <div ref={menuRef} className="relative">
      <Tooltip content="Message actions">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-1 hover:bg-zinc-700 rounded transition-colors opacity-0 group-hover:opacity-100"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="currentColor"
            className="text-zinc-400"
          >
            <path d="M8 2a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 6a1.5 1.5 0 110-3 1.5 1.5 0 010 3z" />
          </svg>
        </button>
      </Tooltip>

      {isOpen && (
        <div className="absolute right-0 top-8 bg-zinc-800 border border-zinc-700 rounded-lg shadow-lg z-40 min-w-[180px] overflow-hidden">
          {/* React Button */}
          {!isMine && (
            <div className="relative">
              <Tooltip content="Add reaction">
                <button
                  onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                  className="w-full text-left px-4 py-2 hover:bg-zinc-700 text-sm text-zinc-300 flex items-center gap-2 transition-colors"
                >
                  <span>😊</span>
                  React
                </button>
              </Tooltip>

              {/* Emoji Picker Popup */}
              {showEmojiPicker && (
                <div className="absolute top-0 right-full mr-2 z-50">
                  <EmojiPicker
                    open={showEmojiPicker}
                    onEmojiClick={(e) => handleReaction(e.emoji)}
                    width={300}
                    height={400}
                    previewConfig={{ showPreview: false }}
                    searchPlaceholder="Search emoji..."
                  />
                </div>
              )}
            </div>
          )}

          {/* Edit Button - Only for own messages */}
          {isMine && (
            <Tooltip content="Edit message">
              <button
                onClick={() => {
                  onEdit?.();
                  setIsOpen(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-zinc-700 text-sm text-zinc-300 flex items-center gap-2 transition-colors border-b border-zinc-700"
              >
                <span>✏️</span>
                Edit
              </button>
            </Tooltip>
          )}

          {/* Delete Button - Only for own messages */}
          {isMine && (
            <Tooltip content="Delete message">
              <button
                onClick={() => {
                  onDelete?.();
                  setIsOpen(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-red-900/30 text-sm text-red-400 flex items-center gap-2 transition-colors"
              >
                <span>🗑️</span>
                Delete
              </button>
            </Tooltip>
          )}

          {/* React Button for own messages too (can react to own msg) */}
          {isMine && (
            <div className="relative border-t border-zinc-700">
              <Tooltip content="Add reaction">
                <button
                  onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                  className="w-full text-left px-4 py-2 hover:bg-zinc-700 text-sm text-zinc-300 flex items-center gap-2 transition-colors"
                >
                  <span>😊</span>
                  React
                </button>
              </Tooltip>

              {/* Emoji Picker Popup */}
              {showEmojiPicker && (
                <div className="absolute top-0 right-full mr-2 z-50">
                  <EmojiPicker
                    open={showEmojiPicker}
                    onEmojiClick={(e) => handleReaction(e.emoji)}
                    width={300}
                    height={400}
                    previewConfig={{ showPreview: false }}
                    searchPlaceholder="Search emoji..."
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
