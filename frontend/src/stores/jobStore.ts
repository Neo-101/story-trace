import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

// --- Interfaces ---
export interface JobStatus {
  job_id: string;
  type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: any;
  error?: string;
  created_at: number;
  updated_at: number;
}

export interface RelationshipJobRequest {
  novel_name: string;
  file_hash: string;
  source: string;
  target: string;
  force?: boolean;
}

export const useJobStore = defineStore('jobs', () => {
  // State
  const activeJobId = ref<string | null>(null);
  const jobs = ref<Record<string, JobStatus>>({});
  const isPolling = ref(false);
  const pollingInterval = ref<number | null>(null);

  // Getters
  const activeJob = computed(() => activeJobId.value ? jobs.value[activeJobId.value] : null);
  const allJobs = computed(() => Object.values(jobs.value).sort((a, b) => b.created_at - a.created_at));

  // Actions
  async function submitRelationshipJob(request: RelationshipJobRequest) {
    if (activeJobId.value && jobs.value[activeJobId.value].status === 'processing') {
      console.warn("Already running a job.");
      // Optionally allow queueing, but for now just warn
    }

    try {
      const response = await axios.post('http://localhost:8000/api/jobs/relationship', request);
      const jobId = response.data.job_id;
      
      // Initialize job placeholder
      jobs.value[jobId] = {
        job_id: jobId,
        type: 'relationship_analysis',
        status: 'pending',
        progress: 0,
        message: 'Job submitted',
        created_at: Date.now() / 1000,
        updated_at: Date.now() / 1000
      };
      
      activeJobId.value = jobId;
      startPolling();
      return jobId;
    } catch (error) {
      console.error("Failed to submit job:", error);
      throw error;
    }
  }

  async function fetchJobStatus(jobId: string) {
    try {
      const response = await axios.get<JobStatus>(`http://localhost:8000/api/jobs/${jobId}`);
      const job = response.data;
      jobs.value[jobId] = job;
      
      // Update active job status logic
      if (job.status === 'completed' || job.status === 'failed') {
          // Keep it active so user can see result, but stop polling if no other jobs?
          // Actually we only poll the active one for now.
          stopPolling();
      }
      return job;
    } catch (error) {
      console.error(`Failed to fetch job ${jobId}:`, error);
    }
  }

  function startPolling() {
    // If already polling, don't start another interval
    if (pollingInterval.value !== null) return;
    
    isPolling.value = true;
    pollingInterval.value = window.setInterval(async () => {
      if (activeJobId.value) {
        // Only fetch if status is not final
        const job = jobs.value[activeJobId.value];
        if (job && (job.status === 'completed' || job.status === 'failed')) {
            stopPolling();
            return;
        }
        await fetchJobStatus(activeJobId.value);
      } else {
        stopPolling();
      }
    }, 2000); // Poll every 2 seconds
  }

  function stopPolling() {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value);
      pollingInterval.value = null;
    }
    isPolling.value = false;
  }
  
  function trackJob(jobId: string) {
    // Initialize job placeholder
    jobs.value[jobId] = {
      job_id: jobId,
      type: 'batch_relationship_analysis', // Assume batch for now, or fetch to correct
      status: 'pending',
      progress: 0,
      message: 'Job tracked',
      created_at: Date.now() / 1000,
      updated_at: Date.now() / 1000
    };
    
    activeJobId.value = jobId;
    startPolling();
  }

  function clearActiveJob() {
      activeJobId.value = null;
      stopPolling();
  }

  return {
    activeJobId,
    jobs,
    activeJob,
    allJobs,
    submitRelationshipJob,
    fetchJobStatus,
    trackJob,
    clearActiveJob
  };
});
