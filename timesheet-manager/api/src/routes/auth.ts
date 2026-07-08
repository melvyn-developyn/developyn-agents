import { OAuth2Client } from 'google-auth-library';
import { row, run } from '../db.js';
import { getUser, mapUser, requireUser } from '../lib/auth.js';

const CLIENT_ID = process.env.GOOGLE_CLIENT_ID!;
const ALLOWED_DOMAIN = process.env.ALLOWED_DOMAIN ?? 'developyn.com';
const client = new OAuth2Client(CLIENT_ID);

export default async function authRoutes(app: any) {
  app.get('/health', async () => ({ status: 'ok' }));

  app.get('/auth/me', { preHandler: requireUser }, async (req: any) => {
    return { user: getUser(req) };
  });

  app.post('/auth/google', async (req: any, reply: any) => {
    const credential = req.body?.credential;
    if (!credential) return reply.code(400).send({ error: 'Missing credential' });
    let ticket;
    try {
      ticket = await client.verifyIdToken({ idToken: credential, audience: CLIENT_ID });
    } catch {
      return reply.code(401).send({ error: 'Invalid token' });
    }
    const p = ticket.getPayload()!;
    const email = (p.email ?? '').toLowerCase();
    if (!p.email_verified) return reply.code(403).send({ error: 'Email not verified' });
    if (!email.endsWith(`@${ALLOWED_DOMAIN}`)) {
      return reply.code(403).send({ error: 'Domain not allowed' });
    }

    const now = new Date().toISOString();
    let user = row<any>('SELECT * FROM users WHERE email = ?', email);
    if (!user) {
      const count = (row<any>('SELECT COUNT(*) AS c FROM users') ?? { c: 0 }).c;
      run(
        'INSERT INTO users (email, name, picture, is_admin, has_email_reminders, active, last_login_at) VALUES (?,?,?,?,1,1,?)',
        email, p.name ?? null, p.picture ?? null, count === 0 ? 1 : 0, now,
      );
      user = row<any>('SELECT * FROM users WHERE email = ?', email);
    } else {
      run(
        'UPDATE users SET name = ?, picture = ?, last_login_at = ? WHERE id = ?',
        p.name ?? null, p.picture ?? null, now, user.id,
      );
      user = row<any>('SELECT * FROM users WHERE id = ?', user.id);
    }
    req.session.set('userId', user.id);
    return { user: mapUser(user) };
  });

  app.post('/auth/logout', async (req: any, reply: any) => {
    req.session.delete();
    return reply.code(204).send();
  });
}