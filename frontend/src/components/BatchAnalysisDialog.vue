<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl w-3/4 max-h-[85vh] flex flex-col">
      <div class="p-4 border-b flex justify-between items-center">
        <h2 class="text-xl font-bold">Batch Relationship Analysis</h2>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Type Filters -->
      <div class="p-4 bg-gray-50 border-b space-y-3">
        <div class="flex items-center gap-4 text-sm">
          <span class="font-bold w-16">Source:</span>
          <div class="flex flex-wrap gap-2">
             <label v-for="type in availableTypes" :key="'s-'+type" 
                class="inline-flex items-center gap-1.5 cursor-pointer px-2 py-1 rounded hover:bg-white hover:shadow-sm border border-transparent transition-all" 
                :class="{'bg-white shadow-sm border-gray-200': sourceFilters.includes(type)}">
                <input type="checkbox" :value="type" v-model="sourceFilters" class="rounded text-indigo-600 focus:ring-indigo-500">
                
                <!-- Icon -->
                <div class="w-3 h-3 flex items-center justify-center" :style="{ color: typeColors[type] }">
                    <div v-if="typeShapes[type] === 'dot'" class="w-2.5 h-2.5 rounded-full bg-current"></div>
                    <div v-else-if="typeShapes[type] === 'square'" class="w-2.5 h-2.5 bg-current rounded-[1px]"></div>
                    <div v-else-if="typeShapes[type] === 'triangle'" class="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[9px] border-l-transparent border-r-transparent border-b-current mb-0.5"></div>
                    <div v-else-if="typeShapes[type] === 'diamond'" class="w-2 h-2 bg-current rotate-45"></div>
                    <svg v-else-if="typeShapes[type] === 'star'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    <svg v-else-if="typeShapes[type] === 'hexagon'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l8.66 5v10L12 22l-8.66-5V7L12 2z"/></svg>
                </div>

                <span>{{ typeLabels[type] || type }}</span>
             </label>
          </div>
        </div>
        <div class="flex items-center gap-4 text-sm">
          <span class="font-bold w-16">Target:</span>
          <div class="flex flex-wrap gap-2">
             <label v-for="type in availableTypes" :key="'t-'+type" 
                class="inline-flex items-center gap-1.5 cursor-pointer px-2 py-1 rounded hover:bg-white hover:shadow-sm border border-transparent transition-all" 
                :class="{'bg-white shadow-sm border-gray-200': targetFilters.includes(type)}">
                <input type="checkbox" :value="type" v-model="targetFilters" class="rounded text-pink-600 focus:ring-pink-500">
                
                 <!-- Icon -->
                <div class="w-3 h-3 flex items-center justify-center" :style="{ color: typeColors[type] }">
                    <div v-if="typeShapes[type] === 'dot'" class="w-2.5 h-2.5 rounded-full bg-current"></div>
                    <div v-else-if="typeShapes[type] === 'square'" class="w-2.5 h-2.5 bg-current rounded-[1px]"></div>
                    <div v-else-if="typeShapes[type] === 'triangle'" class="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[9px] border-l-transparent border-r-transparent border-b-current mb-0.5"></div>
                    <div v-else-if="typeShapes[type] === 'diamond'" class="w-2 h-2 bg-current rotate-45"></div>
                    <svg v-else-if="typeShapes[type] === 'star'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    <svg v-else-if="typeShapes[type] === 'hexagon'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l8.66 5v10L12 22l-8.66-5V7L12 2z"/></svg>
                </div>

                <span>{{ typeLabels[type] || type }}</span>
             </label>
          </div>
        </div>
        <div class="text-xs text-gray-500 italic">
          * Matches are bidirectional (A-B matches if A=Source, B=Target OR A=Target, B=Source)
        </div>
      </div>

      <div class="p-4 flex-1 overflow-auto">
        <div class="flex justify-between mb-2">
          <div class="space-x-2">
            <button @click="selectAll" class="text-sm text-blue-600 hover:underline">Select All</button>
            <span class="text-gray-300">|</span>
            <button @click="deselectAll" class="text-sm text-blue-600 hover:underline">Deselect All</button>
          </div>
          <div class="text-sm text-gray-500">
            Selected: {{ selectedCount }} / {{ filteredPairs.length }} (Total visible: {{ pairs.length }})
          </div>
        </div>

        <table class="min-w-full border text-sm">
          <thead class="bg-gray-50 sticky top-0 z-10">
            <tr>
              <th class="p-2 border w-10">
                <input type="checkbox" :checked="isAllSelected" @change="toggleAll" />
              </th>
              <th class="p-2 border text-left">Source Entity</th>
              <th class="p-2 border text-left">Target Entity</th>
              <th class="p-2 border text-right">Interactions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pair in filteredPairs" :key="pair.id" class="hover:bg-gray-50">
              <td class="p-2 border text-center">
                <input type="checkbox" v-model="pair.selected" />
              </td>
              <td class="p-2 border">
                <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded flex items-center justify-center bg-opacity-20" :style="{ backgroundColor: typeColors[pair.sourceType] + '20' }">
                        <div class="w-3 h-3 flex items-center justify-center" :style="{ color: typeColors[pair.sourceType] }">
                            <div v-if="typeShapes[pair.sourceType] === 'dot'" class="w-2.5 h-2.5 rounded-full bg-current"></div>
                            <div v-else-if="typeShapes[pair.sourceType] === 'square'" class="w-2.5 h-2.5 bg-current rounded-[1px]"></div>
                            <div v-else-if="typeShapes[pair.sourceType] === 'triangle'" class="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[9px] border-l-transparent border-r-transparent border-b-current mb-0.5"></div>
                            <div v-else-if="typeShapes[pair.sourceType] === 'diamond'" class="w-2 h-2 bg-current rotate-45"></div>
                            <svg v-else-if="typeShapes[pair.sourceType] === 'star'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                            <svg v-else-if="typeShapes[pair.sourceType] === 'hexagon'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l8.66 5v10L12 22l-8.66-5V7L12 2z"/></svg>
                        </div>
                    </div>
                    <span class="font-medium">{{ pair.source }}</span>
                </div>
              </td>
              <td class="p-2 border">
                 <div class="flex items-center gap-2">
                    <div class="w-6 h-6 rounded flex items-center justify-center bg-opacity-20" :style="{ backgroundColor: typeColors[pair.targetType] + '20' }">
                        <div class="w-3 h-3 flex items-center justify-center" :style="{ color: typeColors[pair.targetType] }">
                            <div v-if="typeShapes[pair.targetType] === 'dot'" class="w-2.5 h-2.5 rounded-full bg-current"></div>
                            <div v-else-if="typeShapes[pair.targetType] === 'square'" class="w-2.5 h-2.5 bg-current rounded-[1px]"></div>
                            <div v-else-if="typeShapes[pair.targetType] === 'triangle'" class="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[9px] border-l-transparent border-r-transparent border-b-current mb-0.5"></div>
                            <div v-else-if="typeShapes[pair.targetType] === 'diamond'" class="w-2 h-2 bg-current rotate-45"></div>
                            <svg v-else-if="typeShapes[pair.targetType] === 'star'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                            <svg v-else-if="typeShapes[pair.targetType] === 'hexagon'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3"><path d="M12 2l8.66 5v10L12 22l-8.66-5V7L12 2z"/></svg>
                        </div>
                    </div>
                    <span class="font-medium">{{ pair.target }}</span>
                </div>
              </td>
              <td class="p-2 border text-right">{{ pair.weight }}</td>
            </tr>
            <tr v-if="filteredPairs.length === 0">
              <td colspan="4" class="p-8 text-center text-gray-500">
                No pairs match the selected type filters.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="p-4 border-t flex justify-end space-x-3">
        <button @click="close" class="px-4 py-2 border rounded text-gray-600 hover:bg-gray-100">Cancel</button>
        <button 
          @click="startBatch" 
          :disabled="selectedCount === 0 || isSubmitting"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
        >
          <span v-if="isSubmitting" class="mr-2 animate-spin">⏳</span>
          Start Analysis ({{ selectedCount }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { API } from '@/api/client';
import { useJobStore } from '@/stores/jobStore';
import { useNovelStore } from '@/stores/novel';

const props = defineProps<{
  isOpen: boolean;
  visibleEdges: any[]; // Vis.js edges with injected sourceType/targetType
}>();

const emit = defineEmits(['close', 'job-started']);

const jobStore = useJobStore();
const novelStore = useNovelStore();

interface BatchPair {
  id: string;
  source: string;
  target: string;
  sourceType: string;
  targetType: string;
  weight: number;
  selected: boolean;
}

const pairs = ref<BatchPair[]>([]);
const isSubmitting = ref(false);

// Filters
const availableTypes = ['Person', 'Location', 'Organization', 'Event', 'Object', 'Concept'];
const sourceFilters = ref<string[]>(['Person']); // Default to Person
const targetFilters = ref<string[]>(['Person', 'Location', 'Organization']); // Default broad

// --- Style Constants (Copied from GraphView.vue) ---
const typeColors: Record<string, string> = {
  'Person': '#fbbf24', // amber-400
  'Location': '#60a5fa', // blue-400
  'Organization': '#a78bfa', // purple-400
  'Event': '#f87171', // red-400
  'Object': '#34d399', // emerald-400
  'Concept': '#f472b6', // pink-400
  'Other': '#9ca3af'   // gray-400
};

const typeShapes: Record<string, string> = {
  'Person': 'dot',
  'Location': 'triangle',
  'Organization': 'square',
  'Event': 'star',
  'Object': 'diamond',
  'Concept': 'hexagon',
  'Other': 'dot'
};

const typeLabels: Record<string, string> = {
  'Person': '人物',
  'Location': '地点',
  'Organization': '组织',
  'Event': '事件',
  'Object': '物品',
  'Concept': '概念',
  'Other': '其他'
};

// Initialize pairs when dialog opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    // Deduplicate pairs based on sorted names
    const seen = new Set<string>();
    const uniquePairs: BatchPair[] = [];

    props.visibleEdges.forEach(edge => {
      // Vis.js uses 'from'/'to' which are names/ids
      const source = edge.from; 
      const target = edge.to;
      const sType = edge.sourceType || 'Unknown';
      const tType = edge.targetType || 'Unknown';

      // Create a unique key regardless of order
      const key = [source, target].sort().join('_');
      
      if (!seen.has(key)) {
        seen.add(key);
        uniquePairs.push({
          id: edge.id,
          source: source,
          target: target,
          sourceType: sType,
          targetType: tType,
          weight: edge.value || 0,
          selected: true // Default select, but will be filtered by display logic
        });
      }
    });
    
    // Sort by weight (interactions) descending for better UX
    pairs.value = uniquePairs.sort((a, b) => b.weight - a.weight);
  }
});

