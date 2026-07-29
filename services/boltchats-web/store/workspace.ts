import { create } from 'zustand';
import type { Channel, DirectMessageGroup, Workspace } from '@/types';

interface WorkspaceState {
  // Current selection
  currentWorkspaceId: string | null;
  currentChannelId: string | null;
  currentDmId: string | null;

  // Cached data
  workspaces: Workspace[];
  channels: Record<string, Channel[]>; // workspace_id -> channels
  dms: Record<string, DirectMessageGroup[]>; // workspace_id -> dms
  currentWorkspace: Workspace | null;
  currentChannel: Channel | null;
  currentDm: DirectMessageGroup | null;

  // Loading states
  isLoadingWorkspaces: boolean;
  isLoadingChannels: boolean;
  isLoadingDms: boolean;
  isLoadingWorkspace: boolean;

  // Actions
  setCurrentWorkspace: (workspaceId: string) => void;
  setCurrentChannel: (channelId: string | null) => void;
  setCurrentDm: (dmId: string | null) => void;

  // Setters for data
  setWorkspaces: (workspaces: Workspace[]) => void;
  setChannels: (workspaceId: string, channels: Channel[]) => void;
  setDms: (workspaceId: string, dms: DirectMessageGroup[]) => void;
  setCurrentWorkspaceData: (workspace: Workspace) => void;
  setCurrentChannelData: (channel: Channel | null) => void;
  setCurrentDmData: (dm: DirectMessageGroup | null) => void;

  // Setters for loading states
  setIsLoadingWorkspaces: (loading: boolean) => void;
  setIsLoadingChannels: (loading: boolean) => void;
  setIsLoadingDms: (loading: boolean) => void;
  setIsLoadingWorkspace: (loading: boolean) => void;

  // Helpers
  getChannelsByWorkspace: (workspaceId: string) => Channel[];
  getDmsByWorkspace: (workspaceId: string) => DirectMessageGroup[];
  addChannel: (workspaceId: string, channel: Channel) => void;
  updateChannel: (workspaceId: string, channel: Channel) => void;
  removeChannel: (workspaceId: string, channelId: string) => void;
  addDm: (workspaceId: string, dm: DirectMessageGroup) => void;
  addWorkspace: (workspace: Workspace) => void;
  updateWorkspace: (workspace: Workspace) => void;
  reset: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  currentWorkspaceId: null,
  currentChannelId: null,
  currentDmId: null,

  workspaces: [],
  channels: {},
  dms: {},
  currentWorkspace: null,
  currentChannel: null,
  currentDm: null,

  isLoadingWorkspaces: false,
  isLoadingChannels: false,
  isLoadingDms: false,
  isLoadingWorkspace: false,

  setCurrentWorkspace: (workspaceId: string): void => {
    set({
      currentWorkspaceId: workspaceId,
      currentChannelId: null,
      currentDmId: null,
      currentChannel: null,
      currentDm: null,
    });
  },

  setCurrentChannel: (channelId: string | null): void => {
    set({
      currentChannelId: channelId,
      currentDmId: null,
      currentDm: null,
    });
  },

  setCurrentDm: (dmId: string | null): void => {
    set({
      currentDmId: dmId,
      currentChannelId: null,
      currentChannel: null,
    });
  },

  setWorkspaces: (workspaces: Workspace[]): void => {
    set({ workspaces });
  },

  setChannels: (workspaceId: string, channels: Channel[]): void => {
    set((state) => ({
      channels: {
        ...state.channels,
        [workspaceId]: channels,
      },
    }));
  },

  setDms: (workspaceId: string, dms: DirectMessageGroup[]): void => {
    set((state) => ({
      dms: {
        ...state.dms,
        [workspaceId]: dms,
      },
    }));
  },

  setCurrentWorkspaceData: (workspace: Workspace): void => {
    set({
      currentWorkspace: workspace,
      currentWorkspaceId: workspace.id,
    });
  },

  setCurrentChannelData: (channel: Channel | null): void => {
    set({
      currentChannel: channel,
      currentChannelId: channel?.id ?? null,
    });
  },

  setCurrentDmData: (dm: DirectMessageGroup | null): void => {
    set({
      currentDm: dm,
      currentDmId: dm?.id ?? null,
    });
  },

  setIsLoadingWorkspaces: (loading: boolean): void => {
    set({ isLoadingWorkspaces: loading });
  },

  setIsLoadingChannels: (loading: boolean): void => {
    set({ isLoadingChannels: loading });
  },

  setIsLoadingDms: (loading: boolean): void => {
    set({ isLoadingDms: loading });
  },

  setIsLoadingWorkspace: (loading: boolean): void => {
    set({ isLoadingWorkspace: loading });
  },

  getChannelsByWorkspace: (workspaceId: string): Channel[] => {
    const state = get();
    return state.channels[workspaceId] ?? [];
  },

  getDmsByWorkspace: (workspaceId: string): DirectMessageGroup[] => {
    const state = get();
    return state.dms[workspaceId] ?? [];
  },

  addChannel: (workspaceId: string, channel: Channel): void => {
    set((state) => {
      const existing = state.channels[workspaceId] ?? [];
      return {
        channels: {
          ...state.channels,
          [workspaceId]: [...existing, channel],
        },
      };
    });
  },

  updateChannel: (workspaceId: string, channel: Channel): void => {
    set((state) => {
      const existing = state.channels[workspaceId] ?? [];
      return {
        channels: {
          ...state.channels,
          [workspaceId]: existing.map((c) => (c.id === channel.id ? channel : c)),
        },
      };
    });
  },

  removeChannel: (workspaceId: string, channelId: string): void => {
    set((state) => {
      const existing = state.channels[workspaceId] ?? [];
      return {
        channels: {
          ...state.channels,
          [workspaceId]: existing.filter((c) => c.id !== channelId),
        },
      };
    });
  },

  addDm: (workspaceId: string, dm: DirectMessageGroup): void => {
    set((state) => {
      const existing = state.dms[workspaceId] ?? [];
      return {
        dms: {
          ...state.dms,
          [workspaceId]: [...existing, dm],
        },
      };
    });
  },

  addWorkspace: (workspace: Workspace): void => {
    set((state) => ({
      workspaces: [...state.workspaces, workspace],
    }));
  },

  updateWorkspace: (workspace: Workspace): void => {
    set((state) => ({
      workspaces: state.workspaces.map((w) =>
        w.id === workspace.id ? workspace : w,
      ),
    }));
  },

  reset: (): void => {
    set({
      currentWorkspaceId: null,
      currentChannelId: null,
      currentDmId: null,
      workspaces: [],
      channels: {},
      dms: {},
      currentWorkspace: null,
      currentChannel: null,
      currentDm: null,
      isLoadingWorkspaces: false,
      isLoadingChannels: false,
      isLoadingDms: false,
      isLoadingWorkspace: false,
    });
  },
}));
