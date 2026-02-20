<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { computed } from 'vue';

const store = useNovelStore();
const chapter = computed(() => store.currentChapter);

const backToOverview = () => {
  store.viewMode = 'overview';
};
</script>

<template>
  <div class="max-w-4xl mx-auto p-8 bg-white shadow-sm min-h-full" v-if="chapter">
    <button 
      @click="backToOverview"
      class="mb-6 text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
    >
      &larr; 返回概览
    </button>

    <h1 class="text-3xl font-bold text-gray-900 mb-2">{{ chapter.title }}</h1>
    <div class="text-sm text-gray-500 mb-8 font-mono">ID: {{ chapter.id }}</div>

    <!-- Summary Section -->
    <div class="bg-indigo-50 p-6 rounded-xl mb-8 border border-indigo-100">
      <h2 class="text-lg font-semibold text-indigo-900 mb-4">智能总结</h2>
      <div class="space-y-4">
        <div 
          v-for="(sent, idx) in chapter.summary_sentences" 
          :key="idx"
          class="flex gap-3"
        >
          <span class="text-indigo-400 font-bold select-none">{{ idx + 1 }}.</span>
          <p class="text-gray-700 leading-relaxed">{{ sent.summary_text }}</p>
        </div>
      </div>
    </div>

    <!-- Content (Placeholder for now) -->
    <div class="prose prose-lg max-w-none text-gray-800">
      <div v-if="chapter.content" v-html="chapter.content.replace(/\n/g, '<br/>')"></div>
      <div v-else class="text-gray-400 italic">
        (原文内容未加载)
      </div>
    </div>
  </div>
</template>
