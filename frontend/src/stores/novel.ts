import { defineStore } from 'pinia';
import { API } from '@/api/client';
import type { Novel, Run, Chapter, Entity, GraphData, RelationshipStageLabel, PlotSegment, PlotArc } from '@/types';

export const useNovelStore = defineStore('novel', {
  state: () => ({
    novels: [] as Novel[],
    runs: [] as Run[],
    chapters: [] as Chapter[],
    currentNovel: null as Novel | null,
    currentRun: null as Run | null,
    currentChapter: null as Chapter | null,
    selectedChapterId: null as string | null,
    
    // Graph Data
    graphData: null as GraphData | null,
    globalEntities: [] as Entity[],
    relationshipStageIndex: [] as RelationshipStageLabel[],
    
    // Segments & Arcs
    segments: [] as PlotSegment[],
    arcs: [] as PlotArc[],

    // UI State
    loading: false,
    viewMode: 'overview' as 'overview' | 'focus' | 'encyclopedia' | 'graph' | 'reader',
    error: null as string | null,
  }),

  actions: {
    async loadNovels() {
      this.loading = true;
      try {
        this.novels = await API.fetchNovels();
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },

    async selectNovel(novel: Novel) {
      this.currentNovel = novel;
      this.currentRun = null;
      this.chapters = [];
      this.graphData = null;
      
      // Load runs
      if (novel.hashes.length > 0) {
        const hash = novel.hashes[0];
        if (!hash) return;
        
        const runs = await API.fetchRuns(novel.name, hash);
        this.runs = runs;
        const latestRun = runs[0];
        if (latestRun) {
          await this.selectRun(latestRun);
        }
      }
    },

    async selectRun(run: Run) {
      if (!this.currentNovel) return;
      const hash = this.currentNovel.hashes[0];
      if (!hash) return;

      this.currentRun = run;
      this.loading = true;
      // Reset data for new run
      this.graphData = null;
      this.globalEntities = [];
      this.relationshipStageIndex = [];
      this.segments = [];
      this.arcs = [];
      
      try {
        this.chapters = await API.fetchChapters(this.currentNovel.name, hash, run.timestamp);
        // Load segments & arcs in background
        this.loadSegments();
        this.loadArcs();
        // Reset view to overview on new run
        this.viewMode = 'overview';
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },

    async loadSegments() {
        if (!this.currentNovel || !this.currentRun) return;
        const hash = this.currentNovel.hashes[0];
        if (!hash) return;
        
        try {
            // First try to fetch existing segments
            let segments = await API.fetchSegments(this.currentNovel.name, hash);
            
            // If empty, trigger generation
            if (segments.length === 0) {
                console.log("No segments found, generating...");
                segments = await API.generateSegments(this.currentNovel.name, hash);
            }
            
            this.segments = segments;
        } catch (e: any) {
            console.error("Failed to load segments", e);
        }
    },

    async loadArcs() {
        if (!this.currentNovel || !this.currentRun) return;
        const hash = this.currentNovel.hashes[0];
        if (!hash) return;
        
        try {
            // First try to fetch existing arcs
            let arcs = await API.fetchArcs(this.currentNovel.name, hash);
            
            // If empty, trigger generation
            if (arcs.length === 0) {
                console.log("No arcs found, generating...");
                arcs = await API.generateArcs(this.currentNovel.name, hash);
            }
            
            this.arcs = arcs;
        } catch (e: any) {
            console.error("Failed to load arcs", e);
        }
    },

    async loadGlobalEntities() {
      if (!this.currentNovel || !this.currentRun) return;
      const hash = this.currentNovel.hashes[0];
      if (!hash) return;

      // If already loaded, skip
      if (this.globalEntities.length > 0) return;

      try {
        this.globalEntities = await API.fetchGlobalEntities(this.currentNovel.name, hash, this.currentRun.timestamp);
      } catch (e: any) {
        console.error("Failed to load global entities", e);
        // Non-blocking
      }
    },

    async loadChapterDetail(chapterId: string) {
      if (!this.currentNovel || !this.currentRun) return;
      const hash = this.currentNovel.hashes[0];
      if (!hash) return;

      this.loading = true;
      try {
        const chapter = await API.fetchChapterDetail(this.currentNovel.name, hash, this.currentRun.timestamp, chapterId);
        this.currentChapter = chapter;
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },

    async loadGraphData() {
        if (!this.currentNovel || !this.currentRun) return;
        const hash = this.currentNovel.hashes[0];
        if (!hash) return;

        // If already loaded, skip
        if (this.graphData) return;

        this.loading = true;
        try {
            this.graphData = await API.fetchGraphData(this.currentNovel.name, hash, this.currentRun.timestamp);
        } catch (e: any) {
            this.error = e.message;
        } finally {
            this.loading = false;
        }
    },

    async loadRelationshipStageIndex() {
        if (!this.currentNovel || !this.currentRun) return;
        const hash = this.currentNovel.hashes[0];
        if (!hash) return;

        // If already loaded, skip (unless we want force refresh?)
        if (this.relationshipStageIndex.length > 0) return;

        try {
            this.relationshipStageIndex = await API.fetchAllRelationshipStages(this.currentNovel.name, hash);
        } catch (e: any) {
            console.error("Failed to load relationship stages index", e);
            // Non-blocking error
        }
    }
  },
});
