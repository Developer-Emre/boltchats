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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect((): void => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
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

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t border-zinc-800 bg-[#0c0c0e] px-4 py-3"
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={`Message #${roomName}`}
        rows={1}
        className={[
          'flex-1 resize-none overflow-hidden rounded border bg-zinc-900 px-3 py-2',
          'text-sm text-zinc-100 placeholder-zinc-600',
          'transition-colors focus:outline-none focus:ring-1',
          'border-zinc-700 focus:border-indigo-500 focus:ring-indigo-500/20',
          'disabled:opacity-50 min-h-[40px]',
        ].join(' ')}
      />

      <button
        type="submit"
        disabled={disabled || !value.trim()}
        aria-label="Send"
        className={[
          'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded',
          'border border-indigo-700 bg-indigo-600/20 text-indigo-400',
          'transition-colors hover:bg-indigo-600 hover:text-white',
          'disabled:opacity-40 disabled:cursor-not-allowed',
        ].join(' ')}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
          aria-hidden="true"
        >
          <path d="M12.5 7L1.5 1.5L4.5 7L1.5 12.5L12.5 7Z" fill="currentColor" />
        </svg>
      </button>
    </form>
  );
}