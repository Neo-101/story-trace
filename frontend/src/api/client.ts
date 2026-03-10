import axios from 'axios';
import type { Novel, Run, Chapter, Entity, GraphData, TimelineEvent, RelationshipTimelineEvent, RelationshipStage, RelationshipStageLabel, PlotSegment, PlotArc } from '@/types';

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

  async fetchEntityTimeline(novelName: string, hash: string, timestamp: string, entityName: string): Promise<TimelineEvent[]> {
    const response = await apiClient.get<TimelineEvent[]>(`/novels/${novelName}/${hash}/${timestamp}/entity/${encodeURIComponent(entityName)}/timeline`);
    return response.data;
  },

  async fetchRelationshipTimeline(novelName: string, hash: string, timestamp: string, source: string, target: string): Promise<RelationshipTimelineEvent[]> {
    const response = await apiClient.get<RelationshipTimelineEvent[]>(`/novels/${novelName}/${hash}/${timestamp}/relationship`, {
      params: { source, target, _t: Date.now() }
    });
    return response.data;
  },

  async deleteRelationshipAnalysis(novelName: string, hash: string, source: string, target: string): Promise<void> {
    await apiClient.delete(`/novels/${novelName}/${hash}/relationship`, {
      params: { source, target }
    });
  },

  async submitBatchRelationshipAnalysis(novelName: string, fileHash: string, pairs: {source: string, target: string}[]): Promise<{ job_id: string }> {
    const response = await apiClient.post<{ job_id: string }>('/jobs/batch-relationship', {
      novel_name: novelName,
      file_hash: fileHash,
      pairs: pairs
    });
    return response.data;
  },

  async analyzeConcept(novelName: string, fileHash: string, entityName: string, force: boolean = false): Promise<any[]> {
    // Note: Concept Evolution API currently returns List[ConceptStage] directly
    const response = await apiClient.post<any[]>(`/novels/${novelName}/${fileHash}/analyze/concept`, {
      entity_name: entityName,
      force: force
    });
    return response.data;
  },

  async analyzeGroupSummary(novelName: string, fileHash: string, entityName: string, start: number, end: number, force: boolean = false): Promise<{summary: string, is_cached: boolean}> {
    const response = await apiClient.post<{summary: string, is_cached: boolean}>(`/novels/${novelName}/${fileHash}/analyze/group-summary`, {
      entity_name: entityName,
      chapter_start: start,
      chapter_end: end,
      force: force
    });
    return response.data;
  },

  async fetchRelationshipStages(novelName: string, fileHash: string, source: string, target: string): Promise<RelationshipStage[]> {
    const response = await apiClient.get<RelationshipStage[]>(`/novels/${novelName}/${fileHash}/relationship/stages`, {
      params: { source, target }
    });
    return response.data;
  },

  async analyzeRelationshipStage(novelName: string, fileHash: string, source: string, target: string, start: number, end: number, force: boolean = false): Promise<RelationshipStage> {
    const response = await apiClient.post<RelationshipStage>(`/novels/${novelName}/${fileHash}/analyze/relationship-stage`, {
      source_entity: source,
      target_entity: target,
      chapter_start: start,
      chapter_end: end,
      force: force
    });
    return response.data;
  },

  async fetchAllRelationshipStages(novelName: string, fileHash: string): Promise<RelationshipStageLabel[]> {
    const response = await apiClient.get<RelationshipStageLabel[]>(`/novels/${novelName}/${fileHash}/relationship/all_stages`);
    return response.data;
  },

  async fetchSegments(novelName: string, fileHash: string): Promise<PlotSegment[]> {
    const response = await apiClient.get<PlotSegment[]>(`/novels/${novelName}/${fileHash}/segments`);
    return response.data;
  },

  async generateSegments(novelName: string, fileHash: string): Promise<PlotSegment[]> {
    const response = await apiClient.post<PlotSegment[]>(`/novels/${novelName}/${fileHash}/segments/generate`);
    return response.data;
  },

  async fetchArcs(novelName: string, fileHash: string): Promise<PlotArc[]> {
    const response = await apiClient.get<PlotArc[]>(`/novels/${novelName}/${fileHash}/arcs`);
    return response.data;
  },

  async generateArcs(novelName: string, fileHash: string): Promise<PlotArc[]> {
    const response = await apiClient.post<PlotArc[]>(`/novels/${novelName}/${fileHash}/arcs/generate`);
    return response.data;
  }
};
