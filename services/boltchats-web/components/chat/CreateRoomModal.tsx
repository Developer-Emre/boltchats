'use client';
import type React from 'react';
import { useState } from 'react';
import { roomsApi } from '@/lib/api';
import type { Room } from '@/types';

interface CreateRoomModalProps {
  onClose: () => void;
  onCreated: (room: Room) => void;
}

export function CreateRoomModal({
  onClose,
  onCreated,
}: CreateRoomModalProps): React.JSX.Element {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const room = await roomsApi.create({
        name: name.trim(),
        description: description.trim(),
        is_private: isPrivate,
      });
      onCreated(room);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create channel');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg border border-zinc-800 bg-[#111113] p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-5 text-base font-semibold text-zinc-100">
          Create a Channel
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium uppercase tracking-widest text-zinc-500">
              Channel Name
            </label>
            <div className="flex items-center gap-2 rounded border border-zinc-800 bg-[#0c0c0e] px-3 py-2 focus-within:border-indigo-600">
              <span className="text-zinc-600">#</span>
              <input
                autoFocus
                type="text"
                maxLength={64}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. general"
                className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-700 outline-none"
              />
            </div>
          </div>

          {/* Description */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium uppercase tracking-widest text-zinc-500">
              Description{' '}
              <span className="normal-case tracking-normal text-zinc-700">
                (optional)
              </span>
            </label>
            <input
              type="text"
              maxLength={256}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this channel about?"
              className="rounded border border-zinc-800 bg-[#0c0c0e] px-3 py-2 text-sm text-zinc-100 placeholder-zinc-700 outline-none focus:border-indigo-600"
            />
          </div>

          {/* Private toggle */}
          <label className="flex cursor-pointer items-center justify-between rounded border border-zinc-800 px-3 py-2.5">
            <span className="text-sm text-zinc-300">Private channel</span>
            <button
              type="button"
              role="switch"
              aria-checked={isPrivate}
              onClick={() => setIsPrivate((v) => !v)}
              className={[
                'relative h-5 w-9 rounded-full transition-colors',
                isPrivate ? 'bg-indigo-600' : 'bg-zinc-700',
              ].join(' ')}
            >
              <span
                className={[
                  'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform',
                  isPrivate ? 'translate-x-4' : 'translate-x-0.5',
                ].join(' ')}
              />
            </button>
          </label>

          {error && (
            <p className="text-xs text-red-400">{error}</p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="rounded px-4 py-1.5 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !name.trim()}
              className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating…' : 'Create Channel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
