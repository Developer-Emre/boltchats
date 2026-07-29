'use client';

import { useState } from 'react';
import type { Workspace } from '@/types';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';

interface WorkspaceSwitcherProps {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  onSelectWorkspace: (workspaceId: string) => void;
  onCreateWorkspace?: () => void;
  isLoading?: boolean;
}

export function WorkspaceSwitcher({
  workspaces,
  currentWorkspace,
  onSelectWorkspace,
  onCreateWorkspace,
  isLoading = false,
}: WorkspaceSwitcherProps): React.JSX.Element {
  const [isOpen, setIsOpen] = useState(false);

  if (isLoading || !currentWorkspace) {
    return (
      <div className="flex items-center justify-center w-full h-12 bg-zinc-900 border-b border-zinc-800">
        <div className="h-4 w-4 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin" />
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors rounded border border-zinc-800 hover:border-zinc-700"
      >
        <Avatar
          username={currentWorkspace.name}
          size="sm"
        />
        <div className="flex-1 text-left">
          <div className="text-sm font-semibold text-white truncate">
            {currentWorkspace.name}
          </div>
          <div className="text-xs text-zinc-400 truncate">
            {currentWorkspace.members.length} member{currentWorkspace.members.length !== 1 ? 's' : ''}
          </div>
        </div>
        <div className={`text-zinc-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          ▼
        </div>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 right-0 z-20 mt-2 bg-zinc-800 border border-zinc-700 rounded shadow-lg max-h-96 overflow-y-auto">
            {workspaces.length === 0 ? (
              <div className="p-4 text-center text-sm text-zinc-400">
                No workspaces yet
              </div>
            ) : (
              <>
                {workspaces.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => {
                      onSelectWorkspace(ws.id);
                      setIsOpen(false);
                    }}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-white/5 transition-colors ${
                      ws.id === currentWorkspace.id ? 'bg-indigo-600/20 border-l-2 border-indigo-600' : ''
                    }`}
                  >
                    <Avatar
                      username={ws.name}
                      size="sm"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate">
                        {ws.name}
                      </div>
                      <div className="text-xs text-zinc-400 truncate">
                        {ws.members.length} members
                      </div>
                    </div>
                    {ws.id === currentWorkspace.id && (
                      <span className="text-indigo-400 text-xs font-semibold">✓</span>
                    )}
                  </button>
                ))}

                <div className="border-t border-zinc-700 p-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      onCreateWorkspace?.();
                      setIsOpen(false);
                    }}
                    className="w-full text-xs"
                  >
                    + New Workspace
                  </Button>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
