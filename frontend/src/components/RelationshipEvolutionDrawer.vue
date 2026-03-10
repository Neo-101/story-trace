<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkLineComponent
} from 'echarts/components';
import VChart, { THEME_KEY } from 'vue-echarts';
import type { RelationshipTimelineEvent, Entity, RelationshipStage } from '@/types';
import { API } from '@/api/client';
import { useNovelStore } from '@/stores/novel';

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkLineComponent
]);

const props = defineProps<{
  isOpen: boolean;
  sourceEntity: Entity | null;
  targetEntity: Entity | null;
  events: RelationshipTimelineEvent[];
  isLoading: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'jump-to-chapter', chapterId: string): void;
}>();

const store = useNovelStore();
const stages = ref<RelationshipStage[]>([]);
const isLoadingStages = ref(false);
const isAnalyzing = ref(false);

// --- 1. Data Fetching ---

const fetchStages = async () => {
    if (!props.sourceEntity || !props.targetEntity || !store.currentNovel || !store.currentNovel.hashes[0]) return;
    
    isLoadingStages.value = true;
    try {
        const result = await API.fetchRelationshipStages(
            store.currentNovel.name,
            store.currentNovel.hashes[0],
            props.sourceEntity.name,
            props.targetEntity.name
        );
        stages.value = result.sort((a, b) => a.start_chapter - b.start_chapter);
    } catch (e) {
        console.error("Failed to fetch relationship stages", e);
    } finally {
        isLoadingStages.value = false;
    }
};

const analyzeEvolution = async () => {
    if (!props.sourceEntity || !props.targetEntity || !store.currentNovel || !store.currentNovel.hashes[0] || props.events.length === 0) return;
    
    isAnalyzing.value = true;
    try {
        // Simple strategy: Chunk by 10 chapters
        // Find min/max
        const indices = props.events.map(e => e.chapter_index);
        const minCh = Math.min(...indices);
        const maxCh = Math.max(...indices);
        
        const chunkSize = 20; // Analyze every 20 chapters to reduce calls
        
        for (let start = minCh; start <= maxCh; start += chunkSize) {
            const end = Math.min(start + chunkSize - 1, maxCh);
            // Only analyze if there are events in this range?
            const hasEvents = props.events.some(e => e.chapter_index >= start && e.chapter_index <= end);
            if (hasEvents) {
                // Sequential execution to avoid rate limits
                await API.analyzeRelationshipStage(
                    store.currentNovel.name,
                    store.currentNovel.hashes[0],
                    props.sourceEntity.name,
                    props.targetEntity.name,
                    start,
                    end,
                    true // Force analysis
                );
            }
        }
        
        await fetchStages();
        
    } catch (e) {
        console.error("Analysis failed", e);
        alert("分析失败，请稍后重试: " + e);
    } finally {
        isAnalyzing.value = false;
    }
};

watch(() => props.isOpen, (newVal) => {
    if (newVal) {
        fetchStages();
    }
});

// --- 2. Chart Configuration ---

const chartOption = computed(() => {
    const data = stages.value.map(s => [
        (s.start_chapter + s.end_chapter) / 2, // X: Midpoint
        s.sentiment_score // Y: Score
    ]);

    // Add start/end points from events if stages are sparse?
    // Or just plot stages.
    
    return {
        tooltip: {
            trigger: 'axis',
            formatter: (params: any) => {
                const stageIdx = params[0].dataIndex;
                const stage = stages.value[stageIdx];
                return `
                    <div class="font-bold">${stage.stage_label}</div>
                    <div class="text-xs">Ch ${stage.start_chapter} - ${stage.end_chapter}</div>
                    <div class="text-xs">Score: ${stage.sentiment_score}</div>
                `;
            }
        },
        grid: {
            top: 20,
            bottom: 30,
            left: 40,
            right: 20
        },
        xAxis: {
            type: 'value',
            min: 0,
            scale: true,
            splitLine: { show: false },
            axisLabel: {
                formatter: 'Ch {value}'
            }
        },
        yAxis: {
            type: 'value',
            min: -1,
            max: 1,
            name: '情感分 (Score)',
            nameTextStyle: {
                color: '#9ca3af',
                align: 'left',
                padding: [0, 0, 0, -20]
            },
            splitLine: {
                lineStyle: {
                    type: 'dashed'
                }
            }
        },
        series: [
            {
                data: data,
                type: 'line',
                smooth: 0.3,
                symbolSize: 8,
                lineStyle: {
                    color: '#6366f1',
                    width: 3
                },
                itemStyle: {
                    color: '#6366f1'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: 'rgba(99, 102, 241, 0.5)' }, // Positive
                            { offset: 1, color: 'rgba(244, 63, 94, 0.5)' }   // Negative (Gradient across the whole area? No, ECharts area is from line to 0 usually)
                        ]
                    },
                    opacity: 0.2
                },
                markLine: {
                    data: [{ yAxis: 0 }],
                    symbol: ['none', 'none'],
                    lineStyle: { color: '#9ca3af', type: 'solid', width: 1 }
                }
            }
        ]
    };
});

