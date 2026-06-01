'use client';

import type React from 'react';
import { useCallback, useState } from 'react';
import { useUser } from '@/hooks/useUser';
import { useAuth } from '@/hooks/useAuth';
import { toast } from '@/lib/toast';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';

export default function ProfilePage(): React.JSX.Element {
  const { user, isLoading, updateMe } = useUser();
  const { logout } = useAuth();

  const [username, setUsername] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      const trimmed = username.trim();
      if (!trimmed || trimmed === user?.username) return;
      setIsSaving(true);
      try {
        await updateMe({ username: trimmed });
        setUsername('');
        toast.success('Username updated');
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Update failed');
      } finally {
        setIsSaving(false);
      }
    },
    [username, user, updateMe],
  );

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm rounded-lg border border-zinc-800 bg-zinc-950/80 p-8 shadow-xl">
        {/* Avatar + current info */}
        <div className="mb-8 flex flex-col items-center gap-3">
          {user && <Avatar username={user.username} size="md" isOnline />}
          {isLoading ? (
            <div className="h-4 w-32 animate-pulse rounded bg-zinc-800" />
          ) : (
            <>
              <p className="text-sm font-semibold text-zinc-200">{user?.username}</p>
              <p className="text-xs text-zinc-600">{user?.email}</p>
            </>
          )}
        </div>

        {/* Update username form */}
        <form onSubmit={handleSave} className="flex flex-col gap-4">
          <Input
            label="New username"
            type="text"
            placeholder={user?.username ?? ''}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            minLength={3}
            autoComplete="username"
          />
          <Button
            type="submit"
            isLoading={isSaving}
            className="w-full"
            disabled={!username.trim() || username.trim() === user?.username}
          >
            Save changes
          </Button>
        </form>

        {/* Divider + logout */}
        <div className="mt-6 border-t border-zinc-800 pt-5">
          <button
            onClick={logout}
            className="w-full text-center text-xs text-zinc-700 transition-colors hover:text-red-400"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
