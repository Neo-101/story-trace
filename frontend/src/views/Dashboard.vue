<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { onMounted } from 'vue';
import AppNavbar from '../components/AppNavbar.vue';
import OverviewGrid from '../components/OverviewGrid.vue';
import GraphView from '../components/GraphView.vue';
import ReaderView from '../components/ReaderView.vue';

const store = useNovelStore();

onMounted(async () => {
  await store.loadNovels();
});
</script>

<template>
  <div class="h-screen flex flex-col bg-gray-50 text-gray-900 font-sans">
    <AppNavbar />
    
    <main class="flex-1 overflow-hidden relative">
      <div v-if="store.loading && !store.graphData && store.viewMode !== 'focus'" class="absolute inset-0 flex items-center justify-center bg-white/80 z-50">
        <div class="flex flex-col items-center gap-4">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <p class="text-indigo-600 font-medium animate-pulse">Loading story data...</p>
        </div>
      </div>

      <div v-if="store.error" class="p-8 text-center text-red-600">
        <p class="font-bold text-lg mb-2">Error</p>
        <p>{{ store.error }}</p>
      </div>

      <Transition name="fade" mode="out-in">
        <OverviewGrid v-if="store.viewMode === 'overview'" />
        <GraphView v-else-if="store.viewMode === 'graph'" />
        <ReaderView v-else-if="store.viewMode === 'focus' || store.viewMode === 'reader'" />
      </Transition>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
