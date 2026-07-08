import { all } from '../db.js';
import { requireUser } from '../lib/auth.js';
import { startOfWeekMonday, addDays, iso } from '../lib/dates.js';

export default async function exportRoutes(app: any) {
  app.get('/export.csv', { preHandler: requireUser }, async (req: any, reply: any) => {
    const today = new Date();
    const ws = startOfWeekMonday(today);
    const start = (req.query?.start as string) || iso(ws);
    const end = (req.query?.end as string) || iso(addDays(ws, 6));
    const rows = all<any>(
      `SELECT t.entry_date, u.email, p.client, p.name AS project, t.hours, t.hourly_rate, t.description, t.paid_work
       FROM timesheet_entries t
       JOIN users u ON u.id = t.user_id
       JOIN projects p ON p.id = t.project_id
       WHERE t.entry_date BETWEEN ? AND ?
       ORDER BY t.entry_date, t.id`,
      start, end,
    );
    const header = ['date', 'user', 'client', 'project', 'hours', 'hourly_rate', 'description', 'paid_work'];
    const lines = [header.join(',')];
    for (const r of rows) {
      const desc = stripHtml(r.description ?? '');
      const paid = r.paid_work ? '1' : '0';
      lines.push([r.entry_date, r.email, csvEscape(r.client), csvEscape(r.project), r.hours, r.hourly_rate ?? '', csvEscape(desc), paid].join(','));
    }
    reply.header('Content-Type', 'text/csv');
    reply.header('Content-Disposition', 'attachment; filename="timesheet.csv"');
    return lines.join('\n');
  });
}

function csvEscape(s: string): string {
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function stripHtml(s: string | null | undefined): string {
  if (!s) return '';
  let t = s.replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
  t = t.replace(/&([a-zA-Z]+);/g, (m, e) => ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' } as any)[e] ?? m);
  return t.replace(/<[^>]+>/g, '').trim();
}