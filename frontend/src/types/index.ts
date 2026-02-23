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
  history?: { chapter_id: string; content: string }[];
  count?: number;
  chapter_ids?: string[];
  concept_evolution?: ConceptStage[];
  clue_lifecycle?: ClueState[];
  faction_info?: FactionInfo;
}

export interface ConceptStage {
  stage_name: string;
  description: string;
  revealed_by: string[];
}

export interface ClueState {
  state: string;
  chapter_index: number;
  context: string;
}

export interface TimelineEvent {
  chapter_id: string;
  chapter_index: number;
  chapter_title: string;
  content: string[];
  gap_before: number;
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
  weight?: number;
  relation?: string;
  description?: string;
  order?: number;
}

export interface RelationshipInteraction {
  direction: 'forward' | 'backward';
  relation: string;
  description: string;
  confidence: number;
}

export interface NarrativeState {
  trust_level: number;
  romance_level: number;
  conflict_level: number;
  dominant_archetype: string;
  current_stage: string;
  summary_so_far: string;
  unresolved_threads: string[];
}

export interface RelationshipTimelineEvent {
  chapter_id: string;
  chapter_index: number;
  chapter_title: string;
  interactions: RelationshipInteraction[];
  narrative_state?: NarrativeState;
}

export interface FactionInfo {
  faction_name: string;
  territory: string[];
  enemies: string[];
  allies: string[];
}

export interface ExtendedEntity extends Entity {
  faction_info?: FactionInfo;
}
