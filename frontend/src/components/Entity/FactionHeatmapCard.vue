<script setup lang="ts">
import type { FactionInfo } from '@/types';

defineProps<{
  factionInfo: FactionInfo;
}>();
</script>

<template>
  <div class="p-4 bg-slate-50 rounded-lg border border-slate-200 shadow-sm">
    <h3 class="text-sm font-bold text-slate-700 mb-3 flex items-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
      Faction Dynamics
    </h3>
    
    <!-- Territory -->
    <div class="mb-3">
        <h4 class="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">Territory</h4>
        <div class="flex flex-wrap gap-1.5">
            <span v-for="t in factionInfo.territory" :key="t" class="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-xs font-medium rounded border border-emerald-200">
                {{ t }}
            </span>
            <span v-if="!factionInfo.territory.length" class="text-xs text-slate-400 italic pl-1">No known territory</span>
        </div>
    </div>

    <!-- Allies -->
    <div class="mb-3">
        <h4 class="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">Allies</h4>
        <div class="flex flex-wrap gap-1.5">
             <span v-for="a in factionInfo.allies" :key="a" class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded border border-blue-200">
                {{ a }}
            </span>
             <span v-if="!factionInfo.allies.length" class="text-xs text-slate-400 italic pl-1">No known allies</span>
        </div>
    </div>

    <!-- Enemies -->
    <div>
        <h4 class="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">Enemies</h4>
        <div class="flex flex-wrap gap-1.5">
             <span v-for="e in factionInfo.enemies" :key="e" class="px-2 py-0.5 bg-rose-50 text-rose-700 text-xs font-medium rounded border border-rose-200">
                {{ e }}
            </span>
             <span v-if="!factionInfo.enemies.length" class="text-xs text-slate-400 italic pl-1">No known enemies</span>
        </div>
    </div>
  </div>
</template>
