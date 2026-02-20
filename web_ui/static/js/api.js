// API Utility for StoryTrace
// Provides functions to fetch data from the backend

export const API = {
    async fetchNovels() {
        const res = await fetch('/api/novels');
        return await res.json();
    },

    async fetchRuns(novelName, hash) {
        const res = await fetch(`/api/novels/${novelName}/${hash}/runs`);
        return await res.json();
    },

    async fetchChapters(novelName, hash, timestamp) {
        const res = await fetch(`/api/novels/${novelName}/${hash}/${timestamp}/chapters`);
        return await res.json();
    },

    async fetchChapterDetail(novelName, hash, timestamp, chapterId) {
        const res = await fetch(`/api/novels/${novelName}/${hash}/${timestamp}/chapters/${chapterId}`);
        return await res.json();
    },

    async fetchGlobalEntities(novelName, hash, timestamp) {
        const res = await fetch(`/api/novels/${novelName}/${hash}/${timestamp}/entities`);
        return await res.json();
    },

    async fetchGraphData(novelName, hash, timestamp) {
        const res = await fetch(`/api/novels/${novelName}/${hash}/${timestamp}/graph`);
        return await res.json();
    }
};
