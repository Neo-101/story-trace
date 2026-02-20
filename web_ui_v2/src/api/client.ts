import axios from 'axios';
import type { Novel, Run, Chapter, Entity, GraphData } from '@/types';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const API = {
  async fetchNovels(): Promise<Novel[]> {
    const response = await apiClient.get<Novel[]>('/novels');
    return response.data;
  },

  async fetchRuns(novelName: string, hash: string): Promise<Run[]> {
    const response = await apiClient.get<Run[]>(`/novels/${novelName}/${hash}/runs`);
    return response.data;
  },

  async fetchChapters(novelName: string, hash: string, timestamp: string): Promise<Chapter[]> {
    const response = await apiClient.get<Chapter[]>(`/novels/${novelName}/${hash}/${timestamp}/chapters`);
    return response.data;
  },

  async fetchChapterDetail(novelName: string, hash: string, timestamp: string, chapterId: string): Promise<Chapter> {
    const response = await apiClient.get<Chapter>(`/novels/${novelName}/${hash}/${timestamp}/chapters/${chapterId}`);
    return response.data;
  },

  async fetchGlobalEntities(novelName: string, hash: string, timestamp: string): Promise<Entity[]> {
    const response = await apiClient.get<Entity[]>(`/novels/${novelName}/${hash}/${timestamp}/entities`);
    return response.data;
  },

  async fetchGraphData(novelName: string, hash: string, timestamp: string): Promise<GraphData> {
    const response = await apiClient.get<GraphData>(`/novels/${novelName}/${hash}/${timestamp}/graph`);
    return response.data;
  },
};
