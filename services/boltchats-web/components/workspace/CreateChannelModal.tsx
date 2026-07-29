'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface CreateChannelModalProps {
  onClose: () => void;
  onCreateChannel: (name: string, description: string, type: 'public' | 'private') => Promise<void>;
  isLoading?: boolean;
}

export function CreateChannelModal({
  onClose,
  onCreateChannel,
  isLoading = false,
}: CreateChannelModalProps): React.JSX.Element {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<'public' | 'private'>('public');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Channel name is required');
      return;
    }

    try {
      setError(null);
      await onCreateChannel(name, description, type);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create channel');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-700">
          <h2 className="text-lg font-semibold text-white">Create Channel</h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 bg-red-600/10 border border-red-800/50 rounded text-sm text-red-400">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Channel Name *
            </label>
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., general, random, announcements"
              disabled={isLoading}
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this channel about?"
              disabled={isLoading}
              className="w-full px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Channel Type
            </label>
            <div className="space-y-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="type"
                  value="public"
                  checked={type === 'public'}
                  onChange={(e) => setType(e.target.value as 'public' | 'private')}
                  className="w-4 h-4"
                />
                <span className="flex items-center gap-2 text-sm text-zinc-300">
                  <span>🌐</span>
                  <span>Public</span>
                  <span className="text-xs text-zinc-400">Anyone can join</span>
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="type"
                  value="private"
                  checked={type === 'private'}
                  onChange={(e) => setType(e.target.value as 'public' | 'private')}
                  className="w-4 h-4"
                />
                <span className="flex items-center gap-2 text-sm text-zinc-300">
                  <span>🔒</span>
                  <span>Private</span>
                  <span className="text-xs text-zinc-400">Invite only</span>
                </span>
              </label>
            </div>
          </div>
        </form>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-zinc-700 flex gap-3 justify-end">
          <Button
            variant="ghost"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            isLoading={isLoading}
          >
            Create
          </Button>
        </div>
      </div>
    </div>
  );
}
