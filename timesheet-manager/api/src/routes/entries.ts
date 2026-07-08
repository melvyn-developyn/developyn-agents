import { all, row, run } from '../db.js';
import { getUser, requireUser } from '../lib/auth.js';

export default async function entriesRoutes(app: any) {
  app.get('/entries', { preHandler: requireUser }, async (req: any) => {
    const me = getUser(req)!;
    const { start, end, user_id, project_id } = req.query ?? {};
    const where: string[] = ['1=1'];
    const params: any[] = [];
    if (start) { where.push('t.entry_date >= ?'); params.push(start); }
    if (end) { where.push('t.entry_date <= ?'); params.push(end); }
    if (user_id && me.is_admin) { where.push('t.user_id = ?'); params.push(Number(user_id)); }
    else { where.push('t.user_id = ?'); params.push(me.id); }
    if (project_id) { where.push('t.project_id = ?'); params.push(Number(project_id)); }
    const sql = `SELECT t.id, t.entry_date, t.user_id, t.hours, t.hourly_rate, t.description, t.paid_work, t.created_at,
                  COALESCE(u.name, u.email) AS user_name, p.name AS project_name, p.client
                 FROM timesheet_entries t
                 JOIN users u ON u.id = t.user_id
                 JOIN projects p ON p.id = t.project_id
                 WHERE ${where.join(' AND ')}
                 ORDER BY t.entry_date DESC, t.id DESC`;
    return all<any>(sql, ...params).map((r) => ({
      id: r.id, entry_date: r.entry_date, user_id: r.user_id, user_name: r.user_name,
      project_id: r.project_id, project_name: r.project_name, client: r.client,
      hours: r.hours, hourly_rate: r.hourly_rate, description: stripDesc(r.description),
      paid_work: !!r.paid_work, created_at: r.created_at,
    }));
  });

  app.post('/entries', { preHandler: requireUser }, async (req: any, reply: any) => {
    const me = getUser(req)!;
    const { entry_date, project_id, hours, description, paid_work } = req.body ?? {};
    if (!entry_date || !project_id) return reply.code(400).send({ error: 'entry_date and project_id required' });
    const h = Number(hours);
    if (!h || h <= 0) return reply.code(400).send({ error: 'hours must be > 0' });
    const project = row<any>('SELECT id, active FROM projects WHERE id = ?', Number(project_id));
    if (!project) return reply.code(400).send({ error: 'Project not found' });
    if (!project.active) return reply.code(400).send({ error: 'Project not active' });
    const pd = row<any>('SELECT hourly_rate FROM project_developers WHERE developer_id = ? AND project_id = ? AND active = 1', me.id, Number(project_id));
    run(
      'INSERT INTO timesheet_entries (entry_date, user_id, project_id, hours, hourly_rate, description, paid_work) VALUES (?,?,?,?,?,?,?)',
      entry_date, me.id, Number(project_id), h, pd?.hourly_rate ?? null, (description ?? '').trim(), paid_work ?? 1,
    );
    const entry = row<any>(`SELECT t.*, COALESCE(u.name, u.email) AS user_name, p.name AS project_name, p.client FROM timesheet_entries t JOIN users u ON u.id=t.user_id JOIN projects p ON p.id=t.project_id WHERE t.id = last_insert_rowid()`);
    return reply.code(201).send({ entry: fullEntry(entry) });
  });

  app.put('/entries/:id', { preHandler: requireUser }, async (req: any, reply: any) => {
    const me = getUser(req)!;
    const id = Number(req.params.id);
    const entry = row<any>('SELECT * FROM timesheet_entries WHERE id = ?', id);
    if (!entry) return reply.code(404).send({ error: 'Not found' });
    if (entry.user_id !== me.id && !me.is_admin) return reply.code(403).send({ error: 'Forbidden' });
    const { entry_date, project_id, hours, description, paid_work } = req.body ?? {};
    if (project_id !== undefined) {
      const p = row<any>('SELECT active FROM projects WHERE id = ?', Number(project_id));
      if (!p) return reply.code(400).send({ error: 'Project not found' });
      if (!p.active) return reply.code(400).send({ error: 'Project not active' });
    }
    if (hours !== undefined && Number(hours) <= 0) return reply.code(400).send({ error: 'hours must be > 0' });
    const updates: string[] = ['updated_at = CURRENT_TIMESTAMP'];
    const params: any[] = [];
    if (entry_date !== undefined) { updates.push('entry_date = ?'); params.push(entry_date); }
    if (project_id !== undefined) { updates.push('project_id = ?'); params.push(Number(project_id)); }
    if (hours !== undefined) { updates.push('hours = ?'); params.push(Number(hours)); }
    if (description !== undefined) { updates.push('description = ?'); params.push(description.trim()); }
    if (paid_work !== undefined) { updates.push('paid_work = ?'); params.push(paid_work ? 1 : 0); }
    params.push(id);
    run(`UPDATE timesheet_entries SET ${updates.join(', ')} WHERE id = ?`, ...params);
    const updated = row<any>(`SELECT t.*, COALESCE(u.name, u.email) AS user_name, p.name AS project_name, p.client FROM timesheet_entries t JOIN users u ON u.id=t.user_id JOIN projects p ON p.id=t.project_id WHERE t.id = ?`, id);
    return { entry: fullEntry(updated) };
  });

  app.delete('/entries/:id', { preHandler: requireUser }, async (req: any, reply: any) => {
    const me = getUser(req)!;
    const id = Number(req.params.id);
    const entry = row<any>('SELECT user_id FROM timesheet_entries WHERE id = ?', id);
    if (!entry) return reply.code(404).send({ error: 'Not found' });
    if (entry.user_id !== me.id && !me.is_admin) return reply.code(403).send({ error: 'Forbidden' });
    run('DELETE FROM timesheet_entries WHERE id = ?', id);
    return reply.code(204).send();
  });
}

function stripDesc(s: string | null | undefined): string {
  if (!s) return '';
  let t = s.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
  t = t.replace(/&([a-zA-Z]+);/g, (m, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' } as any)[e] ?? m);
  return t.replace(/<[^>]+>/g, '').trim();
}

function fullEntry(r: any) {
  return {
    id: r.id, entry_date: r.entry_date, user_id: r.user_id, user_name: r.user_name,
    project_id: r.project_id, project_name: r.project_name, client: r.client,
    hours: r.hours, hourly_rate: r.hourly_rate, description: stripDesc(r.description),
    paid_work: !!r.paid_work, created_at: r.created_at,
  };
}