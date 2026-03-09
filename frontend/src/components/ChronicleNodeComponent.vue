<script setup lang="ts">
import { computed } from 'vue';
import type { ChronicleNode } from '@/types';

const props = defineProps<{
  node: ChronicleNode;
}>();

const emit = defineEmits<{
  (e: 'jump-to-chapter', chapterId: string): void;
}>();

const isGroup = computed(() => props.node.type === 'group');
const isLeaf = computed(() => props.node.type === 'leaf');

const toggleExpand = () => {
  if (isGroup.value) {
    props.node.isExpanded = !props.node.isExpanded;
  }
};

const jumpToChapter = () => {
  if (isLeaf.value && props.node.event) {
    emit('jump-to-chapter', props.node.event.chapter_id);
  }
};
</script>

<template>
  <div class="relative">
    <!-- Group Node -->
    <div v-if="isGroup" class="mb-2">
      <div 
        @click="toggleExpand"
        class="flex items-center gap-2 cursor-pointer hover:bg-gray-100 p-2 rounded transition-colors select-none group"
      >
        <!-- Expand/Collapse Icon -->
        <div class="w-5 h-5 flex items-center justify-center text-gray-400 group-hover:text-indigo-500 transition-colors">
          <svg v-if="node.isExpanded" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </div>

        <!-- Group Title & Summary -->
        <div class="flex-1 min-w-0">
          <div class="flex items-baseline justify-between gap-2">
              <h3 class="text-sm font-bold text-gray-700 group-hover:text-indigo-600 transition-colors truncate">
                {{ node.title }}
              </h3>
              <span class="text-[10px] text-gray-400 font-mono shrink-0">
                {{ node.children?.length || 0 }} items
              </span>
          </div>
          
          <!-- Group Summary (New) -->
          <p v-if="node.summary" class="text-[10px] text-gray-500 leading-tight mt-0.5 italic">
            {{ node.summary }}
          </p>
        </div>
      </div>

      <!-- Children (Recursive) -->
      <div v-if="node.isExpanded" class="pl-3 ml-2.5 border-l border-indigo-100 space-y-2 mt-1">
        <ChronicleNodeComponent 
          v-for="(child, idx) in node.children" 
          :key="idx" 
          :node="child"
          @jump-to-chapter="emit('jump-to-chapter', $event)"
        />
      </div>
    </div>

    <!-- Leaf Node (Original Event) -->
    <div v-else-if="isLeaf && node.event" class="pl-8 relative pb-6 group/leaf">
         <!-- Dot -->
         <div class="absolute left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-white border-2 border-indigo-500 z-10 group-hover/leaf:scale-110 transition-transform"></div>
         
         <!-- Timeline Line (Visual Connector) -->
         <div class="absolute left-[9px] top-4 bottom-[-4px] w-0.5 bg-gray-100 group-hover/leaf:bg-indigo-50 transition-colors"></div>

         <!-- Gap Indicator -->
         <div v-if="node.event.gap_before > 0" class="mb-4 text-xs text-gray-400 font-mono pl-1 border-l-2 border-dashed border-gray-300 ml-[-20px] py-2 bg-gray-50/80">
            ... Skip {{ node.event.gap_before }} chapters ...
         </div>

         <!-- Content -->
         <div class="group/content relative pl-3 border-l-2 border-gray-100 hover:border-indigo-200 transition-colors py-1">
             <div class="flex flex-col gap-1">
                 <!-- Header Row: Title + Jump -->
                 <div class="flex items-center justify-between">
                     <h3 class="text-xs font-bold text-gray-900 leading-tight group-hover/content:text-indigo-700 transition-colors">
                        {{ node.event.chapter_title }}
                     </h3>
                     <button 
                        @click.stop="jumpToChapter"
                        class="opacity-0 group-hover/content:opacity-100 text-[10px] font-bold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 px-1.5 py-0.5 rounded transition-all whitespace-nowrap"
                        title="Jump to Chapter"
                    >
                        Jump &rarr;
                    </button>
                 </div>

                 <!-- Summary Text (Compact Block) -->
                 <p class="text-[11px] text-gray-600 leading-snug line-clamp-3 hover:line-clamp-none transition-all cursor-default text-justify">
                    {{ node.event.headline || node.event.content.join(' ') }}
                 </p>
             </div>
         </div>
    </div>
  </div>
</template>

<script lang="ts">
// Recursive component needs explicit name
export default {
  name: 'ChronicleNodeComponent'
}
</script>
