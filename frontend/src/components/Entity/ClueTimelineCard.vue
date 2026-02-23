<script setup lang="ts">
import { computed } from 'vue';
import type { ClueState } from '@/types';

const props = defineProps<{
  lifecycle: ClueState[];
}>();

const sortedLifecycle = computed(() => {
  if (!props.lifecycle) return [];
  return [...props.lifecycle].sort((a, b) => a.chapter_index - b.chapter_index);
});

const getStateColor = (state: string) => {
  switch (state.toLowerCase()) {
    case 'setup': return 'bg-blue-50 text-blue-700 border-blue-200 ring-blue-500/10';
    case 'reminder': return 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-500/10';
    case 'payoff': return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-500/10';
    case 'forgotten': return 'bg-gray-50 text-gray-500 border-gray-200 ring-gray-500/10 grayscale opacity-80';
    default: return 'bg-slate-50 text-slate-600 border-slate-200 ring-slate-500/10';
  }
};

const getStateIcon = (state: string) => {
  switch (state.toLowerCase()) {
    case 'setup': return '🌱'; // Seed/Plant
    case 'reminder': return '🔔'; // Bell
    case 'payoff': return '💥'; // Explosion/Impact
    case 'forgotten': return '🕸️'; // Cobweb
    default: return '•';
  }
};

const getStateLabel = (state: string) => {
    switch (state.toLowerCase()) {
    case 'setup': return '引入 (Setup)';
    case 'reminder': return '重提 (Reminder)';
    case 'payoff': return '爆发 (Payoff)';
    case 'forgotten': return '遗忘 (Forgotten)';
    default: return state;
  }
}
</script>

<template>
  <div v-if="sortedLifecycle.length > 0" class="w-full">
    <div class="flex items-center gap-2 mb-3 px-1">
      <div class="w-1 h-4 bg-indigo-500 rounded-full"></div>
      <h3 class="text-sm font-semibold text-gray-900">伏笔生命周期</h3>
      <span class="text-xs font-mono text-gray-400 ml-auto">{{ sortedLifecycle.length }} 节点</span>
    </div>

    <div class="relative pl-2 ml-1 space-y-0">
      <!-- Vertical Timeline Line -->
      <div class="absolute left-[7px] top-2 bottom-2 w-0.5 bg-gray-100 rounded-full"></div>

      <div 
        v-for="(item, index) in sortedLifecycle" 
        :key="index" 
        class="relative pl-6 pb-6 last:pb-0 group"
      >
        <!-- Timeline Dot -->
        <div 
            class="absolute left-0 top-1.5 w-4 h-4 rounded-full bg-white border-2 border-gray-200 z-10 group-hover:border-indigo-400 group-hover:scale-110 transition-all duration-300 shadow-sm flex items-center justify-center"
        >
            <div class="w-1.5 h-1.5 rounded-full bg-gray-300 group-hover:bg-indigo-500 transition-colors"></div>
        </div>

        <!-- Content Card -->
        <div class="flex flex-col gap-1.5">
            <!-- Header: Chapter + State Badge -->
            <div class="flex flex-wrap items-center gap-2">
                <span class="text-[10px] font-mono font-bold text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded border border-gray-100 min-w-[3rem] text-center">
                    Ch.{{ item.chapter_index }}
                </span>
                <span 
                    :class="[
                        'text-[10px] font-medium px-2 py-0.5 rounded-full border shadow-sm ring-1 ring-inset flex items-center gap-1', 
                        getStateColor(item.state)
                    ]"
                >
                    <span>{{ getStateIcon(item.state) }}</span>
                    <span>{{ getStateLabel(item.state) }}</span>
                </span>
            </div>

            <!-- Context Text -->
            <div class="relative group/text">
                <p class="text-xs text-gray-600 leading-relaxed p-2.5 rounded-lg bg-gray-50/50 border border-gray-100/50 hover:bg-white hover:border-gray-200 hover:shadow-sm transition-all duration-200">
                    {{ item.context }}
                </p>
                <!-- Connector Arrow -->
                <!-- <div class="absolute -left-[18px] top-3 w-3 h-[1px] bg-gray-200 group-hover/text:bg-indigo-200 transition-colors"></div> -->
            </div>
        </div>
      </div>
    </div>
  </div>
</template>
