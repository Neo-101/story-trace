<script setup lang="ts">
import type { Entity } from '@/types';

defineProps<{
  entity: Entity;
  typeColors: Record<string, string>;
}>();

defineEmits<{
  (e: 'close'): void;
}>();
</script>

<template>
  <div class="flex items-start justify-between mb-4">
    <div 
      class="w-12 h-12 rounded-lg flex items-center justify-center text-xl font-bold shadow-sm"
      :style="{ backgroundColor: typeColors[entity.type] + '20', color: typeColors[entity.type] }"
    >
      {{ entity.name[0] }}
    </div>
    <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
  
  <h2 class="text-xl font-bold text-gray-900 mb-1">{{ entity.name }}</h2>
  <span 
    class="inline-block px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider mb-4" 
    :style="{ backgroundColor: typeColors[entity.type] + '20', color: typeColors[entity.type] }"
  >
    {{ entity.type }}
  </span>
</template>
