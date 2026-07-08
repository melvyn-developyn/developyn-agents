import { all, row, run } from '../db.js';
import { getUser, requireUser, stripHtml } from '../lib/auth.js';
import { startOfWeekMonday, addDays, iso, parseIso } from '../lib/dates.js';

export default async function timesheetRoutes(app: any) {
  app.get('/timesheet/week', { preHandler: requireUser }, async (req: any) => {
    const me = getUser(req)!;
    const target = Number(process.env.WEEKLY_TARGET_HOURS ?? '37.5');
    const dateStr = (req.query?.date as string) || iso(new Date());
    const base = parseIso(dateStr);
    const weekStart = startOfWeekMonday(base);
    const start = iso(weekStart);
    const end = iso(addDays(weekStart, 6));

    let scopeUserId = me.id;
    if (me.is_admin && req.query?.user_id) scopeUserId = Number(req.query.user_id);
    const canEdit = scopeUserId === me.id;

    const projectRows = canEdit
      ? all<any>(
          `SELECT p.*,
             (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t WHERE t.project_id = p.id AND t.user_id = ?) AS logged_hours,
             (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t WHERE t.project_id = p.id AND t.user_id = ? AND t.entry_date BETWEEN ? AND ?) AS hours_this_week
           FROM projects p
           WHERE p.active = 1 AND (
             EXISTS (SELECT 1 FROM project_developers pd WHERE pd.project_id = p.id AND pd.developer_id = ? AND pd.active = 1)
             OR p.id IN (SELECT project_id FROM timesheet_entries WHERE user_id = ? AND entry_date BETWEEN ? AND ?)
           )
           ORDER BY p.client, p.name`,
          scopeUserId, scopeUserId, start, end, scopeUserId, scopeUserId, start, end,
        )
      : all<any>(
          `SELECT p.*,
             (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t WHERE t.project_id = p.id AND t.user_id = ?) AS logged_hours,
             (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t WHERE t.project_id = p.id AND t.user_id = ? AND t.entry_date BETWEEN ? AND ?) AS hours_this_week
           FROM projects p
           WHERE p.active = 1
           ORDER BY p.client, p.name`,
          scopeUserId, scopeUserId, start, end,
        );

    const projects = projectRows.map((p) => ({
      id: p.id, name: p.name, client: p.client, currency: p.currency,
      maximum_hours: p.maximum_hours, logged_hours: round2(p.logged_hours ?? 0),
      active: !!p.active, hours_this_week: round2(p.hours_this_week ?? 0),
    }));

    const entries = all<any>(
      'SELECT id, project_id, entry_date, hours, description, paid_work FROM timesheet_entries WHERE user_id = ? AND entry_date BETWEEN ? AND ? ORDER BY entry_date, id',
      scopeUserId, start, end,
    ).map((e) => ({
      id: e.id, project_id: e.project_id, entry_date: e.entry_date,
      hours: e.hours, description: stripHtml(e.description), paid_work: !!e.paid_work,
    }));

    const days: any[] = [];
    const byDay: { date: string; hours: number }[] = [];
    for (let i = 0; i < 7; i++) {
      const d = addDays(weekStart, i);
      const ds = iso(d);
      const dayTotal = entries.filter((e) => e.entry_date === ds).reduce((a, e) => a + e.hours, 0);
      const wd = (d.getDay() + 6) % 7;
      days.push({
        date: ds, weekday: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][wd],
        is_today: ds === iso(new Date()), is_weekend: wd >= 5, total: round2(dayTotal),
      });
      byDay.push({ date: ds, hours: round2(dayTotal) });
    }

    const byProjectMap = new Map<number, number>();
    let weekHours = 0;
    let billableHours = 0;
    for (const e of entries) {
      byProjectMap.set(e.project_id, (byProjectMap.get(e.project_id) ?? 0) + e.hours);
      weekHours += e.hours;
      if (e.paid_work) billableHours += e.hours;
    }
    const byProject = Array.from(byProjectMap.entries()).map(([pid, h]) => ({
      project_id: pid, name: projects.find((p) => p.id === pid)?.name ?? '', hours: round2(h),
    })).sort((a, b) => b.hours - a.hours);

    return {
      week_start: start, week_end: end,
      days, projects, entries,
      totals: { week_hours: round2(weekHours), billable_hours: round2(billableHours), by_day: byDay, by_project: byProject },
      can_edit: canEdit, target_hours: target,
    };
  });

  app.put('/timesheet/cell', { preHandler: requireUser }, async (req: any, reply: any) => {
    const me = getUser(req)!;
    const { project_id, date, hours, description, paid_work } = req.body ?? {};
    if (!project_id || !date) return reply.code(400).send({ error: 'project_id and date required' });
    const h = Number(hours);
    const existing = all<any>(
      'SELECT id, hours, description, paid_work FROM timesheet_entries WHERE user_id = ? AND project_id = ? AND entry_date = ? ORDER BY id',
      me.id, project_id, date,
    );
    if (!h || h <= 0) {
      if (existing.length) run('DELETE FROM timesheet_entries WHERE user_id = ? AND project_id = ? AND entry_date = ?', me.id, project_id, date);
      return reply.code(204).send();
    }
    const project = row<any>('SELECT id, active FROM projects WHERE id = ?', project_id);
    if (!project || !project.active) return reply.code(400).send({ error: 'Project not available' });

    if (existing.length === 0) {
      const pd = row<any>('SELECT hourly_rate FROM project_developers WHERE developer_id = ? AND project_id = ? AND active = 1', me.id, project_id);
      const info = run(
        'INSERT INTO timesheet_entries (entry_date, user_id, project_id, hours, hourly_rate, description, paid_work) VALUES (?,?,?,?,?,?,?)',
        date, me.id, project_id, h, pd?.hourly_rate ?? null, (description ?? '').trim(), paid_work ?? 1,
      );
      return { entry: { id: Number(info.lastInsertRowid), project_id, entry_date: date, hours: h, description: (description ?? '').trim(), paid_work: paid_work ?? 1 } };
    }
    const keep = existing[0];
    const newDescription = description !== undefined ? description.trim() : keep.description;
    const newPaid = paid_work ?? keep.paid_work;
    run('UPDATE timesheet_entries SET hours = ?, description = ?, paid_work = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', h, newDescription, newPaid, keep.id);
    if (existing.length > 1) {
      const rest = existing.slice(1).map((e) => e.id);
      const placeholders = rest.map(() => '?').join(',');
      run(`DELETE FROM timesheet_entries WHERE id IN (${placeholders})`, ...rest);
    }
    return { entry: { id: keep.id, project_id, entry_date: date, hours: h, description: newDescription, paid_work: newPaid } };
  });

  app.post('/timesheet/copy-week', { preHandler: requireUser }, async (req: any) => {
    const me = getUser(req)!;
    const { from_start, to_start } = req.body ?? {};
    if (!from_start || !to_start) return { copied: 0 };
    const fromStart = parseIso(from_start);
    const toStart = parseIso(to_start);
    const fromEnd = iso(addDays(fromStart, 6));
    const fromEntries = all<any>(
      'SELECT project_id, entry_date, hours, hourly_rate, description, paid_work FROM timesheet_entries WHERE user_id = ? AND entry_date BETWEEN ? AND ?',
      me.id, from_start, fromEnd,
    );
    let copied = 0;
    const insert = (d: string, e: any) => run(
      'INSERT INTO timesheet_entries (entry_date, user_id, project_id, hours, hourly_rate, description, paid_work) VALUES (?,?,?,?,?,?,?)',
      d, me.id, e.project_id, e.hours, e.hourly_rate, e.description, e.paid_work,
    );
    const exists = (d: string, pid: number) => row<any>(
      'SELECT 1 FROM timesheet_entries WHERE user_id = ? AND project_id = ? AND entry_date = ?',
      me.id, pid, d,
    );
    for (const e of fromEntries) {
      const offset = Math.round((parseIso(e.entry_date).getTime() - fromStart.getTime()) / 86400000);
      const toDate = iso(addDays(toStart, offset));
      if (exists(toDate, e.project_id)) continue;
      insert(toDate, e);
      copied++;
    }
    return { copied };
  });
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}