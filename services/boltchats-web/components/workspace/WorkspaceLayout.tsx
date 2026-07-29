'use client';

import { useCallback, useState } from 'react';
import { useWorkspace } from '@/hooks/useWorkspace';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';
import { ChannelSidebar } from './ChannelSidebar';
import { WorkspaceMemberList } from './WorkspaceMemberList';
import { CreateChannelModal } from './CreateChannelModal';
import { useAuth } from '@/hooks/useAuth';

interface WorkspaceLayoutProps {
  children?: React.ReactNode;
}

export function WorkspaceLayout({ children }: WorkspaceLayoutProps): React.JSX.Element {
  const { user } = useAuth();
  const {
    currentWorkspaceId,
    currentChannelId,
    currentDmId,
    workspaces,
    currentWorkspace,
    currentChannel,
    currentDm,
    isLoadingWorkspaces,
    isLoadingChannels,
    isLoadingDms,
    getChannelsByWorkspace,
    getDmsByWorkspace,
    setCurrentWorkspace,
    setCurrentChannel,
    setCurrentDm,
    createChannel,
    createWorkspace,
  } = useWorkspace();

  const [showCreateChannelModal, setShowCreateChannelModal] = useState(false);
  const [showCreateWorkspaceModal, setShowCreateWorkspaceModal] = useState(false);
  const [isCreatingChannel, setIsCreatingChannel] = useState(false);
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [membersPanelExpanded, setMembersPanelExpanded] = useState(true);

  const channels = currentWorkspaceId ? getChannelsByWorkspace(currentWorkspaceId) : [];
  const dms = currentWorkspaceId ? getDmsByWorkspace(currentWorkspaceId) : [];

  const handleCreateChannel = useCallback(
    async (name: string, description: string, type: 'public' | 'private') => {
      if (!currentWorkspaceId) return;
      try {
        setIsCreatingChannel(true);
        await createChannel(currentWorkspaceId, name, description, type);
      } finally {
        setIsCreatingChannel(false);
      }
    },
    [currentWorkspaceId, createChannel],
  );

  const handleCreateWorkspace = useCallback(
    async (name: string, description: string) => {
      try {
        setIsCreatingWorkspace(true);
        const workspace = await createWorkspace(name, description);
        if (workspace) {
          setCurrentWorkspace(workspace.id);
        }
      } finally {
        setIsCreatingWorkspace(false);
      }
    },
    [createWorkspace, setCurrentWorkspace],
  );

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      {/* Left sidebar: Workspace switcher + Channels */}
      <div className="flex flex-col bg-zinc-950 border-r border-zinc-800">
        <div className="px-3 py-4 border-b border-zinc-800 w-64">
          <WorkspaceSwitcher
            workspaces={workspaces}
            currentWorkspace={currentWorkspace}
            onSelectWorkspace={setCurrentWorkspace}
            onCreateWorkspace={() => setShowCreateWorkspaceModal(true)}
            isLoading={isLoadingWorkspaces}
          />
        </div>

        {currentWorkspaceId && (
          <ChannelSidebar
            channels={channels}
            dms={dms}
            currentChannelId={currentChannelId}
            currentDmId={currentDmId}
            onSelectChannel={setCurrentChannel}
            onSelectDm={setCurrentDm}
            onCreateChannel={() => setShowCreateChannelModal(true)}
            isLoadingChannels={isLoadingChannels}
          />
        )}
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Channel/DM header */}
        <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
          {currentChannel ? (
            <div>
              <h1 className="text-lg font-bold text-white flex items-center gap-2">
                <span>{currentChannel.type === 'private' ? '🔒' : '#'}</span>
                <span>{currentChannel.name}</span>
              </h1>
              {currentChannel.description && (
                <p className="text-sm text-zinc-400 mt-1">{currentChannel.description}</p>
              )}
            </div>
          ) : currentDm ? (
            <div>
              <h1 className="text-lg font-bold text-white flex items-center gap-2">
                <span>💬</span>
                <span>
                  {currentDm.participants
                    .slice(0, 2)
                    .map((p) => p.split('@')[0])
                    .join(', ')}
                </span>
              </h1>
            </div>
          ) : (
            <div className="text-zinc-400">
              {currentWorkspaceId
                ? 'Select a channel or start a conversation'
                : 'Select a workspace'}
            </div>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>

      {/* Right sidebar: Members panel */}
      {currentWorkspaceId && (
        <WorkspaceMemberList
          workspace={currentWorkspace}
          channel={currentChannel}
          isExpanded={membersPanelExpanded}
          onToggleExpand={() => setMembersPanelExpanded(!membersPanelExpanded)}
          isLoadingMembers={isLoadingChannels}
        />
      )}

      {/* Modals */}
      {showCreateChannelModal && (
        <CreateChannelModal
          onClose={() => setShowCreateChannelModal(false)}
          onCreateChannel={handleCreateChannel}
          isLoading={isCreatingChannel}
        />
      )}

      {showCreateWorkspaceModal && (
        <CreateWorkspaceModal
          onClose={() => setShowCreateWorkspaceModal(false)}
          onCreateWorkspace={handleCreateWorkspace}
          isLoading={isCreatingWorkspace}
        />
      )}
    </div>
  );
}

// CreateWorkspaceModal component (inline)
interface CreateWorkspaceModalProps {
  onClose: () => void;
  onCreateWorkspace: (name: string, description: string) => Promise<void>;
  isLoading?: boolean;
}

function CreateWorkspaceModal({
  onClose,
  onCreateWorkspace,
  isLoading = false,
}: CreateWorkspaceModalProps): React.JSX.Element {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Workspace name is required');
      return;
    }

    try {
      setError(null);
      await onCreateWorkspace(name, description);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workspace');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="px-6 py-4 border-b border-zinc-700">
          <h2 className="text-lg font-semibold text-white">Create Workspace</h2>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 bg-red-600/10 border border-red-800/50 rounded text-sm text-red-400">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Workspace Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Tech Corp, Remote Team"
              disabled={isLoading}
              autoFocus
              className="w-full px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this workspace for?"
              disabled={isLoading}
              className="w-full px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors"
              rows={3}
            />
          </div>
        </form>

        <div className="px-6 py-4 border-t border-zinc-700 flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 bg-transparent text-zinc-400 hover:text-white border border-zinc-700 rounded transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-500 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}
