import { all } from '../db.js';
import { requireUser, requireAdmin } from '../lib/auth.js';
import { startOfWeekMonday, addDays, iso } from '../lib/dates.js';

export default async function reportsRoutes(app: any) {
  app.get('/reports', { preHandler: [requireUser, requireAdmin] }, async (req: any) => {
    const today = new Date();
    const thisWeekStart = startOfWeekMonday(today);
    const startDefault = iso(addDays(thisWeekStart, -21));
    const endDefault = iso(addDays(thisWeekStart, 6));
    const start = (req.query?.start as string) || startDefault;
    const end = (req.query?.end as string) || endDefault;
    const groupBy = (req.query?.group_by as string) || 'project';

    let sql: string;
    if (groupBy === 'client') {
      sql = `SELECT p.client AS label, SUM(t.hours) AS hours, SUM(CASE WHEN t.paid_work THEN t.hours ELSE 0 END) AS billable_hours, COUNT(*) AS entries FROM timesheet_entries t JOIN projects p ON p.id = t.project_id WHERE t.entry_date BETWEEN ? AND ? GROUP BY p.client ORDER BY hours DESC`;
    } else if (groupBy === 'user') {
      sql = `SELECT COALESCE(u.name, u.email) AS label, SUM(t.hours) AS hours, SUM(CASE WHEN t.paid_work THEN t.hours ELSE 0 END) AS billable_hours, COUNT(*) AS entries FROM timesheet_entries t JOIN users u ON u.id = t.user_id WHERE t.entry_date BETWEEN ? AND ? GROUP BY u.id ORDER BY hours DESC`;
    } else {
      sql = `SELECT p.name AS label, p.client AS sub, SUM(t.hours) AS hours, SUM(CASE WHEN t.paid_work THEN t.hours ELSE 0 END) AS billable_hours, COUNT(*) AS entries FROM timesheet_entries t JOIN projects p ON p.id = t.project_id WHERE t.entry_date BETWEEN ? AND ? GROUP BY p.id ORDER BY hours DESC`;
    }
    return all<any>(sql, start, end).map((r) => ({
      label: r.label, sub: r.sub, hours: round2(r.hours ?? 0),
      billable_hours: round2(r.billable_hours ?? 0), entries: r.entries,
    }));
  });
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}