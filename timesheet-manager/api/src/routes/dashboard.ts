import { all, row } from '../db.js';
import { getUser, requireUser, stripHtml } from '../lib/auth.js';
import { startOfWeekMonday, addDays, iso, parseIso, weekdayShort } from '../lib/dates.js';

export default async function dashboardRoutes(app: any) {
  app.get('/dashboard', { preHandler: requireUser }, async (req: any) => {
    const me = getUser(req)!;
    const target = Number(process.env.WEEKLY_TARGET_HOURS ?? '37.5');
    const today = new Date();
    const weekStart = startOfWeekMonday(today);
    const start = iso(weekStart);
    const end = iso(addDays(weekStart, 6));

    const scopeSelf = !me.is_admin;
    const userFilter = scopeSelf ? me.id : undefined;

    const where: string[] = ['entry_date >= ?', 'entry_date <= ?'];
    const params: any[] = [start, end];
    if (userFilter) {
      where.push('user_id = ?');
      params.push(userFilter);
    }
    const whereSql = where.join(' AND ');

    const weekEntries = all<any>(`SELECT entry_date, hours, paid_work FROM timesheet_entries WHERE ${whereSql}`, ...params);
    const weekHours = weekEntries.reduce((a, e) => a + e.hours, 0);
    const billableHours = weekEntries.filter((e) => e.paid_work).reduce((a, e) => a + e.hours, 0);

    const presentDays = new Set(weekEntries.map((e) => e.entry_date));
    const missingDays: string[] = [];
    for (let i = 0; i < 7; i++) {
      const d = addDays(weekStart, i);
      const ds = iso(d);
      const wd = (d.getDay() + 6) % 7;
      if (wd >= 5) continue;
      if (!presentDays.has(ds)) missingDays.push(ds);
    }
    const daysLogged = 5 - missingDays.length;

    const recent = all<any>(
      `SELECT t.id, t.entry_date, t.project_id, t.hours, t.description, t.paid_work,
              p.name AS project_name, p.client, COALESCE(u.name, u.email) AS user_name
       FROM timesheet_entries t
       JOIN projects p ON p.id = t.project_id
       JOIN users u ON u.id = t.user_id
       ${userFilter ? 'WHERE t.user_id = ?' : ''}
       ORDER BY t.entry_date DESC, t.id DESC LIMIT 8`,
      ...(userFilter ? [userFilter] : []),
    ).map((r) => ({
      id: r.id, entry_date: r.entry_date, project_id: r.project_id,
      project_name: r.project_name, client: r.client, hours: r.hours,
      description: stripHtml(r.description), paid_work: !!r.paid_work, user_name: r.user_name,
    }));

    const projects = all<any>(
      `SELECT p.id, p.name, p.client, p.maximum_hours, p.active,
              (SELECT COALESCE(SUM(t.hours),0) FROM timesheet_entries t
                 ${userFilter ? 'JOIN users u2 ON u2.id=t.user_id' : ''}
                 WHERE t.project_id = p.id ${userFilter ? 'AND t.user_id = ?' : ''}) AS logged_hours
       FROM projects p
       WHERE p.active = 1
       ORDER BY logged_hours DESC, p.client, p.name`,
      ...(userFilter ? [userFilter] : []),
    ).map((p) => {
      const logged = p.logged_hours ?? 0;
      const max = p.maximum_hours;
      const percent = max ? Math.round((logged / max) * 1000) / 10 : null;
      return { id: p.id, name: p.name, client: p.client, logged_hours: logged, maximum_hours: max, percent, active: !!p.active };
    }).filter((p) => p.logged_hours > 0 || p.maximum_hours).slice(0, 12);

    return {
      week: { start, end },
      totals: { week_hours: round2(weekHours), billable_hours: round2(billableHours), days_logged: daysLogged, target_hours: target, missing_days: missingDays },
      recent,
      projects,
    };
  });
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}