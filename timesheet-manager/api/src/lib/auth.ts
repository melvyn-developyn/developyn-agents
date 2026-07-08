import { row } from '../db.js';

export interface User {
  id: number;
  email: string;
  name: string | null;
  picture: string | null;
  is_admin: boolean;
  active: boolean;
  has_email_reminders: boolean;
}

export function mapUser(r: any): User {
  return {
    id: r.id,
    email: r.email,
    name: r.name,
    picture: r.picture,
    is_admin: !!r.is_admin,
    active: r_active(r),
    has_email_reminders: hr(r),
  };
}

function r_active(r: any): boolean {
  return r.active === undefined ? true : !!r.active;
}
function hr(r: any): boolean {
  return r.has_email_reminders === undefined ? true : !!r.has_email_reminders;
}

export function getUser(req: any): User | null {
  const userId = req.session?.get('userId');
  if (!userId) return null;
  const r = row('SELECT * FROM users WHERE id = ?', userId);
  return r ? mapUser(r) : null;
}

export async function requireUser(req: any, reply: any) {
  if (!getUser(req)) return reply.code(401).send({ error: 'Unauthorized' });
}

export async function requireAdmin(req: any, reply: any) {
  const u = getUser(req);
  if (!u) return reply.code(401).send({ error: 'Unauthorized' });
  if (!u.is_admin) return reply.code(403).send({ error: 'Forbidden' });
}

const NAMED: Record<string, string> = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ',
};

export function stripHtml(s: string | null | undefined): string {
  if (!s) return '';
  let t = s;
  t = t.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
  t = t.replace(/&([a-zA-Z]+);/g, (m, e) => (e in NAMED ? NAMED[e] : m));
  t = t.replace(/<[^>]+>/g, '');
  return t.trim();
}