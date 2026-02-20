<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { onMounted, ref, watch, onUnmounted, computed, shallowRef } from 'vue';
import { Network, DataSet } from "vis-network/standalone";
import type { Entity } from '@/types';

const store = useNovelStore();
const container = ref<HTMLElement | null>(null);
const network = shallowRef<Network | null>(null);

// State for filters and controls
const minWeight = ref(1);
const selectedTypes = ref<string[]>([]);
const physicsEnabled = ref(true);
const isLoading = ref(false);
const selectedEntity = ref<Entity | null>(null);

// DataSets for Vis.js
let nodesDataSet: DataSet<any> | null = null;
let edgesDataSet: DataSet<any> | null = null;

// Computed properties for UI
const availableTypes = computed(() => {
  if (!store.graphData) return [];
  const types = new Set(store.graphData.nodes.map(n => n.type));
  return Array.from(types).sort();
});

const filteredNodeCount = computed(() => {
    if (!nodesDataSet) return 0;
    return nodesDataSet.length;
});

const filteredEdgeCount = computed(() => {
    if (!edgesDataSet) return 0;
    return edgesDataSet.length;
});

// Initialize graph
const initGraph = () => {
  if (!container.value) return;

  nodesDataSet = new DataSet([]);
  edgesDataSet = new DataSet([]);

  const data = {
    nodes: nodesDataSet,
    edges: edgesDataSet
  };

  const options = {
    nodes: {
      shape: 'dot',
      size: 16,
      font: {
        size: 14,
        color: '#374151' // gray-700
      },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      width: 1,
      color: { inherit: 'from', opacity: 0.6 },
      smooth: {
        type: 'continuous'
      }
    },
    physics: {
      enabled: true,
      stabilization: {
        iterations: 100
      },
      barnesHut: {
        gravitationalConstant: -2000,
        centralGravity: 0.3,
        springLength: 95,
        springConstant: 0.04,
        damping: 0.09,
        avoidOverlap: 0.1
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      hideEdgesOnDrag: true
    }
  };

  network.value = new Network(container.value, data, options);

  // Event listeners
  network.value.on("click", (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const entity = store.graphData?.nodes.find(n => n.name === nodeId);
      if (entity) {
        selectedEntity.value = entity;
      }
    } else {
        selectedEntity.value = null;
    }
  });

  // Initial update if data is already available
  if (store.graphData) {
      updateGraphData();
  }
};

// Color palette for entity types
const typeColors: Record<string, string> = {
  'Person': '#6366f1', // indigo-500
  'Location': '#10b981', // emerald-500
  'Organization': '#ef4444', // red-500
  'Event': '#f59e0b', // amber-500
  'Object': '#8b5cf6', // violet-500
  'Other': '#6b7280' // gray-500
};

const getTypeColor = (type: string) => {
  return typeColors[type] || typeColors['Other'];
};

// Update graph data based on filters
const updateGraphData = () => {
  if (!store.graphData || !nodesDataSet || !edgesDataSet) return;

  const allNodes = store.graphData.nodes;
  const allEdges = store.graphData.edges;

  // 1. Filter Nodes by Type
  const validNodeIds = new Set<string>();
  const filteredNodes = allNodes.filter(node => {
    const typeMatch = selectedTypes.value.length === 0 || selectedTypes.value.includes(node.type);
    if (typeMatch) {
      validNodeIds.add(node.name);
    }
    return typeMatch;
  });

  // 2. Filter Edges by Weight and valid Nodes
  const filteredEdges = allEdges.filter(edge => {
    const weightMatch = edge.weight >= minWeight.value;
    const nodesExist = validNodeIds.has(edge.source) && validNodeIds.has(edge.target);
    return weightMatch && nodesExist;
  });

  // 3. Update DataSets (diff update for performance)
  nodesDataSet.clear();
  edgesDataSet.clear();

  // Deduplicate nodes by ID (name) before adding to DataSet
  const uniqueNodes = new Map();
  filteredNodes.forEach(n => {
      if (!uniqueNodes.has(n.name)) {
          uniqueNodes.set(n.name, n);
      }
  });

  nodesDataSet.add(Array.from(uniqueNodes.values()).map(n => ({
    id: n.name,
    label: n.name,
    group: n.type,
    value: n.count || 1, // Size based on importance
    title: `Type: ${n.type}<br>Count: ${n.count}<br>${n.description?.slice(0, 100)}...`, // Tooltip
    color: {
      background: getTypeColor(n.type),
      border: '#ffffff',
      highlight: {
        background: getTypeColor(n.type),
        border: '#1f2937'
      }
    }
  })));

  edgesDataSet.add(filteredEdges.map(e => ({
    from: e.source,
    to: e.target,
    value: e.weight, // Width based on weight
    title: `Weight: ${e.weight}`,
    arrows: 'to'
  })));
  
  // Fit view if it's the first load or significant change
  // network.value?.fit(); 
};

