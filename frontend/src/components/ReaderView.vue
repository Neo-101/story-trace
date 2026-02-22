<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { computed, ref, nextTick, watch } from 'vue';

const store = useNovelStore();
const chapter = computed(() => store.currentChapter);
const activeSentenceIndex = ref<number | null>(null);
const contentContainer = ref<HTMLElement | null>(null);

const backToOverview = () => {
  store.viewMode = 'overview';
};

// Compute text segments for highlighting
const textSegments = computed(() => {
    if (!chapter.value?.content) return [];
    
    const content = chapter.value.content;
    const segments: { text: string; isHighlight: boolean; id?: string }[] = [];
    
    // If no active sentence or no spans, return full content as one segment
    if (activeSentenceIndex.value === null) {
        return [{ text: content, isHighlight: false }];
    }

    const sentence = chapter.value.summary_sentences[activeSentenceIndex.value];
    if (!sentence || !sentence.source_spans || sentence.source_spans.length === 0) {
        return [{ text: content, isHighlight: false }];
    }

    // Sort spans by start_index
    const spans = [...sentence.source_spans].sort((a, b) => a.start_index - b.start_index);
    
    let lastIndex = 0;
    
    spans.forEach((span, idx) => {
        // Add text before highlight
        if (span.start_index > lastIndex) {
            segments.push({
                text: content.slice(lastIndex, span.start_index),
                isHighlight: false
            });
        }
        
        // Add highlighted text
        // Ensure we don't go out of bounds
        const end = Math.min(span.end_index, content.length);
        if (end > span.start_index) {
            segments.push({
                text: content.slice(span.start_index, end),
                isHighlight: true,
                id: idx === 0 ? 'highlight-target' : undefined // Mark first highlight for scrolling
            });
        }
        
        lastIndex = end;
    });
    
    // Add remaining text
    if (lastIndex < content.length) {
        segments.push({
            text: content.slice(lastIndex),
            isHighlight: false
        });
    }
    
    return segments;
});

const handleSelect = (idx: number) => {
    // Toggle if clicking same item
    if (activeSentenceIndex.value === idx) {
        activeSentenceIndex.value = null;
    } else {
        activeSentenceIndex.value = idx;
    }
};

// Auto-scroll when active sentence changes
watch(activeSentenceIndex, async (newVal) => {
    if (newVal !== null) {
        await nextTick();
        const target = contentContainer.value?.querySelector('#highlight-target');
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});
</script>

<template>
  <div class="h-full w-full flex flex-col bg-white overflow-hidden" v-if="chapter">
    <!-- Header -->
    <div class="flex-none border-b border-gray-200 px-6 py-4 flex justify-between items-center bg-white z-10">
        <div class="flex items-center gap-4">
            <button 
              @click="backToOverview"
              class="text-sm text-gray-500 hover:text-indigo-600 flex items-center gap-1 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              返回概览
            </button>
            <h1 class="text-xl font-bold text-gray-900 truncate max-w-md" :title="chapter.title">{{ chapter.title }}</h1>
        </div>
        <!-- <div class="text-xs font-mono text-gray-400">ID: {{ chapter.id }}</div> -->
    </div>


    <!-- Split View -->
    <div class="flex-1 flex overflow-hidden">
        <!-- Left: Summary List -->
        <div class="w-1/3 min-w-[320px] max-w-md border-r border-gray-200 bg-gray-50 overflow-y-auto custom-scrollbar">
            <div class="p-6 space-y-4">
                <h2 class="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 px-2">智能总结</h2>
                
                <div 
                  v-for="(sent, idx) in chapter.summary_sentences" 
                  :key="idx"
                  @click="handleSelect(idx)"
                  class="p-4 rounded-xl cursor-pointer transition-all duration-200 border border-transparent"
                  :class="activeSentenceIndex === idx 
                    ? 'bg-white border-indigo-200 shadow-md ring-1 ring-indigo-500/20' 
                    : 'bg-white/50 hover:bg-white hover:border-gray-200 hover:shadow-sm'"
                >
                  <div class="flex gap-3">
                      <span 
                        class="flex-none w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors"
                        :class="activeSentenceIndex === idx ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-200 text-gray-500'"
                      >
                        {{ idx + 1 }}
                      </span>
                      <p class="text-sm text-gray-700 leading-relaxed">{{ sent.summary_text }}</p>
                  </div>
                </div>
            </div>
        </div>

        <!-- Right: Content -->
        <div ref="contentContainer" class="flex-1 overflow-y-auto bg-white p-8 md:p-12 custom-scrollbar scroll-smooth">
            <div class="max-w-3xl mx-auto prose prose-lg text-gray-800 leading-loose">
                <!-- Use span segments for rendering to support highlighting -->
                <template v-for="(seg, i) in textSegments" :key="i">
                    <span 
                        v-if="seg.isHighlight"
                        :id="seg.id"
                        class="bg-yellow-200 text-gray-900 px-0.5 rounded transition-colors duration-500"
                    >{{ seg.text }}</span>
                    <span v-else class="whitespace-pre-wrap">{{ seg.text }}</span>
                </template>
                
                <div v-if="!chapter.content" class="text-gray-400 italic text-center py-20">
                    (原文内容未加载)
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
