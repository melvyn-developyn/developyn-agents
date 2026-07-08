import { all, row, run } from '../db.js';
import { getUser, requireUser, requireAdmin } from '../lib/auth.js';

export default async function projectsRoutes(app: any) {
  app.get('/projects', { preHandler: requireUser }, async () => {
    return all<any>(
      `SELECT p.*, 
        (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t WHERE t.project_id = p.id) AS logged_hours,
        (SELECT COUNT(*) FROM project_developers pd WHERE pd.project_id = p.id AND pd.active = 1) AS developer_count
       FROM projects p
       ORDER BY p.active DESC, p.client, p.name`,
    ).map((p) => ({
      id: p.id, name: p.name, client: p.client, currency: p.currency,
      maximum_hours: p.maximum_hours, end_date: p.end_date, is_maintenance: !!p.is_maintenance,
      active: !!p.active, logged_hours: round2(p.logged_hours ?? 0), developer_count: p.developer_count,
    }));
  });

  app.post('/projects', { preHandler: [requireUser, requireAdmin] }, async (req: any, reply: any) => {
    const { name, client, currency, maximum_hours, is_maintenance, end_date } = req.body ?? {};
    if (!name) return reply.code(400).send({ error: 'name required' });
    run(
      'INSERT INTO projects (name, client, currency, maximum_hours, is_maintenance, end_date, active) VALUES (?,?,?,?,?,?,1)',
      name, client ?? '', currency ?? 'GBP', maximum_hours ?? null, is_maintenance ? 1 : 0, end_date ?? null,
    );
    const p = row<any>('SELECT * FROM projects WHERE id = last_insert_rowid()');
    return reply.code(201).send({ project: mapProject(p) });
  });

  app.put('/projects/:id', { preHandler: [requireUser, requireAdmin] }, async (req: any, reply: any) => {
    const id = Number(req.params.id);
    const existing = row<any>('SELECT * FROM projects WHERE id = ?', id);
    if (!existing) return reply.code(404).send({ error: 'Not found' });
    const { name, client, currency, maximum_hours, is_maintenance, end_date } = req.body ?? {};
    run(
      'UPDATE projects SET name=?, client=?, currency=?, maximum_hours=?, is_maintenance=?, end_date=? WHERE id=?',
      name ?? existing.name, client ?? existing.client, currency ?? existing.currency,
      maximum_hours ?? existing.maximum_hours, is_maintenance !== undefined ? (is_maintenance ? 1 : 0) : existing.is_maintenance,
      end_date ?? existing.end_date, id,
    );
    const p = row<any>('SELECT * FROM projects WHERE id = ?', id);
    return { project: mapProject(p) };
  });

  app.post('/projects/:id/toggle', { preHandler: [requireUser, requireAdmin] }, async (req: any, reply: any) => {
    const id = Number(req.params.id);
    const p = row<any>('SELECT * FROM projects WHERE id = ?', id);
    if (!p) return reply.code(404).send({ error: 'Not found' });
    run('UPDATE projects SET active = ? WHERE id = ?', p.active ? 0 : 1, id);
    const updated = row<any>('SELECT * FROM projects WHERE id = ?', id);
    return { project: mapProject(updated) };
  });
}

function mapProject(p: any) {
  return {
    id: p.id, name: p.name, client: p.client, currency: p.currency,
    maximum_hours: p.maximum_hours, end_date: p.end_date,
    is_maintenance: !!p.is_maintenance, active: !!p.active,
  };
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}