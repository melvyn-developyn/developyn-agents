export function iso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function addDays(isoDate: string, n: number): string {
  const [y, m, d] = isoDate.split('-').map(Number);
  return iso(new Date(y, m - 1, d + n));
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** e.g. "07 Jul – 13 Jul 2026" */
export function rangeLabel(startIso: string, endIso: string): string {
  const [, sm, sd] = startIso.split('-').map(Number);
  const [ey, em, ed] = endIso.split('-').map(Number);
  return `${pad(sd)} ${MONTHS[sm - 1]} – ${pad(ed)} ${MONTHS[em - 1]} ${ey}`;
}

/** e.g. "07 Jul" */
export function dayLabel(isoDate: string): string {
  const [, m, d] = isoDate.split('-').map(Number);
  return `${pad(d)} ${MONTHS[m - 1]}`;
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

/** Round to at most 2 dp and drop trailing zeros: 7.5, 8, 1.25. */
export function fmtHours(n: number): string {
  return String(Math.round(n * 100) / 100);
}
