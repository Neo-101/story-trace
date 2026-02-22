<script setup lang="ts">
import { computed } from 'vue';
import type { RelationshipTimelineEvent, Entity, NarrativeState } from '@/types';

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

const currentState = computed<NarrativeState | undefined>(() => {
    // Find the latest narrative state from events
    // Since events are chronological, we look at the last event that has a state
    for (let i = props.events.length - 1; i >= 0; i--) {
        if (props.events[i].narrative_state) {
            return props.events[i].narrative_state;
        }
    }
    return undefined;
});

const typeStyles: Record<string, { bg: string, text: string, border: string }> = {
  'Person': { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200' },
  'Location': { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200' },
  'Organization': { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200' },
  'Event': { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-200' },
  'Object': { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-200' },
  'Concept': { bg: 'bg-pink-50', text: 'text-pink-800', border: 'border-pink-200' },
  'Other': { bg: 'bg-gray-50', text: 'text-gray-800', border: 'border-gray-200' }
};

const getStyle = (type: string) => typeStyles[type] || typeStyles['Other'];

</script>

<template>
  <!-- Drawer Container -->
  <div 
    class="fixed inset-y-0 right-0 w-[640px] bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col border-l border-gray-200"
    :class="isOpen ? 'translate-x-0' : 'translate-x-full'"
  >
    <!-- Header with 2 Entities -->
    <div class="p-6 border-b border-gray-100 flex-none bg-white/80 backdrop-blur z-10 relative">
        <!-- Close Button -->
        <button 
          @click="emit('close')"
          class="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors z-20"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div class="text-xs font-mono text-gray-400 mb-6 uppercase tracking-wider">Relationship Arc</div>

        <div class="flex items-center justify-between gap-4">
            <!-- Source Entity (Left) -->
            <div v-if="sourceEntity" class="flex flex-col items-center flex-1 group cursor-default">
                 <div 
                    class="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-bold shadow-sm mb-3 transition-transform group-hover:scale-105"
                    :class="getStyle(sourceEntity.type).bg + ' ' + getStyle(sourceEntity.type).text"
                >
                    {{ sourceEntity.name[0] }}
                </div>
                <span class="font-bold text-base text-center leading-tight text-gray-900">{{ sourceEntity.name }}</span>
                <span class="text-[10px] text-gray-400 mt-1 uppercase">{{ sourceEntity.type }}</span>
            </div>

            <!-- VS / Connection Icon -->
            <div class="flex flex-col items-center justify-center w-12 text-gray-300">
                <div class="w-full h-px bg-gray-200 mb-1"></div>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                <div class="w-full h-px bg-gray-200 mt-1"></div>
            </div>

            <!-- Target Entity (Right) -->
            <div v-if="targetEntity" class="flex flex-col items-center flex-1 group cursor-default">
                 <div 
                    class="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-bold shadow-sm mb-3 transition-transform group-hover:scale-105"
                    :class="getStyle(targetEntity.type).bg + ' ' + getStyle(targetEntity.type).text"
                >
                    {{ targetEntity.name[0] }}
                </div>
                <span class="font-bold text-base text-center leading-tight text-gray-900">{{ targetEntity.name }}</span>
                <span class="text-[10px] text-gray-400 mt-1 uppercase">{{ targetEntity.type }}</span>
            </div>
        </div>
        
        <!-- Narrative State Insights (New) -->
        <div v-if="currentState" class="mt-6 pt-4 border-t border-gray-100">
             <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Current Dynamic</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-600 border border-indigo-100">
                    {{ currentState.dominant_archetype }}
                </span>
             </div>
             
             <!-- Metrics -->
             <div class="grid grid-cols-3 gap-2 mb-3">
                <div class="bg-gray-50 rounded-lg p-2 text-center">
                    <div class="text-[10px] text-gray-400 uppercase">Trust</div>
                    <div class="text-sm font-bold text-gray-700">{{ currentState.trust_level }}%</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-2 text-center">
                    <div class="text-[10px] text-gray-400 uppercase">Romance</div>
                    <div class="text-sm font-bold text-gray-700">{{ currentState.romance_level }}%</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-2 text-center">
                    <div class="text-[10px] text-gray-400 uppercase">Conflict</div>
                    <div class="text-sm font-bold text-gray-700">{{ currentState.conflict_level }}%</div>
                </div>
             </div>
             
             <p class="text-xs text-gray-500 italic leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-100">
                "{{ currentState.summary_so_far }}"
             </p>
        </div>
    </div>

    <!-- Timeline Body -->
    <div class="flex-1 overflow-y-auto custom-scrollbar bg-gray-50/50 p-6 relative">
         <!-- Loading State -->
        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>

        <div v-if="events.length > 0" class="space-y-8">
            <div v-for="event in events" :key="event.chapter_id" class="relative mb-8">
                 <!-- Chapter Header (Sticky) -->
                 <div class="sticky top-0 z-20 flex justify-center mb-6">
                    <div 
                        class="bg-gray-50/95 backdrop-blur px-4 py-1.5 rounded-full border border-gray-200 shadow-sm flex items-center gap-2 cursor-pointer hover:bg-white hover:border-indigo-300 hover:shadow-md transition-all group"
                        @click="emit('jump-to-chapter', event.chapter_id)"
                    >
                        <span class="w-2 h-2 rounded-full bg-indigo-500 group-hover:scale-110 transition-transform"></span>
                        <span class="text-xs font-bold text-gray-600 group-hover:text-indigo-600">{{ event.chapter_title }}</span>
                    </div>
                 </div>

                 <!-- Timeline Grid -->
                 <div class="grid grid-cols-[1fr_2rem_1fr] gap-x-0 relative">
                    <!-- Central Line -->
                    <div class="absolute left-1/2 top-0 bottom-0 w-px bg-gray-200 -ml-px"></div>

                    <template v-for="(interaction, idx) in event.interactions" :key="idx">
                        <!-- Left Side (Forward: A -> B) -->
                        <div class="py-2 pr-4 flex justify-end">
                            <div v-if="interaction.direction === 'forward'" class="relative group max-w-[90%] w-full">
                                <!-- Card Content -->
                                <div class="bg-white p-3 rounded-xl border border-indigo-100 shadow-sm hover:shadow-md transition-all text-right relative">
                                    <!-- Connector Dot -->
                                    <div class="absolute top-1/2 -right-[1.35rem] w-2.5 h-2.5 rounded-full bg-indigo-500 border-2 border-white z-10 shadow-sm"></div>
                                    <!-- Connector Line -->
                                    <div class="absolute top-1/2 -right-4 w-4 h-px bg-indigo-200"></div>

                                    <div class="flex items-center justify-end gap-2 mb-1">
                                         <div class="text-[10px] font-medium text-indigo-400 bg-indigo-50 px-1.5 py-0.5 rounded">
                                            {{ sourceEntity?.name }} → {{ targetEntity?.name }}
                                        </div>
                                        <div class="text-xs font-bold text-indigo-600 uppercase tracking-wider">{{ interaction.relation }}</div>
                                    </div>
                                    <p class="text-xs text-gray-700 leading-relaxed">{{ interaction.description }}</p>
                                </div>
                            </div>
                        </div>

                        <!-- Center Axis (Empty for spacing) -->
                        <div></div>

                        <!-- Right Side (Backward: B -> A) -->
                        <div class="py-2 pl-4 flex justify-start">
                            <div v-if="interaction.direction === 'backward'" class="relative group max-w-[90%] w-full">
                                <!-- Card Content -->
                                <div class="bg-white p-3 rounded-xl border border-rose-100 shadow-sm hover:shadow-md transition-all text-left relative">
                                     <!-- Connector Dot -->
                                    <div class="absolute top-1/2 -left-[1.35rem] w-2.5 h-2.5 rounded-full bg-rose-500 border-2 border-white z-10 shadow-sm"></div>
                                    <!-- Connector Line -->
                                    <div class="absolute top-1/2 -left-4 w-4 h-px bg-rose-200"></div>

                                    <div class="flex items-center justify-start gap-2 mb-1">
                                        <div class="text-xs font-bold text-rose-600 uppercase tracking-wider">{{ interaction.relation }}</div>
                                        <div class="text-[10px] font-medium text-rose-400 bg-rose-50 px-1.5 py-0.5 rounded">
                                            {{ targetEntity?.name }} → {{ sourceEntity?.name }}
                                        </div>
                                    </div>
                                    <p class="text-xs text-gray-700 leading-relaxed">{{ interaction.description }}</p>
                                </div>
                            </div>
                        </div>
                    </template>
                 </div>
            </div>
            
            <div class="text-center pt-8 pb-4">
                <span class="text-xs text-gray-400 font-medium bg-gray-100 px-3 py-1 rounded-full">End of Timeline</span>
            </div>
        </div>
        
        <div v-else-if="!isLoading" class="flex flex-col items-center justify-center h-64 text-gray-400">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
             </svg>
             <p>No interactions found between these entities.</p>
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
