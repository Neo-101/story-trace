import { defineStore } from 'pinia';
import { API } from '@/api/client';
import type { Novel, Run, Chapter, Entity, GraphData } from '@/types';

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

    // UI State
    loading: false,
    viewMode: 'overview' as 'overview' | 'focus' | 'encyclopedia' | 'graph',
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
      try {
        this.chapters = await API.fetchChapters(this.currentNovel.name, hash, run.timestamp);
        // Reset view to overview on new run
        this.viewMode = 'overview';
      } catch (e: any) {
        this.error = e.message;
      } finally {
        this.loading = false;
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
    }
  },
});
