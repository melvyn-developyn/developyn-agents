<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { rangeLabel, dayLabel, fmtHours } from '$lib/dates';
  import { CalendarDays, TriangleAlert } from '@lucide/svelte';

  let data = $state<any>(null);
  let error = $state('');

  onMount(async () => {
    try {
      data = await api('/dashboard');
    } catch (e: any) {
      error = e.message;
    }
  });

  const pct = $derived(
    data ? Math.min(100, Math.round((data.totals.week_hours / data.totals.target_hours) * 100)) : 0,
  );
</script>

{#if error}
  <p class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
{:else if !data}
  <p class="text-muted">Loading…</p>
{:else}
  <div class="mb-6 flex items-end justify-between">
    <div>
      <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{rangeLabel(data.week.start, data.week.end)}</p>
      <h1 class="text-2xl font-semibold">This week</h1>
    </div>
    <a href="/week" class="btn-primary text-sm">Open my week →</a>
  </div>

  <!-- Stat tiles -->
  <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
    <div class="card p-4">
      <p class="text-sm text-slate-500">Hours logged</p>
      <p class="mt-1 text-2xl font-semibold">{fmtHours(data.totals.week_hours)}<span class="text-base font-normal text-slate-400"> / {data.totals.target_hours}</span></p>
      <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
        <div class="h-full rounded-full bg-brand-500 transition-all" style="width: {pct}%"></div>
      </div>
    </div>
    <div class="card p-4">
      <p class="text-sm text-slate-500">Billable</p>
      <p class="mt-1 text-2xl font-semibold">{fmtHours(data.totals.billable_hours)}</p>
      <p class="mt-3 text-xs text-slate-400">
        {data.totals.week_hours > 0 ? Math.round((data.totals.billable_hours / data.totals.week_hours) * 100) : 0}% of logged time
      </p>
    </div>
    <div class="card p-4">
      <p class="text-sm text-slate-500">Days logged</p>
      <p class="mt-1 text-2xl font-semibold">{data.totals.days_logged}<span class="text-base font-normal text-slate-400"> / 5</span></p>
      <p class="mt-3 text-xs text-slate-400">weekdays this week</p>
    </div>
    <div class="card flex flex-col justify-center p-4 {data.totals.missing_days.length ? 'bg-amber-50' : ''}">
      {#if data.totals.missing_days.length}
        <p class="flex items-center gap-1.5 text-sm font-medium text-amber-700"><TriangleAlert size={15} /> Missing days</p>
        <p class="mt-1 text-sm text-amber-800">{data.totals.missing_days.map(dayLabel).join(', ')}</p>
      {:else}
        <p class="text-sm text-slate-500">All caught up</p>
        <p class="mt-1 text-sm text-slate-700">No weekdays missing 🎉</p>
      {/if}
    </div>
  </div>

  <div class="mt-6 grid gap-6 lg:grid-cols-2">
    <!-- Project budgets -->
    <div class="card p-5">
      <h2 class="mb-4 font-semibold">Project budgets</h2>
      {#if data.projects.length === 0}
        <p class="text-sm text-slate-400">No active projects with time logged.</p>
      {:else}
        <div class="space-y-3">
          {#each data.projects as p}
            <div>
              <div class="flex justify-between text-sm">
                <span class="truncate">{p.client ? p.client + ' · ' : ''}{p.name}</span>
                <span class="tabular-nums text-slate-500">
                  {fmtHours(p.logged_hours)}{p.maximum_hours ? ` / ${p.maximum_hours}` : ''}
                </span>
              </div>
              {#if p.maximum_hours}
                <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
                  <div
                    class="h-full rounded-full {p.percent >= 100 ? 'bg-red-500' : p.percent >= 80 ? 'bg-amber-500' : 'bg-brand-500'}"
                    style="width: {Math.min(100, p.percent ?? 0)}%"
                  ></div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Recent entries -->
    <div class="card p-5">
      <h2 class="mb-4 font-semibold">Recent entries</h2>
      {#if data.recent.length === 0}
        <p class="text-sm text-slate-400">Nothing logged yet.</p>
      {:else}
        <ul class="divide-y divide-line">
          {#each data.recent as e}
            <li class="flex items-center gap-3 py-2.5">
              <CalendarDays size={16} class="shrink-0 text-slate-300" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-medium">{e.project_name}</p>
                <p class="truncate text-xs text-slate-400">{dayLabel(e.entry_date)}{e.description ? ' · ' + e.description : ''}</p>
              </div>
              <span class="shrink-0 text-sm font-medium tabular-nums">{fmtHours(e.hours)}h</span>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </div>
{/if}