// Watchers
watch(() => store.graphData, (newData) => {
  if (newData) {
    // Initialize selected types if empty
    if (selectedTypes.value.length === 0) {
        const types = new Set(newData.nodes.map(n => n.type));
        selectedTypes.value = Array.from(types);
    }
    // Force update when data arrives
    updateGraphData();
  }
}, { deep: true, immediate: true });

watch([minWeight, selectedTypes], () => {
  updateGraphData();
});

watch(physicsEnabled, (enabled) => {
  if (network.value) {
    network.value.setOptions({ physics: { enabled } });
  }
});

// Lifecycle
onMounted(async () => {
  initGraph();
  isLoading.value = true;
  try {
      await store.loadGraphData();
  } finally {
      isLoading.value = false;
  }
});

onUnmounted(() => {
  if (network.value) {
    network.value.destroy();
    network.value = null;
  }
  nodesDataSet = null;
  edgesDataSet = null;
});

const toggleType = (type: string) => {
  if (selectedTypes.value.includes(type)) {
    selectedTypes.value = selectedTypes.value.filter(t => t !== type);
  } else {
    selectedTypes.value.push(type);
  }
};
</script>

<template>
  <div class="h-full w-full relative bg-gray-50 overflow-hidden">
    <!-- Graph Container -->
    <div ref="container" class="w-full h-full cursor-grab active:cursor-grabbing"></div>

    <!-- Loading State -->
    <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/80 z-50">
        <div class="flex flex-col items-center">
            <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-2"></div>
            <span class="text-gray-600 font-medium">Loading Graph...</span>
        </div>
    </div>

    <!-- Entity Details Panel -->
    <div v-if="selectedEntity" class="absolute top-4 left-4 w-80 bg-white/95 backdrop-blur shadow-xl rounded-xl p-5 border border-gray-200 z-20 max-h-[85vh] overflow-y-auto transition-all duration-300">
      <div class="flex justify-between items-start mb-3">
        <h2 class="text-xl font-bold text-gray-900 leading-tight">{{ selectedEntity.name }}</h2>
        <button @click="selectedEntity = null" class="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      
      <span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 mb-4">
        {{ selectedEntity.type }}
      </span>
      
      <div class="prose prose-sm text-gray-700 leading-relaxed mb-4 max-h-60 overflow-y-auto custom-scrollbar">
        {{ selectedEntity.description || '暂无描述' }}
      </div>
      
      <div class="flex items-center justify-between text-xs text-gray-500 border-t border-gray-100 pt-3 mt-2">
        <div class="flex flex-col">
            <span class="font-medium text-gray-900">{{ selectedEntity.count }}</span>
            <span>Mentions</span>
        </div>
        <div class="flex flex-col text-right">
            <span class="font-medium text-gray-900">{{ selectedEntity.chapter_ids?.length || 0 }}</span>
            <span>Chapters</span>
        </div>
      </div>
    </div>

    <!-- Controls Overlay -->
    <div class="absolute top-4 right-4 bg-white/90 backdrop-blur shadow-lg rounded-lg p-4 w-64 border border-gray-200 z-10 max-h-[90vh] overflow-y-auto">
      <h3 class="font-bold text-gray-800 mb-3 flex items-center justify-between">
        <span>Graph Controls</span>
        <span class="text-xs font-normal text-gray-500">{{ filteredNodeCount }} nodes, {{ filteredEdgeCount }} edges</span>
      </h3>
      
      <!-- Physics Toggle -->
      <div class="mb-4 flex items-center justify-between">
        <label class="text-sm text-gray-700 font-medium">Physics</label>
        <button 
            @click="physicsEnabled = !physicsEnabled"
            :class="physicsEnabled ? 'bg-indigo-600' : 'bg-gray-300'"
            class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none"
        >
            <span 
                :class="physicsEnabled ? 'translate-x-5' : 'translate-x-1'"
                class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform"
            ></span>
        </button>
      </div>

      <!-- Min Weight Slider -->
      <div class="mb-4">
        <div class="flex justify-between mb-1">
            <label class="text-sm text-gray-700 font-medium">Min Interactions</label>
            <span class="text-xs text-gray-500 font-mono">{{ minWeight }}</span>
        </div>
        <input 
          type="range" 
          v-model.number="minWeight" 
          min="1" 
          max="20" 
          step="1"
          class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
        >
      </div>

      <!-- Entity Types Filter -->
      <div class="mb-2">
        <label class="text-sm text-gray-700 font-medium block mb-2">Entity Types</label>
        <div class="space-y-1.5 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
          <div v-for="type in availableTypes" :key="type" class="flex items-center">
            <input 
              type="checkbox" 
              :id="`type-${type}`" 
              :checked="selectedTypes.includes(type)"
              @change="toggleType(type)"
              class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            >
            <label :for="`type-${type}`" class="ml-2 text-sm text-gray-600 truncate cursor-pointer select-none">
              {{ type }}
            </label>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="mt-4 pt-3 border-t border-gray-100">
        <button 
            @click="network?.fit({ animation: true })"
            class="w-full py-1.5 px-3 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded transition-colors"
        >
            Reset View
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
