<script setup lang="ts">
import { RouterView } from 'vue-router'
import JobStatusWidget from '@/components/JobStatusWidget.vue'
import { useJobStore } from '@/stores/jobStore'

const jobStore = useJobStore()

function handleViewResult(result: any) {
    // Ideally we should emit this event to the current view or use a global event bus
    // But since GraphView is deeply nested, we might need a better way.
    // For v1, if we are on GraphView, we can refresh?
    // Actually, JobStatusWidget is global.
    // Let's use a global state in jobStore to signal "Show Result for Pair X"
    // Or just let the user click the button and we close the widget?
    // The "View Result" button in the widget should probably just trigger the drawer.
    // But the drawer is inside GraphView.
    // We can use a global event bus or store flag.
    
    // For now, let's just close the widget and let the user manually check.
    // Wait, that's bad UX.
    // Let's add a `resultTrigger` to jobStore.
    jobStore.clearActiveJob()
    
    // We need to tell GraphView to open the drawer.
    // Since we don't have a global event bus handy, let's just log it for now.
    // Or we can dispatch a custom window event.
    window.dispatchEvent(new CustomEvent('open-relationship-result', { detail: result }));
}
</script>

<template>
  <RouterView />
  <JobStatusWidget @view-result="handleViewResult" />
</template>
