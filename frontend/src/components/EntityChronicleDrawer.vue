<script setup lang="ts">
import { computed, watch, ref } from 'vue';
import type { TimelineEvent, ChronicleNode } from '@/types';
import ChronicleNodeComponent from './ChronicleNodeComponent.vue';
import { API } from '@/api/client';
import { useNovelStore } from '@/stores/novel';

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

const store = useNovelStore();

// --- Pyramid Algorithm ---

const buildPyramid = async (events: TimelineEvent[]): Promise<ChronicleNode[]> => {
  if (events.length === 0) return [];
  
  // Sort events by chapter_index
  const sorted = [...events].sort((a, b) => a.chapter_index - b.chapter_index);
  
  const total = sorted.length;
  
  // Adaptive Strategy
  // If <= 20: Flat (Level 3)
  // If <= 100: Group by 10 (Level 2)
  // If > 100: Group by 50 (Level 1) -> Group by 10 (Level 2) -> Level 3
  
  let topGroupSize = 1;
  let midGroupSize = 10;
  let useMultiLevel = false;
  
  if (total > 100) {
      topGroupSize = 50;
      useMultiLevel = true;
  } else if (total > 20) {
      topGroupSize = 10;
      useMultiLevel = false;
  } else {
      // Flat
      return sorted.map(e => ({
          type: 'leaf',
          level: 3,
          title: e.chapter_title,
          range: [e.chapter_index, e.chapter_index],
          event: e,
          isExpanded: true
      }));
  }
  
  // Grouping Function
  const createGroups = async (inputEvents: TimelineEvent[], size: number, level: number): Promise<ChronicleNode[]> => {
      const nodes: ChronicleNode[] = [];
      let currentGroup: ChronicleNode | null = null;
      let groupEvents: TimelineEvent[] = [];

      // Helper to finalize group
      const finalizeGroup = async (group: ChronicleNode, events: TimelineEvent[]) => {
           // 1. Generate Placeholder Summary (Start ... End)
           if (events.length > 0) {
              const start = events[0].headline || events[0].chapter_title;
              const end = events[events.length - 1].headline || events[events.length - 1].chapter_title;
              group.summary = events.length === 1 ? start : `${start} ... ${end}`;
           }
           
           // 2. Optimistic Prefetch (Async)
           // We fire this but don't await it to block UI?
           // Actually, buildPyramid is async now.
           // But we want "Instant UI" + "Background Update".
           // So we should return the placeholder first.
           // We can attach a method to the node to trigger fetch.
           
           // For now, let's just return. The UI component can trigger fetch on mount or expand.
           return group;
      };

      for (const event of inputEvents) {
          const groupIndex = Math.floor(event.chapter_index / size);
          const groupStart = groupIndex * size;
          const groupEnd = groupStart + size - 1;
          
          if (!currentGroup || currentGroup.range[0] !== groupStart) {
              // Finalize previous group
              if (currentGroup) {
                  await finalizeGroup(currentGroup, groupEvents);
                  nodes.push(currentGroup);
              }
              
              groupEvents = []; // Reset tracker
              
              currentGroup = {
                  type: 'group',
                  level: level,
                  title: `Chapter ${groupStart} - ${groupEnd}`,
                  range: [groupStart, groupEnd],
                  children: [], // To be filled
                  isExpanded: false
              };
          }
          
          groupEvents.push(event);
          
          if (!useMultiLevel || level === 2) {
               // Bottom grouping layer: Add leaves directly
               if (currentGroup.children) {
                   currentGroup.children.push({
                      type: 'leaf',
                      level: 3,
                      title: event.chapter_title,
                      range: [event.chapter_index, event.chapter_index],
                      event: event,
                      isExpanded: true
                   });
               }
          } else {
              // Top grouping layer
              (currentGroup as any)._rawEvents = (currentGroup as any)._rawEvents || [];
              (currentGroup as any)._rawEvents.push(event);
          }
      }
      
      // Push final group
      if (currentGroup) {
          await finalizeGroup(currentGroup, groupEvents);
          nodes.push(currentGroup);
      }
      
      // If Top Layer in Multi-Level, process children recursively
      if (useMultiLevel && level === 1) {
          for (const node of nodes) {
              const raw = (node as any)._rawEvents || [];
              if (raw.length > 0) {
                  node.children = await createGroups(raw, midGroupSize, 2);
              }
          }
      }
      
      return nodes;
  };
  
  return await createGroups(sorted, topGroupSize, useMultiLevel ? 1 : 2);
};

const treeData = ref<ChronicleNode[]>([]);

// --- Summary Fetching Logic ---
const fetchSummary = async (node: ChronicleNode) => {
    if (node.type !== 'group' || !store.currentNovel || !store.currentNovel.hashes[0]) return;
    
    try {
        const result = await API.analyzeGroupSummary(
            store.currentNovel.name,
            store.currentNovel.hashes[0],
            props.entityName,
            node.range[0],
            node.range[1]
        );
        
        if (result.summary) {
            node.summary = result.summary; // Reactively update UI
        }
    } catch (e) {
        console.warn('Failed to fetch group summary', e);
    }
};

// Recursive Fetcher
const fetchAllSummaries = (nodes: ChronicleNode[]) => {
    nodes.forEach(node => {
        if (node.type === 'group') {
            fetchSummary(node); // Fetch current
            if (node.children) {
                fetchAllSummaries(node.children); // Recurse
            }
        }
    });
};

// Rebuild tree when events change
watch(() => props.events, async (newEvents) => {
    treeData.value = await buildPyramid(newEvents);
    // Trigger recursive fetch for ALL groups
    fetchAllSummaries(treeData.value);
}, { immediate: true });

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

        <div v-if="treeData.length > 0" class="space-y-4 relative">
            <!-- Render Tree -->
            <ChronicleNodeComponent 
                v-for="(node, idx) in treeData" 
                :key="idx" 
                :node="node"
                @jump-to-chapter="emit('jump-to-chapter', $event)"
            />
            
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
