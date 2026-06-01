// Lightweight module-level toast bus — no context, no extra deps.

export type ToastType = 'success' | 'error' | 'info';

export interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
}

type Listener = (toasts: ToastItem[]) => void;

let _toasts: ToastItem[] = [];
const _listeners = new Set<Listener>();

function _notify(): void {
  _listeners.forEach((l) => l([..._toasts]));
}

function _add(type: ToastType, message: string): void {
  const id = crypto.randomUUID();
  _toasts = [..._toasts, { id, type, message }];
  _notify();
  setTimeout(() => _remove(id), 4000);
}

function _remove(id: string): void {
  _toasts = _toasts.filter((t) => t.id !== id);
  _notify();
}

export const toast = {
  success: (message: string): void => _add('success', message),
  error: (message: string): void => _add('error', message),
  info: (message: string): void => _add('info', message),
};

export function subscribeToasts(fn: Listener): () => void {
  _listeners.add(fn);
  fn([..._toasts]); // emit current state immediately
  return (): void => {
    _listeners.delete(fn);
  };
}
