'use client';

import { useState } from 'react';
import type { Channel, Workspace, WorkspaceMember } from '@/types';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';

interface WorkspaceMemberListProps {
  workspace: Workspace | null;
  channel?: Channel | null;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  isLoadingMembers?: boolean;
}

export function WorkspaceMemberList({
  workspace,
  channel,
  isExpanded = true,
  onToggleExpand,
  isLoadingMembers = false,
}: WorkspaceMemberListProps): React.JSX.Element {
  if (!isExpanded) {
    return (
      <div className="w-12 bg-zinc-950 border-l border-zinc-800 flex flex-col items-center py-4">
        <button
          onClick={onToggleExpand}
          className="p-2 hover:bg-zinc-800 rounded transition-colors"
          title="Expand members"
        >
          ▶
        </button>
      </div>
    );
  }

  const entity = channel || workspace;
  const members = entity?.members || [];
  const title = channel ? 'Channel Members' : 'Workspace Members';

  const getMemberRole = (member: WorkspaceMember): string => {
    return member.role.charAt(0).toUpperCase() + member.role.slice(1);
  };

  const getRoleColor = (role: string): string => {
    switch (role) {
      case 'owner':
        return 'text-red-400';
      case 'admin':
        return 'text-yellow-400';
      case 'member':
        return 'text-blue-400';
      case 'guest':
        return 'text-gray-400';
      default:
        return 'text-zinc-400';
    }
  };

  return (
    <div className="w-64 bg-zinc-950 border-l border-zinc-800 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <h3 className="font-semibold text-white text-sm">{title}</h3>
        <button
          onClick={onToggleExpand}
          className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors"
          title="Collapse"
        >
          ▶
        </button>
      </div>

      {/* Members list */}
      <div className="flex-1 overflow-y-auto">
        {isLoadingMembers ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-4 w-4 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin" />
          </div>
        ) : typeof members === 'string' || members.length === 0 ? (
          <div className="p-4 text-center text-sm text-zinc-400">
            No members
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {/* Check if members are WorkspaceMember objects (has role) or just user IDs */}
            {members
              .filter((m): m is WorkspaceMember => typeof m === 'object' && 'role' in m)
              .sort((a, b) => {
                const roleOrder: Record<string, number> = {
                  owner: 0,
                  admin: 1,
                  member: 2,
                  guest: 3,
                };
                return (roleOrder[a.role] ?? 99) - (roleOrder[b.role] ?? 99);
              })
              .map((member) => (
                <div
                  key={member.user_id}
                  className="flex items-center gap-2 px-3 py-2 rounded hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  <Avatar
                    username={member.user_id}
                    size="sm"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">
                      {member.user_id.split('@')[0]}
                    </div>
                    <div className={`text-xs font-medium ${getRoleColor(member.role)}`}>
                      {getMemberRole(member)}
                    </div>
                  </div>
                  {!member.is_active && (
                    <span className="text-xs text-zinc-500">offline</span>
                  )}
                </div>
              ))}

            {/* Fallback for string member IDs (channels) */}
            {members
              .filter((m): m is string => typeof m === 'string')
              .map((memberId) => (
                <div
                  key={memberId}
                  className="flex items-center gap-2 px-3 py-2 rounded hover:bg-white/10 transition-colors"
                >
                  <Avatar username={memberId} size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">
                      {memberId.split('@')[0]}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Stats footer */}
      {!isLoadingMembers && (
        <div className="px-4 py-3 border-t border-zinc-800 text-xs text-zinc-400">
          <div className="flex justify-between">
            <span>{members.length} member{members.length !== 1 ? 's' : ''}</span>
            {workspace && (
              <span>{workspace.members.filter((m) => m.is_active).length} online</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