const onChartClick = (params: any) => {
    const stage = stages.value[params.dataIndex];
    if (stage) {
        // Find the stage element and scroll to it
        const el = document.getElementById(`stage-${stage.start_chapter}`);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
};

// --- 3. Interaction Grouping ---

const groupedEvents = computed(() => {
    // Group events by stages
    // If no stages, put everything in "Unanalyzed"
    if (stages.value.length === 0) {
        return [{
            type: 'raw',
            events: props.events
        }];
    }

    const groups = [];
    let currentStageIdx = 0;
    
    // Sort events
    const sorted = [...props.events].sort((a, b) => a.chapter_index - b.chapter_index);
    
    for (const stage of stages.value) {
        const stageEvents = sorted.filter(e => 
            e.chapter_index >= stage.start_chapter && 
            e.chapter_index <= stage.end_chapter
        );
        
        groups.push({
            type: 'stage',
            stage: stage,
            events: stageEvents
        });
    }
    
    return groups;
});

// --- UI Helpers ---
const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-indigo-600 bg-indigo-50 border-indigo-200';
    if (score < -0.3) return 'text-rose-600 bg-rose-50 border-rose-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
};

const expandedStages = ref<Record<string, boolean>>({});
const toggleStage = (key: string) => {
    expandedStages.value[key] = !expandedStages.value[key];
};

</script>