// Computed filtered pairs based on type selection
const filteredPairs = computed(() => {
  return pairs.value.filter(p => {
    // Check direct match: Source -> SourceFilter AND Target -> TargetFilter
    const directMatch = sourceFilters.value.includes(p.sourceType) && targetFilters.value.includes(p.targetType);
    
    // Check reverse match (Symmetry): Source -> TargetFilter AND Target -> SourceFilter
    // Because relationship analysis is undirected (A-B is same as B-A)
    const reverseMatch = sourceFilters.value.includes(p.targetType) && targetFilters.value.includes(p.sourceType);

    return directMatch || reverseMatch;
  });
});

const selectedCount = computed(() => filteredPairs.value.filter(p => p.selected).length);
const isAllSelected = computed(() => filteredPairs.value.length > 0 && selectedCount.value === filteredPairs.value.length);

function selectAll() {
  filteredPairs.value.forEach(p => p.selected = true);
}

function deselectAll() {
  filteredPairs.value.forEach(p => p.selected = false);
}

function toggleAll(e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  filteredPairs.value.forEach(p => p.selected = checked);
}

function close() {
  emit('close');
}

async function startBatch() {
  const selectedPairs = filteredPairs.value.filter(p => p.selected);
  if (selectedPairs.length === 0) return;

  isSubmitting.value = true;
  try {
    const payload = selectedPairs.map(p => ({
      source: p.source,
      target: p.target
    }));

    if (!novelStore.currentNovel || !novelStore.currentRun) {
        throw new Error("No novel context");
    }

    const res = await API.submitBatchRelationshipAnalysis(
        novelStore.currentNovel.name,
        novelStore.currentRun.file_hash,
        payload
    );

    jobStore.trackJob(res.job_id);
    emit('job-started', res.job_id);
    close();
  } catch (e) {
    console.error(e);
    alert("Failed to start batch job: " + e);
  } finally {
    isSubmitting.value = false;
  }
}
</script>
