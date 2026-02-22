<script setup lang="ts">
import { computed } from 'vue';
import { useJobStore } from '@/stores/jobStore';

const jobStore = useJobStore();
const job = computed(() => jobStore.activeJob);

// Don't show if no job
const isVisible = computed(() => !!job.value);

const statusColor = computed(() => {
    if (!job.value) return 'bg-gray-500';
    switch (job.value.status) {
        case 'pending': return 'bg-yellow-400';
        case 'processing': return 'bg-indigo-500';
        case 'completed': return 'bg-emerald-500';
        case 'failed': return 'bg-rose-500';
        default: return 'bg-gray-500';
    }
});

const progressWidth = computed(() => {
    return `${job.value?.progress || 0}%`;
});

function closeWidget() {
    jobStore.clearActiveJob();
}
</script>

<template>
    <div 
        v-if="isVisible"
        class="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2"
    >
        <!-- The Bubble Card -->
        <div class="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden w-80 transition-all duration-300 transform hover:scale-[1.02]">
            
            <!-- Header -->
            <div class="px-4 py-3 bg-gray-50/50 flex items-center justify-between border-b border-gray-100">
                <div class="flex items-center gap-2">
                    <span class="relative flex h-3 w-3">
                        <span 
                            v-if="job?.status === 'processing'"
                            class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                            :class="statusColor"
                        ></span>
                        <span class="relative inline-flex rounded-full h-3 w-3" :class="statusColor"></span>
                    </span>
                    <span class="text-xs font-bold text-gray-700 uppercase tracking-wider">
                        {{ job?.status === 'processing' ? '正在分析 (ANALYZING)' : 
                           job?.status === 'completed' ? '分析完成 (READY)' :
                           job?.status === 'failed' ? '分析失败 (FAILED)' : '排队中 (PENDING)' }}
                    </span>
                </div>
                
                <button @click="closeWidget" class="text-gray-400 hover:text-gray-600">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <!-- Body -->
            <div class="p-4">
                <p class="text-sm text-gray-600 font-medium mb-1 truncate">{{ job?.message }}</p>
                
                <!-- Progress Bar -->
                <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div 
                        class="h-full transition-all duration-500 ease-out"
                        :class="statusColor"
                        :style="{ width: progressWidth }"
                    ></div>
                </div>
                
                <div class="flex justify-between mt-2 text-[10px] text-gray-400 font-mono">
                    <span>{{ job?.progress }}%</span>
                    <span>{{ job?.type }}</span>
                </div>

                <!-- Result Action -->
                <div v-if="job?.status === 'completed'" class="mt-4">
                    <button 
                        class="w-full py-2 bg-emerald-50 text-emerald-600 hover:bg-emerald-100 rounded-lg text-xs font-bold transition-colors border border-emerald-100 flex items-center justify-center gap-2"
                        @click="$emit('view-result', job.result)"
                    >
                        <span>查看结果 (VIEW RESULT)</span>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                    </button>
                </div>

                <!-- Error Action -->
                <div v-if="job?.status === 'failed'" class="mt-4">
                     <p class="text-xs text-rose-500 bg-rose-50 p-2 rounded mb-2">{{ job.error }}</p>
                     <button 
                        class="w-full py-2 bg-gray-50 text-gray-600 hover:bg-gray-100 rounded-lg text-xs font-bold transition-colors border border-gray-200"
                        @click="closeWidget"
                    >
                        关闭 (CLOSE)
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
