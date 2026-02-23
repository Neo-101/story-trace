<script setup lang="ts">
import type { ConceptStage } from '@/types';

defineProps<{
  stages: ConceptStage[];
}>();

const stageColors: Record<string, string> = {
  'Unknown': 'bg-gray-100 text-gray-500 border-gray-200',
  'Rumor': 'bg-amber-50 text-amber-700 border-amber-200',
  'Fact': 'bg-blue-50 text-blue-700 border-blue-200',
  'Truth': 'bg-purple-50 text-purple-700 border-purple-200'
};

const getStageColor = (stage: string) => {
  return stageColors[stage] || stageColors['Unknown'];
};

const getDotColor = (stage: string) => {
    // Extract the color part (e.g. amber-700) and convert to bg-amber-400 for dot
    const baseClass = stageColors[stage] || stageColors['Unknown'];
    if (baseClass.includes('amber')) return 'bg-amber-400';
    if (baseClass.includes('blue')) return 'bg-blue-400';
    if (baseClass.includes('purple')) return 'bg-purple-400';
    return 'bg-gray-300';
};
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2">
    <div class="px-4 py-3 border-b border-gray-50 bg-gray-50/50 flex items-center justify-between">
      <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
        </svg>
        概念演变
      </h3>
      <span class="text-[10px] text-gray-400 font-mono">{{ stages.length }} 阶段</span>
    </div>
    
    <div class="p-4 space-y-0">
      <div v-for="(stage, index) in stages" :key="index" class="relative pl-6 pb-6 last:pb-0 border-l border-gray-100 last:border-transparent ml-1.5">
        <!-- Timeline Dot -->
        <div 
          class="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm ring-1 ring-gray-100"
          :class="getDotColor(stage.stage_name)"
        ></div>
        
        <!-- Content -->
        <div class="flex flex-col gap-1.5 -mt-1">
          <div class="flex items-center gap-2">
            <span 
              class="px-1.5 py-0.5 rounded text-[10px] font-bold border uppercase shadow-sm"
              :class="getStageColor(stage.stage_name)"
            >
              {{ stage.stage_name }}
            </span>
          </div>
          
          <p class="text-sm text-gray-700 leading-snug">
            {{ stage.description }}
          </p>
          
          <div v-if="stage.revealed_by && stage.revealed_by.length" class="flex flex-wrap gap-1 mt-0.5">
            <span v-for="clue in stage.revealed_by" :key="clue" class="text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">
              🔍 {{ clue }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
