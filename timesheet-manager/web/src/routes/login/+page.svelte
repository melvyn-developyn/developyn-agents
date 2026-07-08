<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { loadMe } from '$lib/auth.svelte';

  const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string;
  let btn: HTMLDivElement;
  let error = $state('');

  onMount(() => {
    const s = document.createElement('script');
    s.src = 'https://accounts.google.com/gsi/client';
    s.async = true;
    s.defer = true;
    s.onload = initGoogle;
    document.head.appendChild(s);
  });

  function initGoogle() {
    const g = (window as any).google;
    if (!g) return;
    g.accounts.id.initialize({ client_id: CLIENT_ID, callback: onCredential });
    g.accounts.id.renderButton(btn, { theme: 'filled_blue', size: 'large', text: 'continue_with', width: 280 });
  }

  async function onCredential(resp: { credential: string }) {
    error = '';
    try {
      await api('/auth/google', { method: 'POST', body: JSON.stringify({ credential: resp.credential }) });
      await loadMe();
      goto('/');
    } catch (e: any) {
      error = e.message ?? 'Sign-in failed';
    }
  }
</script>

<div class="grid min-h-screen place-items-center px-4">
  <div class="card w-full max-w-md p-8 text-center">
    <div class="mx-auto mb-5 grid h-12 w-12 place-items-center rounded-xl bg-brand-500 text-lg font-semibold text-white">T</div>
    <h1 class="text-2xl font-semibold text-brand-700">Track time without the faff.</h1>
    <p class="mt-2 text-sm text-slate-500">Sign in with your Developyn Google account to manage project time.</p>
    <div class="mt-6 flex justify-center" bind:this={btn}></div>
    {#if error}
      <p class="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
    {/if}
  </div>
</div>