<template>
  <!-- Drawer Container -->
  <div 
    class="fixed inset-y-0 right-0 w-[640px] bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col border-l border-gray-200"
    :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
  >
    <!-- Header -->
    <div class="p-6 border-b border-gray-100 flex-none bg-white/80 backdrop-blur z-10 relative">
        <button 
          @click="emit('close')"
          class="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors z-20"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="text-xs font-mono text-gray-400 mb-2 uppercase tracking-wider">RELATIONSHIP EVOLUTION</div>
        
        <div class="flex items-center gap-4 mb-4">
             <h2 class="text-xl font-bold text-gray-800">
                {{ sourceEntity?.name }} 
                <span class="text-gray-300 mx-2">⇄</span>
                {{ targetEntity?.name }}
             </h2>
        </div>

        <!-- Chart Area -->
        <div v-if="stages.length > 0" class="h-40 w-full mb-2">
            <v-chart class="chart" :option="chartOption" autoresize @click="onChartClick" />
        </div>
        <div v-else-if="!isLoadingStages && events.length > 0" class="h-20 flex flex-col items-center justify-center text-gray-400 text-sm bg-gray-50 rounded-lg border border-dashed border-gray-200 gap-2">
            <span>No analysis stages yet.</span>
            <button 
                @click="analyzeEvolution"
                :disabled="isAnalyzing"
                class="px-3 py-1 bg-indigo-50 text-indigo-600 rounded text-xs font-bold hover:bg-indigo-100 disabled:opacity-50"
            >
                {{ isAnalyzing ? 'Analyzing...' : 'Generate Evolution' }}
            </button>
        </div>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto custom-scrollbar bg-gray-50 p-6">
        <div v-if="isLoading || isLoadingStages" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>

        <div v-else class="space-y-6">
            <template v-for="(group, idx) in groupedEvents" :key="idx">
                
                <!-- STAGE CARD -->
                <div v-if="group.type === 'stage'" :id="`stage-${group.stage.start_chapter}`" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <!-- Stage Header -->
                    <div 
                        class="p-4 cursor-pointer hover:bg-gray-50 transition-colors flex justify-between items-start"
                        @click="toggleStage(idx.toString())"
                    >
                        <div>
                            <div class="flex items-center gap-3 mb-1">
                                <span class="px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wider" :class="getSentimentColor(group.stage.sentiment_score)">
                                    {{ group.stage.stage_label }}
                                </span>
                                <span class="text-xs text-gray-400 font-mono">
                                    Ch {{ group.stage.start_chapter }} - {{ group.stage.end_chapter }}
                                </span>
                            </div>
                            <p class="text-sm text-gray-600 leading-relaxed">
                                {{ group.stage.summary_text }}
                            </p>
                        </div>
                        <div class="text-gray-400">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 transform transition-transform" :class="expandedStages[idx.toString()] ? 'rotate-180' : ''" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    </div>

                    <!-- Stage Details (Expanded) -->
                    <div v-if="expandedStages[idx.toString()]" class="border-t border-gray-100 bg-gray-50/50 p-4 space-y-4">
                        <div v-for="event in group.events" :key="event.chapter_id" class="relative pl-4 border-l-2 border-indigo-100">
                            <div 
                                class="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-indigo-300 cursor-pointer hover:scale-125 transition-transform"
                                @click="emit('jump-to-chapter', event.chapter_id)"
                            ></div>
                            
                            <div class="mb-1 flex items-center gap-2">
                                <span class="text-xs font-bold text-gray-500 cursor-pointer hover:text-indigo-600" @click="emit('jump-to-chapter', event.chapter_id)">
                                    Ch {{ event.chapter_index }}
                                </span>
                                <span class="text-xs text-gray-300">|</span>
                                <span class="text-xs font-medium text-gray-700 truncate max-w-[300px]">{{ event.chapter_title }}</span>
                            </div>

                            <!-- Interactions List -->
                            <div class="space-y-2">
                                <div v-for="(interaction, i) in event.interactions" :key="i" class="bg-white p-2 rounded border border-gray-100 text-sm shadow-sm">
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="text-[10px] font-bold uppercase" :class="interaction.direction === 'forward' ? 'text-indigo-500' : 'text-rose-500'">
                                            {{ interaction.relation }}
                                        </span>
                                        <span class="text-[10px] text-gray-400">
                                            {{ interaction.direction === 'forward' ? `${sourceEntity?.name} → ${targetEntity?.name}` : `${targetEntity?.name} → ${sourceEntity?.name}` }}
                                        </span>
                                    </div>
                                    <p class="text-gray-600 text-xs">{{ interaction.description }}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- RAW EVENTS (If no stages) -->
                <div v-else class="space-y-4">
                     <div v-for="event in group.events" :key="event.chapter_id" class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="font-bold text-gray-800 text-sm cursor-pointer hover:text-indigo-600" @click="emit('jump-to-chapter', event.chapter_id)">
                                Ch {{ event.chapter_index }}: {{ event.chapter_title }}
                            </h4>
                        </div>
                         <div class="space-y-2">
                                <div v-for="(interaction, i) in event.interactions" :key="i" class="bg-gray-50 p-2 rounded border border-gray-100 text-sm">
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="text-[10px] font-bold uppercase" :class="interaction.direction === 'forward' ? 'text-indigo-500' : 'text-rose-500'">
                                            {{ interaction.relation }}
                                        </span>
                                        <span class="text-[10px] text-gray-400">
                                            {{ interaction.direction === 'forward' ? `${sourceEntity?.name} → ${targetEntity?.name}` : `${targetEntity?.name} → ${sourceEntity?.name}` }}
                                        </span>
                                    </div>
                                    <p class="text-gray-600 text-xs">{{ interaction.description }}</p>
                                </div>
                            </div>
                     </div>
                </div>

            </template>
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
.chart {
  height: 100%;
  width: 100%;
}
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
