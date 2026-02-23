<script setup lang="ts">
import type { Entity } from '@/types';
import EntityHeader from './EntityHeader.vue';
import ConceptEvolutionCard from './ConceptEvolutionCard.vue';

defineProps<{
  entity: Entity;
  description: string;
  typeColors: Record<string, string>;
}>();

defineEmits<{
  (e: 'close'): void;
}>();
</script>

<template>
  <div class="absolute top-4 right-4 w-80 bg-white/95 backdrop-blur shadow-xl rounded-xl border border-gray-100 p-6 z-20 transition-all animate-in slide-in-from-right-4">
    <!-- 1. Common Header -->
    <EntityHeader 
      :entity="entity" 
      :type-colors="typeColors"
      @close="$emit('close')"
    />

    <!-- 2. Base Description -->
    <p class="text-sm text-gray-600 leading-relaxed mb-6 max-h-60 overflow-y-auto custom-scrollbar">
      {{ description }}
    </p>
    
    <!-- 3. Dynamic Modules Slot (Vibe Coding Extension Point) -->
    <!-- This is where Agent B and Agent C will inject their components -->
    <div class="space-y-4 mb-6">
        <slot name="modules">
            <ConceptEvolutionCard 
                v-if="entity.concept_evolution && entity.concept_evolution.length > 0" 
                :stages="entity.concept_evolution" 
            />
        </slot>
    </div>

    <!-- 4. Actions Slot -->
    <div class="space-y-2">
      <slot name="actions"></slot>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}
</style>
