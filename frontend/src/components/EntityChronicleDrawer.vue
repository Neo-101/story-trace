<script setup lang="ts">
import { computed } from 'vue';
import type { TimelineEvent } from '@/types';

const props = defineProps<{
  isOpen: boolean;
  entityName: string;
  events: TimelineEvent[];
  isLoading: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'jump-to-chapter', chapterId: string): void;
}>();

const timeline = computed(() => props.events);
</script>

<template>
  <!-- Drawer Container -->
  <div 
    class="fixed inset-y-0 right-0 w-96 bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col border-l border-gray-200"
    :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
  >
    <!-- Header -->
    <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-white z-10">
        <div>
            <h2 class="text-lg font-bold text-gray-900 truncate max-w-[200px]" :title="entityName">{{ entityName }}</h2>
            <p class="text-xs text-gray-500 uppercase tracking-wider font-semibold mt-1">Entity Chronicle</p>
        </div>
        <button 
          @click="emit('close')"
          class="p-2 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
    </div>

    <!-- Timeline Body -->
    <div class="flex-1 overflow-y-auto custom-scrollbar bg-gray-50 p-6 relative">
         <!-- Loading State -->
        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>

        <div v-if="timeline.length > 0" class="space-y-8 relative">
            <!-- Timeline Line -->
            <div class="absolute left-3 top-2 bottom-2 w-0.5 bg-gray-200"></div>

            <div v-for="event in timeline" :key="event.chapter_id" class="relative pl-8">
                 <!-- Dot -->
                 <div class="absolute left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-white border-2 border-indigo-500 z-10"></div>
                 
                 <!-- Gap Indicator -->
                 <div v-if="event.gap_before > 0" class="mb-4 text-xs text-gray-400 font-mono pl-1 border-l-2 border-dashed border-gray-300 ml-[-20px] py-2 bg-gray-50/80">
                    ... Skip {{ event.gap_before }} chapters ...
                 </div>

                 <!-- Content -->
                 <div class="group">
                     <div class="flex items-baseline justify-between mb-1">
                        <button 
                            @click="emit('jump-to-chapter', event.chapter_id)"
                            class="text-xs font-bold text-indigo-600 hover:text-indigo-800 hover:underline transition-colors ml-auto bg-indigo-50 px-2 py-0.5 rounded-full flex items-center gap-1"
                        >
                            <span>Jump</span>
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                        </button>
                     </div>
                     <h3 class="text-sm font-semibold text-gray-800 mb-2 leading-tight">{{ event.chapter_title }}</h3>
                     
                     <ul class="space-y-2">
                        <li 
                            v-for="(sent, idx) in event.content" 
                            :key="idx"
                            class="text-xs text-gray-600 leading-relaxed bg-white p-3 rounded shadow-sm border border-gray-100"
                        >
                            {{ sent }}
                        </li>
                     </ul>
                 </div>
            </div>
            
            <div class="text-center pt-8 pb-4">
                <span class="text-xs text-gray-400 font-medium bg-gray-100 px-3 py-1 rounded-full">End of Records</span>
            </div>
        </div>
        
        <div v-else-if="!isLoading" class="flex flex-col items-center justify-center h-64 text-gray-400">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
             </svg>
             <p>No timeline data found.</p>
        </div>
    </div>
  </div>

  <!-- Overlay -->
  <div 
    v-if="isOpen"
    class="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity"
    @click="emit('close')"
  ></div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}
</style>
