<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { auth } from '$lib/auth.svelte';
  import { iso, addDays, rangeLabel, fmtHours } from '$lib/dates';
  import { ChevronLeft, ChevronRight, Copy, StickyNote } from '@lucide/svelte';

  interface Entry {
    id: number;
    project_id: number;
    entry_date: string;
    hours: number;
    description: string;
    paid_work: boolean;
  }

  let weekDate = $state(iso(new Date()));
  let raw = $state<any>(null); // { week_start, week_end, days, projects, can_edit, target_hours }
  let entries = $state<Entry[]>([]);
  let userId = $state<number | undefined>(undefined);
  let users = $state<any[]>([]);
  let error = $state('');
  let saving = $state(false);
  let editor = $state<{ pid: number; date: string; x: number; y: number } | null>(null);

  const canEdit = $derived(raw?.can_edit ?? false);
  const weekTotal = $derived(entries.reduce((a, e) => a + e.hours, 0));
  const billableTotal = $derived(entries.filter((e) => e.paid_work).reduce((a, e) => a + e.hours, 0));

  onMount(async () => {
    if (auth.user?.is_admin) {
      try {
        users = (await api('/users')).users;
      } catch {
        /* non-fatal */
      }
    }
    load();
  });

  async function load() {
    error = '';
    const q = new URLSearchParams({ date: weekDate });
    if (userId) q.set('user_id', String(userId));
    try {
      const d = await api('/timesheet/week?' + q);
      raw = d;
      entries = d.entries.map(norm);
    } catch (e: any) {
      error = e.message;
    }
  }

  function norm(e: any): Entry {
    return {
      id: e.id,
      project_id: e.project_id,
      entry_date: e.entry_date,
      hours: e.hours,
      description: e.description ?? '',
      paid_work: !!e.paid_work,
    };
  }

  function cell(pid: number, date: string): Entry | undefined {
    return entries.find((e) => e.project_id === pid && e.entry_date === date);
  }
  function projectTotal(pid: number): number {
    return entries.filter((e) => e.project_id === pid).reduce((a, e) => a + e.hours, 0);
  }
  function dayTotal(date: string): number {
    return entries.filter((e) => e.entry_date === date).reduce((a, e) => a + e.hours, 0);
  }

  async function saveCell(pid: number, date: string, hours: number, extra: Partial<Entry> = {}) {
    if (isNaN(hours) || hours < 0) return;
    const cur = cell(pid, date);
    saving = true;
    error = '';
    try {
      const res = await api('/timesheet/cell', {
        method: 'PUT',
        body: JSON.stringify({
          project_id: pid,
          date,
          hours,
          description: extra.description ?? cur?.description,
          paid_work: (extra.paid_work ?? cur?.paid_work ?? true) ? 1 : 0,
        }),
      });
      entries = entries.filter((e) => !(e.project_id === pid && e.entry_date === date));
      if (res?.entry) entries.push(norm(res.entry));
    } catch (e: any) {
      error = e.message;
      load(); // reconcile on failure
    } finally {
      saving = false;
    }
  }

  function onCellInput(pid: number, date: string, ev: Event) {
    const v = (ev.target as HTMLInputElement).value.trim();
    saveCell(pid, date, v === '' ? 0 : Number(v));
  }

  function openEditor(ev: MouseEvent, pid: number, date: string) {
    const r = (ev.currentTarget as HTMLElement).getBoundingClientRect();
    editor = { pid, date, x: Math.min(r.left, window.innerWidth - 288), y: r.bottom + 4 };
  }

  async function copyLastWeek() {
    if (!raw) return;
    saving = true;
    try {
      await api('/timesheet/copy-week', {
        method: 'POST',
        body: JSON.stringify({ from_start: addDays(raw.week_start, -7), to_start: raw.week_start }),
      });
      await load();
    } catch (e: any) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  function shiftWeek(n: number) {
    weekDate = addDays(weekDate, n * 7);
    load();
  }
  function thisWeek() {
    weekDate = iso(new Date());
    load();
  }
</script>

<svelte:window
  onclick={(e) => {
    if (editor && !(e.target as HTMLElement).closest('[data-editor]')) editor = null;
  }}
  onkeydown={(e) => e.key === 'Escape' && (editor = null)}
/>

<div class="mb-5 flex flex-wrap items-center justify-between gap-3">
  <div>
    <h1 class="text-2xl font-semibold">My week</h1>
    {#if raw}<p class="text-sm text-slate-400">{rangeLabel(raw.week_start, raw.week_end)}</p>{/if}
  </div>
  <div class="flex flex-wrap items-center gap-2">
    {#if auth.user?.is_admin && users.length}
      <select class="input py-1.5 text-sm" bind:value={userId} onchange={load}>
        <option value={undefined}>Me</option>
        {#each users as u}<option value={u.id}>{u.name ?? u.email}</option>{/each}
      </select>
    {/if}
    <div class="flex items-center rounded-lg border border-slate-300 bg-white">
      <button class="px-2 py-1.5 hover:bg-slate-50" onclick={() => shiftWeek(-1)} title="Previous week"><ChevronLeft size={16} /></button>
      <button class="border-x border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50" onclick={thisWeek}>This week</button>
      <button class="px-2 py-1.5 hover:bg-slate-50" onclick={() => shiftWeek(1)} title="Next week"><ChevronRight size={16} /></button>
    </div>
    <input type="date" class="input py-1.5 text-sm" bind:value={weekDate} onchange={load} />
    {#if canEdit}
      <button class="btn-secondary flex items-center gap-1.5 text-sm" onclick={copyLastWeek} disabled={saving}>
        <Copy size={15} /> Copy last week
      </button>
    {/if}
  </div>
</div>

{#if error}
  <p class="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>
{/if}

{#if !raw}
  <p class="text-muted">Loading…</p>
{:else if raw.projects.length === 0}
  <div class="card p-8 text-center text-slate-500">
    You're not assigned to any active projects yet. Ask an admin to add you to one.
  </div>
{:else}
  <div class="card overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-line">
          <th class="sticky left-0 z-10 bg-white px-4 py-3 text-left font-medium text-slate-500">Project</th>
          {#each raw.days as d}
            <th
              class="min-w-[64px] px-2 py-3 text-center font-medium
                {d.is_weekend ? 'bg-slate-50/60 text-slate-400' : 'text-slate-500'}
                {d.is_today ? 'text-brand-600' : ''}"
            >
              <div>{d.weekday}</div>
              <div class="text-xs font-normal {d.is_today ? 'text-brand-600' : 'text-slate-400'}">{d.date.slice(8)}</div>
            </th>
          {/each}
          <th class="px-3 py-3 text-right font-medium text-slate-500">Total</th>
        </tr>
      </thead>
      <tbody>
        {#each raw.projects as p (p.id)}
          <tr class="border-b border-line last:border-0">
            <td class="sticky left-0 z-10 max-w-[220px] bg-white px-4 py-2">
              <div class="truncate font-medium">{p.name}</div>
              {#if p.client}<div class="truncate text-xs text-slate-400">{p.client}</div>{/if}
            </td>
            {#each raw.days as d}
              {@const c = cell(p.id, d.date)}
              <td class="relative px-1 py-1 text-center {d.is_weekend ? 'bg-slate-50/40' : ''} {d.is_today ? 'bg-brand-50/40' : ''}">
                <input
                  type="number"
                  min="0"
                  step="0.25"
                  disabled={!canEdit}
                  value={c ? fmtHours(c.hours) : ''}
                  onchange={(e) => onCellInput(p.id, d.date, e)}
                  class="h-9 w-14 rounded-md border border-transparent bg-transparent text-center tabular-nums outline-none
                    hover:border-slate-200 focus:border-brand-500 focus:bg-white disabled:cursor-default
                    {c && !c.paid_work ? 'text-slate-400 italic' : ''}"
                  placeholder="·"
                />
                {#if c && canEdit}
                  <button
                    data-editor
                    onclick={(e) => openEditor(e, p.id, d.date)}
                    class="absolute right-0.5 top-0.5 text-slate-300 hover:text-brand-500"
                    title={c.description || 'Add note'}
                  >
                    <StickyNote size={11} class={c.description ? 'fill-brand-100' : ''} />
                  </button>
                {/if}
              </td>
            {/each}
            <td class="px-3 text-right font-medium tabular-nums text-slate-700">
              {projectTotal(p.id) ? fmtHours(projectTotal(p.id)) : ''}
            </td>
          </tr>
        {/each}
      </tbody>
      <tfoot>
        <tr class="border-t-2 border-line bg-slate-50/50 font-medium">
          <td class="sticky left-0 z-10 bg-slate-50 px-4 py-3">Daily total</td>
          {#each raw.days as d}
            {@const t = dayTotal(d.date)}
            <td class="px-2 py-3 text-center tabular-nums {t > 0 ? 'text-slate-700' : 'text-slate-300'}">{t ? fmtHours(t) : '·'}</td>
          {/each}
          <td class="px-3 py-3 text-right tabular-nums">{fmtHours(weekTotal)}</td>
        </tr>
      </tfoot>
    </table>
  </div>

  <!-- Week summary -->
  <div class="mt-4 flex flex-wrap items-center gap-x-8 gap-y-2 text-sm text-slate-600">
    <span>
      Week total:
      <strong class="tabular-nums {weekTotal >= raw.target_hours ? 'text-green-700' : ''}">{fmtHours(weekTotal)}</strong>
      / {raw.target_hours}h
    </span>
    <span>Billable: <strong class="tabular-nums">{fmtHours(billableTotal)}</strong>h</span>
    {#if weekTotal < raw.target_hours}
      <span class="text-amber-600">{fmtHours(raw.target_hours - weekTotal)}h to target</span>
    {:else}
      <span class="text-green-600">Target met ✓</span>
    {/if}
    {#if saving}<span class="text-slate-400">Saving…</span>{/if}
  </div>
{/if}

<!-- Note / billable popover -->
{#if editor}
  {@const c = cell(editor.pid, editor.date)}
  <div
    data-editor
    class="card fixed z-30 w-72 p-3 shadow-lg"
    style="left: {editor.x}px; top: {editor.y}px"
  >
    <p class="mb-2 text-xs text-slate-400">{editor.date} · {fmtHours(c?.hours ?? 0)}h</p>
    <textarea
      class="input w-full text-sm"
      rows="2"
      placeholder="What did you work on?"
      value={c?.description ?? ''}
      onchange={(e) => c && saveCell(editor!.pid, editor!.date, c.hours, { description: (e.target as HTMLTextAreaElement).value })}
    ></textarea>
    <label class="mt-2 flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={c?.paid_work ?? true}
        onchange={(e) => c && saveCell(editor!.pid, editor!.date, c.hours, { paid_work: (e.target as HTMLInputElement).checked })}
      />
      Billable
    </label>
    <div class="mt-3 flex justify-between">
      <button
        class="text-sm text-red-600 hover:underline"
        onclick={() => {
          saveCell(editor!.pid, editor!.date, 0);
          editor = null;
        }}
      >Delete</button>
      <button class="btn-secondary text-sm" onclick={() => (editor = null)}>Done</button>
    </div>
  </div>
{/if}
