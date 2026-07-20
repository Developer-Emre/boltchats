'use client';

import type React from 'react';
import { useState, useCallback } from 'react';
import { useMediaQuery } from '@/hooks/useMediaQuery';

export interface Channel {
  id: string;
  name: string;
  isUnread?: boolean;
}

export interface DirectMessage {
  id: string;
  name: string;
  userId: string;
  presence: 'active' | 'idle' | 'offline';
  isUnread?: boolean;
}

export interface SidebarProps {
  channels: Channel[];
  directMessages: DirectMessage[];
  activeRoom?: string;
  onSelectChannel: (channelId: string) => void;
  onSelectDM: (dmId: string) => void;
}

export function Sidebar({
  channels,
  directMessages,
  activeRoom,
  onSelectChannel,
  onSelectDM,
}: SidebarProps): React.JSX.Element {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const isMobile = useMediaQuery('(max-width: 767px)');

  const closeDrawer = useCallback(() => {
    setIsDrawerOpen(false);
  }, []);

  const handleSelectChannel = useCallback(
    (channelId: string) => {
      onSelectChannel(channelId);
      if (isMobile) closeDrawer();
    },
    [isMobile, closeDrawer, onSelectChannel]
  );

  const handleSelectDM = useCallback(
    (dmId: string) => {
      onSelectDM(dmId);
      if (isMobile) closeDrawer();
    },
    [isMobile, closeDrawer, onSelectDM]
  );

  const sidebarContent = (
    <div className="flex h-full flex-col bg-bg-primary text-text-primary">
      {/* Workspace Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-4">
        <h2 className="text-base font-semibold">BoltChats</h2>
        {isMobile && (
          <button
            onClick={closeDrawer}
            className="flex h-8 w-8 items-center justify-center rounded text-text-secondary hover:bg-surface-hover"
            aria-label="Close sidebar"
          >
            ✕
          </button>
        )}
      </div>

      {/* Channels Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-4">
          <h3 className="mb-2 text-label font-semibold uppercase tracking-wider text-text-tertiary">
            Channels
          </h3>
          <nav className="space-y-1">
            {channels.map((channel) => (
              <button
                key={channel.id}
                onClick={() => handleSelectChannel(channel.id)}
                className={[
                  'relative w-full rounded-md px-4 py-2.5 text-left transition-colors duration-fast',
                  'text-message font-normal',
                  activeRoom === channel.id
                    ? 'bg-accent-soft text-accent font-medium'
                    : 'bg-transparent text-text-primary hover:bg-surface-hover',
                  'focus:outline-2 focus:outline-offset-2 focus:outline-accent',
                ].join(' ')}
              >
                <span className="flex items-center gap-2">
                  {channel.isUnread && (
                    <span className="h-2 w-2 rounded-full bg-accent flex-shrink-0" />
                  )}
                  <span>#{channel.name}</span>
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Direct Messages Section */}
        <div className="border-t border-border px-4 py-4">
          <h3 className="mb-2 text-label font-semibold uppercase tracking-wider text-text-tertiary">
            Direct Messages
          </h3>
          <nav className="space-y-1">
            {directMessages.map((dm) => (
              <button
                key={dm.id}
                onClick={() => handleSelectDM(dm.id)}
                className={[
                  'relative w-full rounded-md px-4 py-2.5 text-left transition-colors duration-fast',
                  'text-message font-normal',
                  'flex items-center gap-2',
                  activeRoom === dm.id
                    ? 'bg-accent-soft text-accent font-medium'
                    : 'bg-transparent text-text-primary hover:bg-surface-hover',
                  'focus:outline-2 focus:outline-offset-2 focus:outline-accent',
                ].join(' ')}
              >
                {/* Presence Indicator */}
                <span
                  className={[
                    'h-2 w-2 rounded-full flex-shrink-0',
                    dm.presence === 'active'
                      ? 'bg-presence-active'
                      : dm.presence === 'idle'
                        ? 'bg-presence-idle animate-pulse'
                        : 'bg-presence-offline',
                  ].join(' ')}
                  aria-label={`${dm.name} is ${dm.presence}`}
                />
                <span className="truncate">
                  {dm.isUnread && <span className="font-semibold">●</span>}
                  {dm.name}
                </span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Settings Footer */}
      <div className="border-t border-border px-4 py-3">
        <button
          className={[
            'w-full rounded-md px-4 py-2 text-left text-message font-normal',
            'text-text-secondary hover:bg-surface-hover transition-colors duration-fast',
            'focus:outline-2 focus:outline-offset-2 focus:outline-accent',
          ].join(' ')}
        >
          ⚙️ Settings
        </button>
      </div>
    </div>
  );

  // Desktop Layout: Fixed Sidebar
  if (!isMobile) {
    return (
      <aside className="w-[280px] flex-shrink-0 border-r border-border">
        {sidebarContent}
      </aside>
    );
  }

  // Mobile Layout: Drawer Overlay
  return (
    <>
      {/* Hamburger Button */}
      <button
        onClick={() => setIsDrawerOpen(true)}
        className="fixed left-4 top-4 z-30 flex h-10 w-10 items-center justify-center rounded bg-surface text-text-primary hover:bg-surface-hover lg:hidden"
        aria-label="Open sidebar"
      >
        ☰
      </button>

      {/* Backdrop */}
      {isDrawerOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/75 lg:hidden"
          onClick={closeDrawer}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <aside
        className={[
          'fixed inset-y-0 left-0 z-50 w-screen max-w-xs transform transition-transform duration-base ease-out',
          'lg:hidden',
          isDrawerOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
