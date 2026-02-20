export interface Novel {
  name: string;
  hashes: string[];
}

export interface Run {
  timestamp: string;
  file_hash: string;
}

export interface Chapter {
  id: string;
  title: string;
  headline: string | null;
  summary_sentences: SummarySentence[];
  content?: string;
  entities?: Entity[];
}

export interface SummarySentence {
  summary_text: string;
  source_spans: SourceSpan[];
}

export interface SourceSpan {
  start_index: number;
  end_index: number;
  text: string;
}

export interface Entity {
  name: string;
  type: string;
  description: string;
  count?: number;
  chapter_ids?: string[];
}

export interface GraphData {
  nodes: Entity[];
  edges: Relationship[];
}

export interface Relationship {
  source: string;
  target: string;
  weight: number;
  timeline?: EdgeEvent[];
}

export interface GraphNode {
  // Deprecated, use Entity
  id: string;
  label: string;
  group: string;
  value: number;
}

export interface GraphEdge {
  // Deprecated, use Relationship
  from: string;
  to: string;
  value: number;
}

export interface EdgeEvent {
  chapter_id: string;
  weight: number;
}
