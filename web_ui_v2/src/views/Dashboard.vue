<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import AppNavbar from '@/components/AppNavbar.vue';
import OverviewGrid from '@/components/OverviewGrid.vue';
import ReaderView from '@/components/ReaderView.vue';
import GraphView from '@/components/GraphView.vue';
import { onMounted } from 'vue';

const store = useNovelStore();

onMounted(() => {
  store.loadNovels();
});
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-50 overflow-hidden">
    <AppNavbar />
    
    <main class="flex-1 overflow-y-auto relative scroll-smooth">
      <div v-if="store.loading" class="absolute inset-0 flex items-center justify-center bg-white/50 z-50">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>

      <div v-if="!store.currentNovel" class="flex flex-col items-center justify-center h-full text-gray-400">
        <div class="text-6xl mb-4">📚</div>
        <p class="text-lg">请选择一本小说开始探索</p>
      </div>

      <div v-else-if="store.viewMode === 'overview'" class="container mx-auto">
        <OverviewGrid />
      </div>

      <div v-else-if="store.viewMode === 'graph'" class="h-full">
        <GraphView />
      </div>
      
      <div v-else-if="store.viewMode === 'focus'" class="h-full">
         <ReaderView />
      </div>
    </main>
  </div>
</template>
