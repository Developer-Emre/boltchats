'use client';
import type React from 'react';

import {
  type FormEvent,
  type KeyboardEvent,
  type ChangeEvent,
  useEffect,
  useRef,
  useState,
  useCallback,
} from 'react';
import EmojiPicker from 'emoji-picker-react';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  roomName: string;
}

export function MessageInput({
  onSend,
  disabled = false,
  roomName,
}: MessageInputProps): React.JSX.Element {
  const [value, setValue] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [isBoldActive, setIsBoldActive] = useState(false);
  const [isItalicActive, setIsItalicActive] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea (48px min, 120px max)
  useEffect((): void => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const newHeight = Math.min(el.scrollHeight, 120);
    el.style.height = `${newHeight}px`;
  }, [value]);

  const submit = useCallback((): void => {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue('');
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }, [submit]);

  const handleSubmit = useCallback((e: FormEvent): void => {
    e.preventDefault();
    submit();
  }, [submit]);

  const handleChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>): void => {
    setValue(e.target.value);
  }, []);

  const handleSelectEmoji = useCallback((emoji: string): void => {
    setValue((prev) => prev + emoji);
    setTimeout(() => textareaRef.current?.focus(), 0);
  }, []);

  const insertFormatting = useCallback((before: string, after: string = ''): void => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    const newValue =
      value.substring(0, start) + before + selectedText + after + value.substring(end);

    setValue(newValue);

    // Restore cursor position
    setTimeout(() => {
      textarea.selectionStart = start + before.length;
      textarea.selectionEnd = start + before.length + selectedText.length;
      textarea.focus();
    }, 0);
  }, [value]);

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t transition-colors duration-fast"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderColor: 'var(--color-border)',
      }}
    >
      {/* Unified Container with border and padding */}
      <div
        className="mx-3 my-2 rounded-lg border transition-all duration-fast"
        style={{
          backgroundColor: 'var(--color-bg-secondary)',
          borderColor: 'var(--color-border)',
        }}
      >
        {/* Toolbar - Top Row */}
        <div className="flex gap-1 px-2 pt-2 pb-1 border-b" style={{
          borderColor: 'var(--color-border)',
        }}>
          <button
            type="button"
            onClick={() => {
              insertFormatting('**', '**');
              setIsBoldActive(!isBoldActive);
            }}
            className={[
              'h-8 w-8 rounded-sm flex items-center justify-center text-sm transition-colors duration-fast',
              'hover:bg-surface-hover focus:outline-2 focus:outline-offset-2 focus:outline-accent',
              isBoldActive ? 'bg-accent-soft text-accent' : 'bg-transparent text-text-secondary',
            ].join(' ')}
            title="Bold (Cmd+B)"
            disabled={disabled}
          >
            <strong>B</strong>
          </button>

          <button
            type="button"
            onClick={() => {
              insertFormatting('*', '*');
              setIsItalicActive(!isItalicActive);
            }}
            className={[
              'h-8 w-8 rounded-sm flex items-center justify-center text-sm transition-colors duration-fast',
              'hover:bg-surface-hover focus:outline-2 focus:outline-offset-2 focus:outline-accent',
              isItalicActive ? 'bg-accent-soft text-accent' : 'bg-transparent text-text-secondary',
            ].join(' ')}
            title="Italic (Cmd+I)"
            disabled={disabled}
          >
            <em>I</em>
          </button>

          <div className="w-px bg-border mx-1" style={{
            backgroundColor: 'var(--color-border)',
          }} />

          {/* Emoji Picker Button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowEmojiPicker(!showEmojiPicker)}
              disabled={disabled}
              className="h-8 w-8 rounded-sm flex items-center justify-center text-sm transition-colors duration-fast bg-transparent text-text-secondary hover:bg-surface-hover focus:outline-2 focus:outline-offset-2 focus:outline-accent disabled:opacity-50"
              title="Add emoji"
            >
              😊
            </button>
            {showEmojiPicker && (
              <div className="absolute bottom-10 left-0 z-50">
                <EmojiPicker
                  open={showEmojiPicker}
                  onEmojiClick={(e) => {
                    handleSelectEmoji(e.emoji);
                    setShowEmojiPicker(false);
                  }}
                  width={300}
                  height={400}
                  previewConfig={{ showPreview: false }}
                  searchPlaceholder="Search emoji..."
                />
              </div>
            )}
          </div>

          {/* File Upload Button */}
          <button
            type="button"
            className="h-8 w-8 rounded-sm flex items-center justify-center text-sm transition-colors duration-fast bg-transparent text-text-secondary hover:bg-surface-hover focus:outline-2 focus:outline-offset-2 focus:outline-accent disabled:opacity-50"
            title="Attach file"
            disabled={disabled}
          >
            📎
          </button>
        </div>

        {/* Input + Send Button - Bottom Row */}
        <div className="flex items-end gap-2 px-2 py-2">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={`Message #${roomName}`}
            rows={1}
            className={[
              'flex-1 resize-none overflow-hidden bg-transparent',
              'text-message text-text-primary placeholder-text-tertiary italic',
              'focus:outline-none disabled:opacity-50',
              'min-h-[32px] max-h-[120px]',
            ].join(' ')}
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            aria-label="Send"
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-sm transition-colors duration-fast focus:outline-2 focus:outline-offset-2 focus:outline-accent"
            style={{
              backgroundColor: disabled || !value.trim() ? 'var(--color-gray-300)' : 'var(--color-accent)',
              color: disabled || !value.trim() ? 'var(--color-gray-600)' : 'white',
              cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
              opacity: disabled || !value.trim() ? 0.6 : 1,
            }}
            onMouseEnter={(e) => {
              if (!disabled && value.trim()) {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-accent-hover)';
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled && value.trim()) {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-accent)';
              }
            }}
            onMouseDown={(e) => {
              if (!disabled && value.trim()) {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-accent-active)';
              }
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path d="M14 8L2 2L5 8L2 14L14 8Z" fill="currentColor" />
            </svg>
          </button>
        </div>
      </div>
    </form>
  );
}