import { all, row, run } from '../db.js';
import { requireUser, requireAdmin, mapUser, getUser } from '../lib/auth.js';

export default async function usersRoutes(app: any) {
  app.get('/users', { preHandler: [requireUser, requireAdmin] }, async () => {
    const users = all<any>(
      `SELECT u.*,
        (SELECT COUNT(*) FROM timesheet_entries t WHERE t.user_id = u.id) AS entry_count,
        (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t WHERE t.user_id = u.id) AS total_hours
       FROM users u
       ORDER BY u.email`,
    );
    return {
      users: users.map((u) => ({
        ...mapUser(u),
        entry_count: u.entry_count,
        total_hours: Math.round((u.total_hours ?? 0) * 100) / 100,
      })),
    };
  });

  app.post('/users/:id/toggle-admin', { preHandler: [requireUser, requireAdmin] }, async (req: any, reply: any) => {
    const me = getUser(req)!;
    const id = Number(req.params.id);
    if (id === me.id) return reply.code(400).send({ error: 'Cannot change your own admin status' });
    const u = row<any>('SELECT * FROM users WHERE id = ?', id);
    if (!u) return reply.code(404).send({ error: 'Not found' });
    run('UPDATE users SET is_admin = ? WHERE id = ?', u.is_admin ? 0 : 1, id);
    const updated = row<any>('SELECT * FROM users WHERE id = ?', id);
    return { user: mapUser(updated) };
  });

  app.post('/users/:id/toggle-active', { preHandler: [requireUser, requireAdmin] }, async (req: any, reply: any) => {
    const me = getUser(req)!;
    const id = Number(req.params.id);
    if (id === me.id) return reply.code(400).send({ error: 'Cannot change your own active status' });
    const u = row<any>('SELECT * FROM users WHERE id = ?', id);
    if (!u) return reply.code(404).send({ error: 'Not found' });
    run('UPDATE users SET active = ? WHERE id = ?', u.active ? 0 : 1, id);
    const updated = row<any>('SELECT * FROM users WHERE id = ?', id);
    return { user: mapUser(updated) };
  });
}