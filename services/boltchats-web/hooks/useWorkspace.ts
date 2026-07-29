'use client';

import { useCallback, useEffect } from 'react';
import { useWorkspaceStore } from '@/store/workspace';
import { workspacesApi, channelsApi, directMessagesApi } from '@/lib/api';
import type { Channel, DirectMessageGroup, Workspace } from '@/types';

interface UseWorkspaceOptions {
  autoLoad?: boolean;
}

export function useWorkspace(options: UseWorkspaceOptions = {}) {
  const { autoLoad = true } = options;

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
    setCurrentWorkspace,
    setCurrentChannel,
    setCurrentDm,
    setWorkspaces,
    setChannels,
    setDms,
    setCurrentWorkspaceData,
    setCurrentChannelData,
    setCurrentDmData,
    setIsLoadingWorkspaces,
    setIsLoadingChannels,
    setIsLoadingDms,
    getChannelsByWorkspace,
    getDmsByWorkspace,
    addChannel,
    updateChannel,
    addDm,
    addWorkspace,
    updateWorkspace,
  } = useWorkspaceStore();

  const loadWorkspaces = useCallback(async (): Promise<void> => {
    try {
      setIsLoadingWorkspaces(true);
      const data = await workspacesApi.list();
      setWorkspaces(data);
      if (data.length > 0 && !currentWorkspaceId) {
        setCurrentWorkspace(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    } finally {
      setIsLoadingWorkspaces(false);
    }
  }, [currentWorkspaceId, setCurrentWorkspace, setWorkspaces, setIsLoadingWorkspaces]);

  const loadChannels = useCallback(
    async (workspaceId: string): Promise<void> => {
      if (!workspaceId) return;
      try {
        setIsLoadingChannels(true);
        const data = await channelsApi.list(workspaceId);
        setChannels(workspaceId, data);
        if (data.length > 0 && !currentChannelId) {
          setCurrentChannel(data[0].id);
        }
      } catch (err) {
        console.error('Failed to load channels:', err);
      } finally {
        setIsLoadingChannels(false);
      }
    },
    [currentChannelId, setCurrentChannel, setChannels, setIsLoadingChannels],
  );

  const loadDms = useCallback(
    async (workspaceId: string): Promise<void> => {
      if (!workspaceId) return;
      try {
        setIsLoadingDms(true);
        const data = await directMessagesApi.list(workspaceId);
        setDms(workspaceId, data);
      } catch (err) {
        console.error('Failed to load DMs:', err);
      } finally {
        setIsLoadingDms(false);
      }
    },
    [setDms, setIsLoadingDms],
  );

  const getChannel = useCallback(
    async (workspaceId: string, channelId: string): Promise<Channel | null> => {
      try {
        return await channelsApi.get(workspaceId, channelId);
      } catch (err) {
        console.error('Failed to load channel:', err);
        return null;
      }
    },
    [],
  );

  const getDm = useCallback(
    async (workspaceId: string, dmId: string): Promise<DirectMessageGroup | null> => {
      try {
        return await directMessagesApi.get(workspaceId, dmId);
      } catch (err) {
        console.error('Failed to load DM:', err);
        return null;
      }
    },
    [],
  );

  const createChannel = useCallback(
    async (
      workspaceId: string,
      name: string,
      description: string,
      type: 'public' | 'private' = 'public',
    ): Promise<Channel | null> => {
      try {
        const channel = await channelsApi.create(workspaceId, name, description, type);
        addChannel(workspaceId, channel);
        return channel;
      } catch (err) {
        console.error('Failed to create channel:', err);
        return null;
      }
    },
    [addChannel],
  );

  const createWorkspace = useCallback(
    async (name: string, description: string): Promise<Workspace | null> => {
      try {
        const workspace = await workspacesApi.create(name, description);
        addWorkspace(workspace);
        return workspace;
      } catch (err) {
        console.error('Failed to create workspace:', err);
        return null;
      }
    },
    [addWorkspace],
  );

  const createDm = useCallback(
    async (
      workspaceId: string,
      participantIds: string[],
    ): Promise<DirectMessageGroup | null> => {
      try {
        const dm = await directMessagesApi.create(workspaceId, participantIds);
        addDm(workspaceId, dm);
        return dm;
      } catch (err) {
        console.error('Failed to create DM:', err);
        return null;
      }
    },
    [addDm],
  );

  // Auto-load workspaces on mount
  useEffect(() => {
    if (autoLoad) {
      loadWorkspaces();
    }
  }, [autoLoad, loadWorkspaces]);

  // Load channels when workspace changes
  useEffect(() => {
    if (currentWorkspaceId) {
      loadChannels(currentWorkspaceId);
      loadDms(currentWorkspaceId);
    }
  }, [currentWorkspaceId, loadChannels, loadDms]);

  // Update current workspace data when workspaces list changes
  useEffect(() => {
    if (currentWorkspaceId) {
      const workspace = workspaces.find((w) => w.id === currentWorkspaceId);
      if (workspace) {
        setCurrentWorkspaceData(workspace);
      }
    }
  }, [currentWorkspaceId, workspaces, setCurrentWorkspaceData]);

  // Update current channel data when channels list changes
  useEffect(() => {
    if (currentWorkspaceId && currentChannelId) {
      const channels = getChannelsByWorkspace(currentWorkspaceId);
      const channel = channels.find((c) => c.id === currentChannelId);
      if (channel) {
        setCurrentChannelData(channel);
      }
    }
  }, [currentWorkspaceId, currentChannelId, getChannelsByWorkspace, setCurrentChannelData]);

  // Update current DM data when DMs list changes
  useEffect(() => {
    if (currentWorkspaceId && currentDmId) {
      const dms = getDmsByWorkspace(currentWorkspaceId);
      const dm = dms.find((d) => d.id === currentDmId);
      if (dm) {
        setCurrentDmData(dm);
      }
    }
  }, [currentWorkspaceId, currentDmId, getDmsByWorkspace, setCurrentDmData]);

  return {
    // State
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

    // Helpers
    getChannelsByWorkspace,
    getDmsByWorkspace,

    // Actions
    setCurrentWorkspace,
    setCurrentChannel,
    setCurrentDm,
    loadWorkspaces,
    loadChannels,
    loadDms,
    getChannel,
    getDm,
    createChannel,
    createWorkspace,
    createDm,
  };
}
