/** BroadcastChannel wrapper for cross-tab auth state synchronisation.
 *
 *  Usage:
 *  - Logout tab:  broadcastLogout()
 *  - Other tabs:  subscribeAuthChannel(onLogout)  →  returns unsubscribe fn
 */

const CHANNEL_NAME = 'bolt_auth';

type AuthChannelMessage = { type: 'logout' };

function isAuthMessage(data: unknown): data is AuthChannelMessage {
  return (
    typeof data === 'object' &&
    data !== null &&
    (data as Record<string, unknown>)['type'] === 'logout'
  );
}

/** Post a logout event to every other tab on the same origin. */
export function broadcastLogout(): void {
  if (typeof window === 'undefined') return;
  const channel = new BroadcastChannel(CHANNEL_NAME);
  channel.postMessage({ type: 'logout' } satisfies AuthChannelMessage);
  channel.close();
}

/** Listen for logout events broadcast by other tabs.
 *  Returns a cleanup function — call it in useEffect cleanup. */
export function subscribeAuthChannel(onLogout: () => void): () => void {
  if (typeof window === 'undefined') return () => {};

  const channel = new BroadcastChannel(CHANNEL_NAME);

  channel.onmessage = (event: MessageEvent<unknown>): void => {
    if (isAuthMessage(event.data) && event.data.type === 'logout') {
      onLogout();
    }
  };

  return () => channel.close();
}
