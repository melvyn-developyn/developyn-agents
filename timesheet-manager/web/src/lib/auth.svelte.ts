import { api } from './api';

export interface User {
  id: number;
  email: string;
  name: string | null;
  picture: string | null;
  is_admin: boolean;
  active: boolean;
  has_email_reminders: boolean;
}

export const auth = $state<{ user: User | null; loading: boolean }>({ user: null, loading: true });

export async function loadMe(): Promise<void> {
  try {
    const r = await api('/auth/me');
    auth.user = r.user;
  } catch {
    auth.user = null;
  } finally {
    auth.loading = false;
  }
}

export async function logout(): Promise<void> {
  await api('/auth/logout', { method: 'POST' });
  auth.user = null;
}
