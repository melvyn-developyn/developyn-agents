<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { auth, loadMe, logout } from '$lib/auth.svelte';
  import { LayoutDashboard, CalendarDays, FolderKanban, BarChart3, Users, LogOut } from '@lucide/svelte';

  let { children } = $props();

  onMount(loadMe);

  // Redirect unauthenticated users to /login (and away from /login once signed in).
  $effect(() => {
    if (auth.loading) return;
    const path = $page.url.pathname;
    if (!auth.user && path !== '/login') goto('/login');
    if (auth.user && path === '/login') goto('/');
  });

  const nav = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard, admin: false },
    { href: '/week', label: 'My week', icon: CalendarDays, admin: false },
    { href: '/projects', label: 'Projects', icon: FolderKanban, admin: true },
    { href: '/reports', label: 'Reports', icon: BarChart3, admin: true },
    { href: '/team', label: 'Team', icon: Users, admin: true },
  ];

  const visibleNav = $derived(nav.filter((n) => !n.admin || auth.user?.is_admin));

  async function onLogout() {
    await logout();
    goto('/login');
  }
</script>

{#if auth.loading}
  <div class="grid min-h-screen place-items-center text-muted">Loading…</div>
{:else if !auth.user}
  {@render children()}
{:else}
  <div class="min-h-screen">
    <header class="sticky top-0 z-20 border-b border-line bg-white/90 backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <a href="/" class="flex items-center gap-2 font-semibold text-brand-700">
          <span class="grid h-7 w-7 place-items-center rounded-lg bg-brand-500 text-sm text-white">T</span>
          Timesheets
        </a>
        <nav class="flex flex-1 items-center gap-1">
          {#each visibleNav as item}
            {@const active = $page.url.pathname === item.href}
            <a
              href={item.href}
              class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition
                {active ? 'bg-brand-50 text-brand-600' : 'text-slate-600 hover:bg-slate-100'}"
            >
              <item.icon size={16} />
              {item.label}
            </a>
          {/each}
        </nav>
        <div class="flex items-center gap-3">
          {#if auth.user.picture}
            <img src={auth.user.picture} alt="" class="h-8 w-8 rounded-full" referrerpolicy="no-referrer" />
          {/if}
          <span class="hidden text-sm text-slate-600 sm:block">{auth.user.name ?? auth.user.email}</span>
          <button onclick={onLogout} class="text-slate-400 hover:text-slate-700" title="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-6">
      {@render children()}
    </main>
  </div>
{/if}
