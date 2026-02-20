<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { computed } from 'vue';

const store = useNovelStore();

const novels = computed(() => store.novels);
const runs = computed(() => store.runs);

// Actions
const selectNovel = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  const novel = novels.value.find(n => n.name === target.value);
  if (novel) {
    store.selectNovel(novel);
  }
};

const selectRun = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  const run = runs.value.find(r => r.timestamp === target.value);
  if (run) {
    store.selectRun(run);
  }
};

// Formatting
const formatTime = (ts: string) => {
  if (ts.length === 15) {
    return `${ts.slice(0,4)}-${ts.slice(4,6)}-${ts.slice(6,8)} ${ts.slice(9,11)}:${ts.slice(11,13)}`;
  }
  return ts;
};
</script>

<template>
  <header class="bg-white shadow-sm px-6 py-4 flex items-center justify-between z-10 sticky top-0">
    <h1 class="text-xl font-bold text-indigo-600 flex items-center gap-2">
      <span>📚</span> StoryTrace V2
    </h1>
    
    <div class="flex gap-4 items-center">
      <!-- Novel Selector -->
      <select 
        :value="store.currentNovel?.name || ''" 
        @change="selectNovel" 
        class="border rounded px-2 py-1 text-sm bg-white hover:border-indigo-400 transition-colors"
      >
        <option value="" disabled>选择小说</option>
        <option v-for="n in novels" :key="n.name" :value="n.name">{{ n.name }}</option>
      </select>
      
      <!-- Run Selector -->
      <select 
        :value="store.currentRun?.timestamp || ''" 
        @change="selectRun" 
        class="border rounded px-2 py-1 text-sm bg-white hover:border-indigo-400 transition-colors"
        :disabled="!store.currentNovel"
      >
        <option value="" disabled>选择版本</option>
        <option v-for="r in runs" :key="r.timestamp" :value="r.timestamp">{{ formatTime(r.timestamp) }}</option>
      </select>

      <!-- Chapter Selector -->
      <select 
        v-if="store.currentRun"
        :value="store.selectedChapterId || ''" 
        @change="(e) => store.selectedChapterId = (e.target as HTMLSelectElement).value" 
        class="border rounded px-2 py-1 text-sm bg-white hover:border-indigo-400 transition-colors max-w-[200px]"
      >
        <option value="" disabled>跳转章节</option>
        <option v-for="c in store.chapters" :key="c.id" :value="c.id">{{ c.title }}</option>
      </select>

      <!-- View Toggles -->
      <div class="flex bg-gray-100 rounded-lg p-1" v-if="store.currentRun">
        <button 
          @click="store.viewMode = 'overview'" 
          class="px-3 py-1 text-sm rounded-md transition-all font-medium"
          :class="store.viewMode === 'overview' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        >
          📚 概览
        </button>
        <button 
          @click="store.viewMode = 'graph'" 
          class="px-3 py-1 text-sm rounded-md transition-all font-medium"
          :class="store.viewMode === 'graph' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        >
          🕸️ 图谱
        </button>
      </div>
    </div>
  </header>
</template>
