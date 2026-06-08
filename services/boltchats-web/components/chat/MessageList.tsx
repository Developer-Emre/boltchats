'use client';

import { useEffect, useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Message } from '@/types';
import { MessageBubble } from '@/components/chat/MessageBubble';

interface MessageListProps {
  messages: Message[];
  currentUserId: string;
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  onLoadOlder: () => void;
  onEditMessage?: (messageId: string, content: string) => Promise<void>;
  onDeleteMessage?: (messageId: string) => Promise<void>;
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
}: MessageListProps): React.JSX.Element {
  const parentRef = useRef<HTMLDivElement>(null);
  const scrollToBottomRef = useRef<boolean>(true);
  const [wasBelowThreshold, setWasBelowThreshold] = useState(false);

  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
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
      rowVirtualizer.scrollToIndex(messages.length - 1, { align: 'end', behavior: 'smooth' });
    }
  }, [messages.length, rowVirtualizer]);

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
        <span className="h-5 w-5 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center px-8">
        <span className="text-4xl opacity-30">⚡</span>
        <p className="text-sm text-zinc-600 max-w-xs">
          No messages yet. Send the first one.
        </p>
      </div>
    );
  }

  return (
    <div ref={parentRef} className="flex flex-1 flex-col overflow-y-auto px-4 py-4">
      {isLoadingMore && hasMore && (
        <div className="flex justify-center py-2">
          <span className="h-4 w-4 rounded-full border-2 border-zinc-600 border-t-indigo-500 animate-spin" />
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
          {virtualItems.map((virtualItem) => (
            <div key={virtualItem.key} className="mb-4">
              <MessageBubble
                message={messages[virtualItem.index]!}
                isMine={messages[virtualItem.index]!.sender_id === currentUserId}
                onEdit={onEditMessage}
                onDelete={onDeleteMessage}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
