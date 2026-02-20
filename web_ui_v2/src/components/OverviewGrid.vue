<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { computed, watch, nextTick } from 'vue';

const store = useNovelStore();

const chapters = computed(() => store.chapters);

// Auto-Scroll Logic
watch(() => store.selectedChapterId, (newId) => {
  if (!newId || store.viewMode !== 'overview') return;

  nextTick(() => {
    const el = document.getElementById(`card-${newId}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Highlight effect
      el.classList.add('ring-4', 'ring-indigo-300');
      setTimeout(() => el.classList.remove('ring-4', 'ring-indigo-300'), 1500);
    } else {
        console.warn('Card not found', newId);
    }
  });
});

const enterIntensiveReading = async (chapterId: string) => {
  store.selectedChapterId = chapterId;
  await store.loadChapterDetail(chapterId);
  store.viewMode = 'focus';
};
</script>

<template>
  <div class="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-24">
    <div 
      v-for="chap in chapters" 
      :key="chap.id"
      :id="`card-${chap.id}`"
      @click="enterIntensiveReading(chap.id)"
      class="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:border-indigo-400 hover:shadow-lg cursor-pointer transition-all duration-300 group flex flex-col h-full"
      :class="{'ring-2 ring-indigo-500 bg-indigo-50/30': store.selectedChapterId === chap.id}"
    >
      <div class="flex justify-between items-start mb-3">
        <h3 class="font-bold text-gray-800 text-lg group-hover:text-indigo-600 transition-colors line-clamp-1" :title="chap.title">
          {{ chap.title }}
        </h3>
        <span class="text-xs font-mono text-gray-400 bg-gray-50 px-2 py-1 rounded-full whitespace-nowrap">
          {{ chap.id }}
        </span>
      </div>
      
      <div class="flex-1 mb-4">
        <p class="text-sm text-gray-600 leading-relaxed line-clamp-4" v-if="chap.headline">
          {{ chap.headline }}
        </p>
        <p class="text-sm text-gray-400 italic" v-else>
          (暂无核心总结)
        </p>
      </div>

      <div class="mt-auto pt-4 border-t border-gray-50 flex justify-end">
        <button 
          @click.stop="enterIntensiveReading(chap.id)"
          class="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-600 hover:text-indigo-800 px-4 py-2 rounded-full transition-colors font-semibold flex items-center gap-1 opacity-0 group-hover:opacity-100 translate-y-2 group-hover:translate-y-0 duration-300"
        >
          开始精读 &rarr;
        </button>
      </div>
    </div>
  </div>
</template>
