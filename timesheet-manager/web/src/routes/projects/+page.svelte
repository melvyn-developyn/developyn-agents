<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { fmtHours } from '$lib/dates';
  import { Plus } from '@lucide/svelte';

  let projects = $state<any[]>([]);
  let error = $state('');
  let editing = $state<any | null>(null); // null = closed; {} = new; {id,...} = edit

  onMount(load);
  async function load() {
    try {
      projects = await api('/projects');
    } catch (e: any) {
      error = e.message;
    }
  }

  function newProject() {
    editing = { name: '', client: '', currency: 'GBP', maximum_hours: null, is_maintenance: false, end_date: null };
  }

  async function save() {
    const body = JSON.stringify(editing);
    try {
      if (editing.id) await api('/projects/' + editing.id, { method: 'PUT', body });
      else await api('/projects', { method: 'POST', body });
      editing = null;
      await load();
    } catch (e: any) {
      error = e.message;
    }
  }

  async function toggle(p: any) {
    try {
      await api('/projects/' + p.id + '/toggle', { method: 'POST' });
      await load();
    } catch (e: any) {
      error = e.message;
    }
  }
</script>

<div class="mb-5 flex items-center justify-between">
  <h1 class="text-2xl font-semibold">Projects</h1>
  <button class="btn-primary flex items-center gap-1.5 text-sm" onclick={newProject}><Plus size={16} /> New project</button>
</div>

{#if error}<p class="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>{/if}

<div class="card overflow-x-auto">
  <table class="w-full text-sm">
    <thead>
      <tr class="border-b border-line text-left text-slate-500">
        <th class="px-4 py-3 font-medium">Project</th>
        <th class="px-4 py-3 font-medium">Client</th>
        <th class="px-4 py-3 text-right font-medium">Logged</th>
        <th class="px-4 py-3 text-right font-medium">Budget</th>
        <th class="px-4 py-3 text-center font-medium">Devs</th>
        <th class="px-4 py-3 text-center font-medium">Status</th>
        <th class="px-4 py-3"></th>
      </tr>
    </thead>
    <tbody>
      {#each projects as p (p.id)}
        <tr class="border-b border-line last:border-0 {p.active ? '' : 'opacity-50'}">
          <td class="px-4 py-2.5 font-medium">{p.name}{p.is_maintenance ? ' 🔧' : ''}</td>
          <td class="px-4 py-2.5 text-slate-500">{p.client || '—'}</td>
          <td class="px-4 py-2.5 text-right tabular-nums">{fmtHours(p.logged_hours)}h</td>
          <td class="px-4 py-2.5 text-right tabular-nums text-slate-500">{p.maximum_hours ? p.maximum_hours + 'h' : '—'}</td>
          <td class="px-4 py-2.5 text-center text-slate-500">{p.developer_count}</td>
          <td class="px-4 py-2.5 text-center">
            <span class="rounded-full px-2 py-0.5 text-xs {p.active ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}">
              {p.active ? 'Active' : 'Archived'}
            </span>
          </td>
          <td class="px-4 py-2.5 text-right whitespace-nowrap">
            <button class="text-brand-600 hover:underline" onclick={() => (editing = { ...p })}>Edit</button>
            <button class="ml-3 text-slate-400 hover:underline" onclick={() => toggle(p)}>{p.active ? 'Archive' : 'Restore'}</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

{#if editing}
  <div class="fixed inset-0 z-30 grid place-items-center bg-black/30 p-4" onclick={(e) => e.target === e.currentTarget && (editing = null)} role="presentation">
    <div class="card w-full max-w-md p-5">
      <h2 class="mb-4 text-lg font-semibold">{editing.id ? 'Edit project' : 'New project'}</h2>
      <div class="space-y-3">
        <label class="block text-sm">Name<input class="input mt-1 w-full" bind:value={editing.name} /></label>
        <label class="block text-sm">Client<input class="input mt-1 w-full" bind:value={editing.client} /></label>
        <div class="grid grid-cols-2 gap-3">
          <label class="block text-sm">Currency<input class="input mt-1 w-full" bind:value={editing.currency} /></label>
          <label class="block text-sm">Max hours<input type="number" class="input mt-1 w-full" bind:value={editing.maximum_hours} /></label>
        </div>
        <label class="block text-sm">End date<input type="date" class="input mt-1 w-full" bind:value={editing.end_date} /></label>
        <label class="flex items-center gap-2 text-sm"><input type="checkbox" bind:checked={editing.is_maintenance} /> Maintenance project</label>
      </div>
      <div class="mt-5 flex justify-end gap-2">
        <button class="btn-secondary text-sm" onclick={() => (editing = null)}>Cancel</button>
        <button class="btn-primary text-sm" onclick={save} disabled={!editing.name}>Save</button>
      </div>
    </div>
  </div>
{/if}
