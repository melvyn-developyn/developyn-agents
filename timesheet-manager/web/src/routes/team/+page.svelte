<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { auth } from '$lib/auth.svelte';
  import { fmtHours } from '$lib/dates';

  let users = $state<any[]>([]);
  let error = $state('');

  onMount(load);
  async function load() {
    try {
      users = (await api('/users')).users;
    } catch (e: any) {
      error = e.message;
    }
  }

  async function post(path: string) {
    try {
      await api(path, { method: 'POST' });
      await load();
    } catch (e: any) {
      error = e.message;
    }
  }
</script>

<h1 class="mb-5 text-2xl font-semibold">Team</h1>

{#if error}<p class="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>{/if}

<div class="card overflow-x-auto">
  <table class="w-full text-sm">
    <thead>
      <tr class="border-b border-line text-left text-slate-500">
        <th class="px-4 py-3 font-medium">Person</th>
        <th class="px-4 py-3 text-right font-medium">Entries</th>
        <th class="px-4 py-3 text-right font-medium">Total hours</th>
        <th class="px-4 py-3 text-center font-medium">Role</th>
        <th class="px-4 py-3 text-center font-medium">Status</th>
        <th class="px-4 py-3"></th>
      </tr>
    </thead>
    <tbody>
      {#each users as u (u.id)}
        <tr class="border-b border-line last:border-0 {u.active ? '' : 'opacity-50'}">
          <td class="px-4 py-2.5">
            <div class="flex items-center gap-2.5">
              {#if u.picture}<img src={u.picture} alt="" class="h-7 w-7 rounded-full" referrerpolicy="no-referrer" />{/if}
              <div>
                <div class="font-medium">{u.name ?? u.email}{u.id === auth.user?.id ? ' (you)' : ''}</div>
                <div class="text-xs text-slate-400">{u.email}</div>
              </div>
            </div>
          </td>
          <td class="px-4 py-2.5 text-right tabular-nums text-slate-500">{u.entry_count}</td>
          <td class="px-4 py-2.5 text-right tabular-nums">{fmtHours(u.total_hours)}h</td>
          <td class="px-4 py-2.5 text-center">
            <span class="rounded-full px-2 py-0.5 text-xs {u.is_admin ? 'bg-brand-50 text-brand-600' : 'bg-slate-100 text-slate-500'}">
              {u.is_admin ? 'Admin' : 'Member'}
            </span>
          </td>
          <td class="px-4 py-2.5 text-center">
            <span class="rounded-full px-2 py-0.5 text-xs {u.active ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}">
              {u.active ? 'Active' : 'Disabled'}
            </span>
          </td>
          <td class="px-4 py-2.5 text-right whitespace-nowrap">
            {#if u.id !== auth.user?.id}
              <button class="text-brand-600 hover:underline" onclick={() => post(`/users/${u.id}/toggle-admin`)}>
                {u.is_admin ? 'Revoke admin' : 'Make admin'}
              </button>
              <button class="ml-3 text-slate-400 hover:underline" onclick={() => post(`/users/${u.id}/toggle-active`)}>
                {u.active ? 'Disable' : 'Enable'}
              </button>
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
