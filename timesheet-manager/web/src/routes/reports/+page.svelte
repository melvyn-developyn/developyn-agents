<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { iso, addDays, fmtHours } from '$lib/dates';
  import { Download } from '@lucide/svelte';

  let start = $state(addDays(iso(new Date()), -27));
  let end = $state(iso(new Date()));
  let groupBy = $state('project');
  let rows = $state<any[]>([]);
  let error = $state('');

  const groups = [
    { id: 'project', label: 'Project' },
    { id: 'client', label: 'Client' },
    { id: 'user', label: 'Person' },
  ];

  const maxHours = $derived(Math.max(1, ...rows.map((r) => r.hours)));
  const totalHours = $derived(rows.reduce((a, r) => a + r.hours, 0));
  const csvUrl = $derived(`/api/export.csv?start=${start}&end=${end}`);

  onMount(load);
  async function load() {
    error = '';
    try {
      rows = await api(`/reports?start=${start}&end=${end}&group_by=${groupBy}`);
    } catch (e: any) {
      error = e.message;
    }
  }
</script>

<div class="mb-5 flex flex-wrap items-end justify-between gap-3">
  <h1 class="text-2xl font-semibold">Reports</h1>
  <a href={csvUrl} class="btn-secondary flex items-center gap-1.5 text-sm"><Download size={15} /> Export CSV</a>
</div>

<div class="mb-4 flex flex-wrap items-center gap-2">
  <input type="date" class="input py-1.5 text-sm" bind:value={start} onchange={load} />
  <span class="text-slate-400">→</span>
  <input type="date" class="input py-1.5 text-sm" bind:value={end} onchange={load} />
  <div class="ml-2 flex rounded-lg border border-slate-300 bg-white p-0.5">
    {#each groups as g}
      <button
        class="rounded-md px-3 py-1 text-sm {groupBy === g.id ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-50'}"
        onclick={() => { groupBy = g.id; load(); }}
      >{g.label}</button>
    {/each}
  </div>
</div>

{#if error}<p class="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>{/if}

<div class="card p-5">
  <div class="mb-4 flex justify-between text-sm text-slate-500">
    <span>{rows.length} {groupBy === 'user' ? 'people' : groupBy + 's'}</span>
    <span>Total: <strong class="text-slate-700">{fmtHours(totalHours)}h</strong></span>
  </div>
  {#if rows.length === 0}
    <p class="text-sm text-slate-400">No time logged in this range.</p>
  {:else}
    <div class="space-y-3">
      {#each rows as r}
        <div>
          <div class="mb-1 flex justify-between text-sm">
            <span class="truncate">{r.label}{r.sub ? ` · ${r.sub}` : ''}</span>
            <span class="tabular-nums text-slate-500">
              {fmtHours(r.hours)}h
              <span class="text-xs text-slate-400">({fmtHours(r.billable_hours)} billable)</span>
            </span>
          </div>
          <div class="h-2 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full bg-brand-500" style="width: {(r.hours / maxHours) * 100}%"></div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
