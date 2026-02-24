<script setup lang="ts">
import { ref, computed } from 'vue';
import type { ConceptStage } from '@/types';
import { API } from '@/api/client';
import { useNovelStore } from '@/stores/novel';

const props = defineProps<{
  stages: ConceptStage[];
  entityName: string;
}>();

const emit = defineEmits<{
  (e: 'update', stages: ConceptStage[]): void;
}>();

const store = useNovelStore();

// State
const isExpanded = ref(false);
const isAnalyzing = ref(false);

// Actions
const handleAnalyze = async (force: boolean = false) => {
    if (!store.currentNovel || !store.currentNovel.hashes[0]) return;
    
    // UX: Confirm re-analysis if data exists
    if (force && props.stages.length > 0) {
        if (!confirm('重新分析将消耗 Token 并覆盖现有结果，确定继续吗？')) return;
    }
    
    isAnalyzing.value = true;
    try {
        const newStages = await API.analyzeConcept(
            store.currentNovel.name,
            store.currentNovel.hashes[0],
            props.entityName,
            force
        );
        
        // Notify parent to update local state immediately
        emit('update', newStages);
        
        // Simple hack: reload graph data
        store.graphData = null; // Clear cache
        await store.loadGraphData();
        
        // Notify user (optional)
        console.log('Analysis complete', newStages);
    } catch (e) {
        console.error('Analysis failed', e);
    } finally {
        isAnalyzing.value = false;
    }
};

// Computed
const currentStage = computed(() => {
  return props.stages[props.stages.length - 1];
});

const historicalStages = computed(() => {
  // Sort by chapter index descending (newest to oldest)
  // Or simply reverse the list if stages are already sorted by time (which they usually are from backend)
  // But wait, the currentStage is the last one (newest).
  // So historicalStages are 0..N-1.
  // We want to show them in reverse order (N-1 down to 0).
  return props.stages.slice(0, props.stages.length - 1).reverse();
});

// Styles
const stageColors: Record<string, string> = {
  'Unknown': 'bg-gray-100 text-gray-500 border-gray-200',
  'Rumor': 'bg-amber-50 text-amber-700 border-amber-200',
  'Fact': 'bg-blue-50 text-blue-700 border-blue-200',
  'Truth': 'bg-purple-50 text-purple-700 border-purple-200'
};

const stageBackgrounds: Record<string, string> = {
  'Unknown': 'bg-gray-50',
  'Rumor': 'bg-amber-50/50',
  'Fact': 'bg-blue-50/50',
  'Truth': 'bg-purple-50/50'
};

const getStageColor = (stage: string) => {
  return stageColors[stage] || stageColors['Unknown'];
};

const getStageBackground = (stage: string) => {
    return stageBackgrounds[stage] || 'bg-gray-50';
};

const getDotColor = (stage: string) => {
    const baseClass = stageColors[stage] || stageColors['Unknown'];
    if (baseClass.includes('amber')) return 'bg-amber-400';
    if (baseClass.includes('blue')) return 'bg-blue-400';
    if (baseClass.includes('purple')) return 'bg-purple-400';
    return 'bg-gray-300';
};
</script>

<template>
  <div class="rounded-xl border border-gray-100 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 transition-all duration-300"
    :class="[
      stages.length > 0 ? getStageBackground(currentStage.stage_name) : 'bg-gray-50',
      isExpanded ? 'ring-2 ring-indigo-50' : ''
    ]"
  >
    <!-- Header / Current State (Always Visible) -->
    <div 
        @click="isExpanded = !isExpanded"
        class="px-4 py-3 cursor-pointer hover:bg-white/50 transition-colors flex flex-col gap-2"
    >
        <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
                </svg>
                概念演变
            </h3>
            
            <!-- Stage Badge (Current) -->
            <span v-if="stages.length > 0"
              class="px-2 py-0.5 rounded text-[10px] font-bold border uppercase shadow-sm"
              :class="getStageColor(currentStage.stage_name)"
            >
              {{ currentStage.stage_name }}
            </span>
        </div>
        
        <!-- Current Description -->
        <p class="text-sm text-gray-800 font-medium leading-snug" v-if="stages.length > 0">
            {{ currentStage.description }}
        </p>
        <p v-else class="text-sm text-gray-400 italic">
            暂无概念演变分析数据
        </p>
        
        <!-- Toggle Hint -->
        <div class="flex items-center justify-center pt-1">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400 transition-transform duration-300" :class="isExpanded ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
        </div>
    </div>
    
    <!-- Expanded Content (History & Actions) -->
    <div v-if="isExpanded" class="px-4 pb-4 pt-0 border-t border-gray-100/50 bg-white/50">
        <!-- History Timeline -->
        <div class="mt-4 space-y-0" v-if="historicalStages.length > 0">
             <div class="text-[10px] font-bold text-gray-400 uppercase mb-2">History Trace</div>
             
             <div v-for="(stage, index) in historicalStages" :key="index" class="relative pl-4 pb-4 last:pb-0 border-l border-gray-200 ml-1">
                <!-- Dot -->
                <div 
                  class="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-white shadow-sm"
                  :class="getDotColor(stage.stage_name)"
                ></div>
                
                <div class="flex flex-col gap-1 -mt-1 opacity-70 hover:opacity-100 transition-opacity">
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] font-bold text-gray-500 uppercase">{{ stage.stage_name }}</span>
                    </div>
                    <p class="text-xs text-gray-600 line-through decoration-gray-400/50">
                        {{ stage.description }}
                    </p>
                </div>
             </div>
        </div>
        
        <!-- Deep Dive Action -->
        <div class="mt-4 pt-3 border-t border-gray-100 flex gap-2">
            <!-- Main Analysis Button (Idempotent) -->
            <button 
                @click="handleAnalyze(false)"
                :disabled="isAnalyzing"
                class="flex-1 py-2 bg-gray-900 hover:bg-black text-white rounded-lg text-xs font-bold shadow-lg shadow-gray-200 transition-all flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <span v-if="!isAnalyzing">
                    {{ stages.length > 0 ? '刷新/补全' : '分析概念演变' }}
                </span>
                <span v-else class="flex items-center gap-2">
                    <span class="animate-pulse">分析中...</span>
                </span>
                <svg v-if="!isAnalyzing" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 group-hover:translate-x-0.5 transition-transform" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="animate-spin h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </button>
            
            <!-- Force Re-analyze Button (Only if data exists) -->
            <button 
                v-if="stages.length > 0 && !isAnalyzing"
                @click="handleAnalyze(true)"
                class="px-3 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg text-xs font-bold border border-red-200 transition-all flex items-center justify-center"
                title="强制重新生成 (消耗 Token)"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
            </button>
        </div>
    </div>
  </div>
</template>
