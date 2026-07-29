'use client';

import { useState } from 'react';
import type { Channel, DirectMessageGroup } from '@/types';
import { Button } from '@/components/ui/Button';

interface ChannelSidebarProps {
  channels: Channel[];
  dms: DirectMessageGroup[];
  currentChannelId: string | null;
  currentDmId: string | null;
  onSelectChannel: (channelId: string) => void;
  onSelectDm: (dmId: string) => void;
  onCreateChannel?: () => void;
  isLoadingChannels?: boolean;
}

export function ChannelSidebar({
  channels,
  dms,
  currentChannelId,
  currentDmId,
  onSelectChannel,
  onSelectDm,
  onCreateChannel,
  isLoadingChannels = false,
}: ChannelSidebarProps): React.JSX.Element {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!isExpanded) {
    return (
      <div className="w-12 bg-zinc-950 border-r border-zinc-800 flex flex-col items-center py-4">
        <button
          onClick={() => setIsExpanded(true)}
          className="p-2 hover:bg-zinc-800 rounded transition-colors"
          title="Expand channels"
        >
          ◀
        </button>
      </div>
    );
  }

  return (
    <div className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <h3 className="font-semibold text-white text-sm">Channels</h3>
        <div className="flex gap-1">
          <button
            onClick={onCreateChannel}
            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors"
            title="Create channel"
          >
            +
          </button>
          <button
            onClick={() => setIsExpanded(false)}
            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors"
            title="Collapse"
          >
            ▶
          </button>
        </div>
      </div>

      {/* Channels list */}
      <div className="flex-1 overflow-y-auto">
        {isLoadingChannels ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-4 w-4 rounded-full border-2 border-indigo-600 border-t-transparent animate-spin" />
          </div>
        ) : channels.length === 0 ? (
          <div className="p-4 text-center text-sm text-zinc-400">
            No channels yet
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {channels.map((channel) => (
              <button
                key={channel.id}
                onClick={() => onSelectChannel(channel.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
                  currentChannelId === channel.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-zinc-300 hover:bg-white/10 hover:text-white'
                }`}
                title={channel.description}
              >
                <span className="text-base">{channel.type === 'private' ? '🔒' : '#'}</span>
                <span className="truncate">{channel.name}</span>
                {channel.is_archived && (
                  <span className="text-xs text-zinc-400 ml-auto">archived</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* DMs section */}
      {dms.length > 0 && (
        <div className="border-t border-zinc-800">
          <div className="px-4 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Direct Messages
          </div>
          <div className="space-y-1 p-2 pb-4">
            {dms.map((dm) => {
              const participantNames = dm.participants
                .slice(0, 2)
                .map((p) => p.split('@')[0])
                .join(', ');

              return (
                <button
                  key={dm.id}
                  onClick={() => onSelectDm(dm.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
                    currentDmId === dm.id
                      ? 'bg-indigo-600 text-white'
                      : 'text-zinc-300 hover:bg-white/10 hover:text-white'
                  }`}
                  title={participantNames}
                >
                  <span className="text-base">💬</span>
                  <span className="truncate">{participantNames}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
