'use client';

import { useEffect, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Message } from '@/types';

interface MessageListProps {
  messages: Message[];
  currentUserId: string;
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  onLoadOlder: () => void;
  onEditMessage?: (messageId: string, content: string) => Promise<void>;
  onDeleteMessage?: (messageId: string) => Promise<void>;
  onAddReaction?: (messageId: string, emoji: string) => Promise<void>;
  onRemoveReaction?: (messageId: string, emoji: string) => Promise<void>;
}

interface MessageGroup {
  userId: string;
  messages: Message[];
  timestamp: Date;
}

/**
 * Group messages from same user within 5-minute window
 */
function groupMessages(messages: Message[]): MessageGroup[] {
  const groups: MessageGroup[] = [];
  const FIVE_MINUTES_MS = 5 * 60 * 1000;

  for (const message of messages) {
    const lastGroup = groups[groups.length - 1];
    const messageTime = new Date(message.created_at).getTime();
    const lastTime = lastGroup ? new Date(lastGroup.timestamp).getTime() : 0;

    if (
      lastGroup &&
      lastGroup.userId === message.sender_id &&
      messageTime - lastTime < FIVE_MINUTES_MS
    ) {
      lastGroup.messages.push(message);
      // Update timestamp to the latest message in group
      lastGroup.timestamp = new Date(message.created_at);
    } else {
      groups.push({
        userId: message.sender_id,
        messages: [message],
        timestamp: new Date(message.created_at),
      });
    }
  }

  return groups;
}

/**
 * Format avatar initials from username
 */
function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function MessageList({
  messages,
  currentUserId,
  isLoading,
  isLoadingMore,
  hasMore,
  onLoadOlder,
  onEditMessage,
  onDeleteMessage,
  onAddReaction,
  onRemoveReaction,
}: MessageListProps): React.JSX.Element {
  const parentRef = useRef<HTMLDivElement>(null);
  const scrollToBottomRef = useRef<boolean>(true);
  const [wasBelowThreshold, setWasBelowThreshold] = useState(false);

  // Filter out deleted messages
  const visibleMessages = messages.filter((m) => !m.is_deleted && !m.deleted_at);
  const messageGroups = groupMessages(visibleMessages);

  const rowVirtualizer = useVirtualizer({
    count: messageGroups.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 10,
    measureElement:
      typeof window !== 'undefined' && navigator.userAgent.indexOf('Firefox') === -1
        ? (element) => element?.getBoundingClientRect().height
        : undefined,
  });

  const virtualItems = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (parentRef.current && scrollToBottomRef.current) {
      rowVirtualizer.scrollToIndex(messageGroups.length - 1, {
        align: 'end',
        behavior: 'smooth',
      });
    }
  }, [messageGroups.length, rowVirtualizer]);

  // Detect if near bottom — if yes, keep auto-scrolling
  useEffect(() => {
    const handleScroll = () => {
      if (!parentRef.current) return;
      const { scrollTop, scrollHeight, clientHeight } = parentRef.current;
      const distanceFromBottom = scrollHeight - (scrollTop + clientHeight);
      setWasBelowThreshold(distanceFromBottom < 100);
      scrollToBottomRef.current = distanceFromBottom < 100;
    };

    const scrollElement = parentRef.current;
    if (scrollElement) {
      scrollElement.addEventListener('scroll', handleScroll);
      return () => scrollElement.removeEventListener('scroll', handleScroll);
    }
  }, []);

  // Load older messages when scroll reaches top
  useEffect(() => {
    if (virtualItems.length === 0) return;

    const firstItem = virtualItems[0];
    if (firstItem && firstItem.index < 5 && hasMore && !isLoadingMore) {
      onLoadOlder();
    }
  }, [virtualItems, hasMore, isLoadingMore, onLoadOlder]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="h-5 w-5 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center px-4">
        <span className="text-4xl opacity-30">⚡</span>
        <p className="text-sm text-text-tertiary max-w-xs">
          No messages yet. Send the first one.
        </p>
      </div>
    );
  }

  if (visibleMessages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center px-4">
        <span className="text-4xl opacity-30">🗑️</span>
        <p className="text-sm text-text-tertiary max-w-xs">
          All messages have been deleted.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      className="flex flex-1 flex-col overflow-y-auto px-4 py-4 bg-bg-primary"
    >
      {isLoadingMore && hasMore && (
        <div className="flex justify-center py-2">
          <span className="h-4 w-4 rounded-full border-2 border-border border-t-accent animate-spin" />
        </div>
      )}

      <div
        style={{
          height: totalSize,
        }}
      >
        <div
          style={{
            transform: `translateY(${virtualItems[0]?.start ?? 0}px)`,
          }}
        >
          {virtualItems.map((virtualItem) => {
            const group = messageGroups[virtualItem.index]!;
            const userInitials = getInitials('User'); // TODO: get from message metadata

            return (
              <div key={virtualItem.key} className="mb-4 flex gap-3 items-start">
                {/* Avatar */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold" style={{
                  backgroundColor: 'var(--color-accent-soft)',
                  color: 'var(--color-accent)',
                }}>
                  {userInitials}
                </div>

                {/* Message Group Content */}
                <div className="flex-1 min-w-0">
                  {/* Username */}
                  <div className="text-message font-semibold text-text-primary mb-1">
                    User Name {/* TODO: get from message metadata */}
                  </div>

                  {/* Messages */}
                  <div className="space-y-0.5">
                    {group.messages.map((message) => (
                      <div
                        key={message.id}
                        className="text-message text-text-primary break-words whitespace-pre-wrap"
                      >
                        {message.content}
                      </div>
                    ))}
                  </div>

                  {/* Timestamp (only once per group) */}
                  <div className="text-timestamp text-text-tertiary mt-1">
                    {new Date(group.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
