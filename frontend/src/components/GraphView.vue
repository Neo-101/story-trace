<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted, computed, shallowRef } from 'vue';
import { Network, DataSet } from "vis-network/standalone";
import type { Entity, TimelineEvent, RelationshipTimelineEvent, EdgeEvent } from '@/types';
import { API } from '@/api/client';
import EntityChronicleDrawer from './EntityChronicleDrawer.vue';
import RelationshipEvolutionDrawer from './RelationshipEvolutionDrawer.vue';
import BatchAnalysisDialog from './BatchAnalysisDialog.vue';
import EntityDetailContainer from './Entity/EntityDetailContainer.vue';
import { useNovelStore } from '@/stores/novel';
import { useJobStore } from '@/stores/jobStore';
import ConceptEvolutionCard from './Entity/ConceptEvolutionCard.vue';
import { RELATIONSHIP_LEXICON } from '@/utils/relationshipLexicon';

const store = useNovelStore();
const jobStore = useJobStore();

const container = ref<HTMLElement | null>(null);
const network = shallowRef<Network | null>(null);

// Batch Analysis State
const isBatchDialogOpen = ref(false);
const visibleEdgesForBatch = ref<any[]>([]);

const openBatchDialog = () => {
  if (!store.currentNovel || !store.graphData) return;
  
  // Create a map of node types for quick lookup
  const nodeTypeMap = new Map<string, string>();
  store.graphData.nodes.forEach(node => {
      nodeTypeMap.set(node.name, node.type);
  });

  // Get all currently visible edges from the DataSet and inject types
  const edges = edgesDataSet.get();
  visibleEdgesForBatch.value = edges.map(edge => ({
      ...edge,
      sourceType: nodeTypeMap.get(edge.from) || 'Unknown',
      targetType: nodeTypeMap.get(edge.to) || 'Unknown'
  }));

  isBatchDialogOpen.value = true;
};

// State for filtering
const minWeight = ref(1);
const selectedTypes = ref<string[]>(['Person', 'Location', 'Organization', 'Event', 'Object', 'Concept']);
const availableTypes = ['Person', 'Location', 'Organization', 'Event', 'Object', 'Concept'];

// State for Timeline
const timelineIndex = ref(0);
const maxTimelineIndex = computed(() => (store.chapters.length > 0 ? store.chapters.length - 1 : 0));
const graphMode = ref<'cumulative' | 'focus'>('cumulative');

// Chronicle State
const isChronicleOpen = ref(false);
const chronicleEvents = ref<TimelineEvent[]>([]);
const isChronicleLoading = ref(false);
const selectedEntity = ref<Entity | null>(null);
const hoveredNodeId = ref<string | null>(null);
const hoveredEdgeId = ref<string | null>(null);

// Relationship Arc State
const selectedNodes = ref<Entity[]>([]);
const isRelationshipDrawerOpen = ref(false);
const relationshipEvents = ref<RelationshipTimelineEvent[]>([]);
const isRelationshipLoading = ref(false);

// Stats
const stats = computed(() => {
    if (!store.graphData) return { nodes: 0, edges: 0 };
    return {
        nodes: nodesDataSet.length,
        edges: edgesDataSet.length
    };
});

// Vis.js DataSets
const nodesDataSet = new DataSet<any>();
const edgesDataSet = new DataSet<any>();

const debugMapSize = ref(0);
const lastError = ref<string>("");
const lastAppliedPhysicsMode = ref<string>("");

const typeColors: Record<string, string> = {
  'Person': '#fbbf24', // amber-400
  'Location': '#60a5fa', // blue-400
  'Organization': '#a78bfa', // purple-400
  'Event': '#f87171', // red-400
  'Object': '#34d399', // emerald-400
  'Concept': '#f472b6', // pink-400
  'Other': '#9ca3af'   // gray-400
};

const typeShapes: Record<string, string> = {
  'Person': 'dot',
  'Location': 'triangle',
  'Organization': 'square',
  'Event': 'star',
  'Object': 'diamond',
  'Concept': 'hexagon',
  'Other': 'dot'
};

const typeLabels: Record<string, string> = {
  'Person': '人物',
  'Location': '地点',
  'Organization': '组织',
  'Event': '事件',
  'Object': '物品',
  'Concept': '概念',
  'Other': '其他'
};

// --- Async Analysis Logic ---

const handleAnalyzeRelationship = async () => {
    if (selectedNodes.value.length !== 2 || !store.currentNovel || !store.currentRun) return;
    
    // 1. Check Threshold (Warning)
    // We need to check if they have enough interactions.
    // We can use the graph data for this.
    // Find the edge between them
    const n1 = selectedNodes.value[0].name;
    const n2 = selectedNodes.value[1].name;
    
    // This logic is a bit naive because we don't have the edge object readily available in `selectedNodes`
    // But we can find it in store.graphData.edges
    // Or we can just let the backend handle it?
    // The design spec said "Frontend checks edge.weight".
    // Let's find the edge.
    const edge = store.graphData?.edges.find(e => 
        (e.source === n1 && e.target === n2) || (e.source === n2 && e.target === n1)
    );
    
    const weight = edge ? edge.weight : 0;
    const coOccurrence = edge?.timeline?.length || 0; // Approximate co-occurrence by timeline events
    
    if (weight < 3 && coOccurrence < 3) {
        if (!confirm(`这两位角色的互动较少 (权重 ${weight}, 事件 ${coOccurrence})。\n深度分析可能产生幻觉或内容稀疏。\n是否继续？`)) {
            return;
        }
    }
    
    // 2. Submit Job
    try {
        const hash = store.currentNovel.hashes[0];
        // If force is true, we might want to delete cache first?
        // Actually, the backend job runner doesn't auto-delete unless we tell it to, or we handle it here.
        // But for "Analyze", we usually mean "Compute if missing".
        // If the user wants to RE-analyze, they should probably clear cache.
        
        await jobStore.submitRelationshipJob({
            novel_name: store.currentNovel.name,
            file_hash: hash,
            source: n1,
            target: n2,
            force: true
        });
        
        // Deselect or just notify?
        // The JobStatusWidget will appear.
    } catch (e) {
        alert("Failed to start analysis: " + e);
    }
};

const handleClearCache = async () => {
    if (selectedNodes.value.length !== 2 || !store.currentNovel) return;
    
    const n1 = selectedNodes.value[0].name;
    const n2 = selectedNodes.value[1].name;
    
    if (!confirm(`确定要清除 "${n1} & ${n2}" 的分析缓存吗？\n清除后需要重新运行 AI 分析。`)) return;
    
    try {
        const hash = store.currentNovel.hashes[0];
        await API.deleteRelationshipAnalysis(
            store.currentNovel.name, 
            hash, 
            n1, 
            n2
        );
        alert("缓存已清除，请重新点击 Analyze 进行分析。");
        // Close drawer if open
        isRelationshipDrawerOpen.value = false;
        relationshipEvents.value = [];
    } catch (e) {
        alert("清除缓存失败: " + e);
    }
};

const openRelationshipDrawer = async () => {
    if (selectedNodes.value.length !== 2 || !store.currentNovel || !store.currentRun) return;
    
    isRelationshipDrawerOpen.value = true;
    isRelationshipLoading.value = true;
    
    try {
        const hash = store.currentNovel.hashes[0];
        relationshipEvents.value = await API.fetchRelationshipTimeline(
            store.currentNovel.name,
            hash,
            store.currentRun.timestamp,
            selectedNodes.value[0].name,
            selectedNodes.value[1].name
        );
    } catch (e) {
        console.error("Failed to fetch relationship timeline:", e);
    } finally {
        isRelationshipLoading.value = false;
    }
};

// Listen for global event to open drawer after analysis
onMounted(() => {
    window.addEventListener('open-relationship-result', handleAnalysisResult as EventListener);
});

onUnmounted(() => {
    window.removeEventListener('open-relationship-result', handleAnalysisResult as EventListener);
});

const handleAnalysisResult = (e: CustomEvent) => {
    const result = e.detail;
    // result contains { pair_id: "A_B", ... }
    // We need to parse pair_id to find source/target names?
    // Or simpler: Just check if the currently selected nodes match the result?
    // If user changed selection, we might not want to open drawer blindly.
    // But for better UX, we should probably parse the pair_id and set selectedNodes.
    
    // For now, let's just trigger the drawer refresh if the selected nodes match.
    // Or if the user clicks "View Result", we assume they want to see THAT result.
    // So we should ideally open the drawer for the entities involved in the job.
    // The job result has `pair_id`.
    
    // Let's assume we just open the drawer for the current selection for now
    // as that's the most common flow (User waits).
    if (selectedNodes.value.length === 2) {
         openRelationshipDrawer();
    }
};

const openChronicle = async () => {
    if (!selectedEntity.value || !store.currentNovel || !store.currentRun) return;
    
    isChronicleOpen.value = true;
    isChronicleLoading.value = true;
    
    try {
        const hash = store.currentNovel.hashes[0];
        chronicleEvents.value = await API.fetchEntityTimeline(
            store.currentNovel.name,
            hash,
            store.currentRun.timestamp,
            selectedEntity.value.name
        );
    } catch (e) {
        console.error("Failed to fetch chronicle:", e);
    } finally {
        isChronicleLoading.value = false;
    }
};

const handleChronicleJump = async (chapterId: string) => {
    store.selectedChapterId = chapterId;
    await store.loadChapterDetail(chapterId);
    store.viewMode = 'reader'; // Switch to reader mode directly
    isChronicleOpen.value = false;
    isRelationshipDrawerOpen.value = false;
};

// --- Graph Logic ---

const initGraph = () => {
  if (!container.value) return;

  const data = {
    nodes: nodesDataSet,
    edges: edgesDataSet
  };

  const options = {
    nodes: {
      shape: 'dot',
      font: {
        size: 14,
        color: '#374151' // gray-700
      },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      width: 1,
      color: { color: '#d1d5db', highlight: '#6366f1' }, // gray-300, indigo-500
      smooth: {
        type: 'continuous',
        enabled: true,
        roundness: 0.5
      },
      arrows: {
          to: { enabled: false } // undirected by default
      }
    },
    physics: {
      stabilization: {
          enabled: true,
          iterations: 100
      },
      barnesHut: {
        gravitationalConstant: -30000,
        springLength: 200,
        springConstant: 0.04,
        damping: 0.09,
        avoidOverlap: 0.5 // Prevent node overlap
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      hideEdgesOnDrag: true,
      multiselect: true
    }
  };

  network.value = new Network(container.value, data, options);

  // Event listeners
    network.value.on("click", (params) => {
      const selectedIds = params.nodes;
      
      // Case 1: Clicked empty space
      if (selectedIds.length === 0) {
          selectedEntity.value = null;
          selectedNodes.value = [];
          network.value?.fit({ 
              animation: { duration: 500, easingFunction: 'easeInOutQuad' } 
          });
          updateGraphData();
          return;
      }

      // Case 2: Multiselect (>= 2 nodes)
      if (selectedIds.length >= 2) {
          selectedEntity.value = null;
          const entities = selectedIds
            .map((id: string) => store.graphData?.nodes.find(n => n.name === id))
            .filter((n: Entity | undefined): n is Entity => !!n);
            
          selectedNodes.value = entities;
          
          // Fit view to pair
          if (entities.length === 2) {
              network.value?.fit({
                  nodes: [entities[0].name, entities[1].name],
                  animation: true
              });
          }
          updateGraphData();
          return;
      }

      // Case 3: Single Node Click (length === 1)
      const clickedNodeId = selectedIds[0];
      
      // If clicking the ALREADY selected single entity -> Deselect (Toggle off)
      if (selectedEntity.value && selectedEntity.value.name === clickedNodeId) {
          selectedEntity.value = null;
          selectedNodes.value = [];
          network.value?.unselectAll();
          network.value?.fit({ 
              animation: { duration: 500, easingFunction: 'easeInOutQuad' } 
          });
      } 
      // If clicking a NEW node (or switching from pair to single)
      else {
          const entity = store.graphData?.nodes.find(n => n.name === clickedNodeId);
          if (entity) {
              selectedEntity.value = entity;
              selectedNodes.value = []; // Clear pair selection
              
              network.value?.focus(clickedNodeId, {
                  scale: 1.2,
                  animation: { duration: 500, easingFunction: 'easeInOutQuad' }
              });
          }
      }
      
      updateGraphData();
    });

    // Re-enable hover listeners for dynamic labels and highlighting
    network.value.on("hoverNode", (params) => {
        hoveredNodeId.value = params.node;
        updateGraphData();
    });

    network.value.on("blurNode", (params) => {
        hoveredNodeId.value = null;
        updateGraphData();
    });
    
    // Add hover edge listeners
    network.value.on("hoverEdge", (params) => {
        // We set edge ID as `source__target` (sorted) in updateGraphData.
        // So params.edge is this ID.
        // We can check which nodes it connects.
        // But we just need to know "an edge is hovered".
        // Actually, we need to know WHICH edge to highlight.
        // Let's store hoveredEdgeId.
        if (params.edge) {
            hoveredEdgeId.value = params.edge;
            updateGraphData();
        }
    });

    network.value.on("blurEdge", (params) => {
        hoveredEdgeId.value = null;
        updateGraphData();
    });


    // Initial update if data is already available
  if (store.graphData) {
      updateGraphData();
  }
};

const updateGraphData = () => {
    if (!store.graphData) return;

    // 1. Filter Nodes
    const activeNodes = store.graphData.nodes.filter(node => {
        // Type filter
        if (!selectedTypes.value.includes(node.type)) return false;
        
        // Timeline filter: Node must appear in chapters <= timelineIndex
        if (store.chapters.length === 0) return true;

        // Use strict ID matching
        const hasAppeared = node.chapter_ids?.some(id => {
            const chIdStr = String(id);
            const chIndex = store.chapters.findIndex(c => String(c.id) === chIdStr);
            return chIndex !== -1 && chIndex <= timelineIndex.value;
        });

        return hasAppeared ?? false;
    });

    // 2. Filter Edges
    const currentChapter = store.chapters[timelineIndex.value];
    if (!currentChapter) return;
    
    // Ensure strict string comparison
    const currentChapterId = String(currentChapter.id); 
    
    const activeEdges: any[] = [];
    const nodeWeights: Record<string, number> = {};

    // Create a set of active node IDs for O(1) lookup
    const activeNodeIds = new Set(activeNodes.map(n => n.name));

    // Deduplication Map: Key -> Edge Object
    const uniqueEdges = new Map<string, any>();

    try {
        // Optimization: Create map for O(1) chapter index lookup
        const chapterIndexMap = new Map<string, number>();
        store.chapters.forEach((c, idx) => {
            chapterIndexMap.set(String(c.id), idx);
        });
        debugMapSize.value = chapterIndexMap.size;
        
        // --- Dynamic Label Helper ---
        const calculateLexiconLabel = (edgeTimeline: any[]): string | undefined => {
             if (!edgeTimeline || edgeTimeline.length === 0) return undefined;

             const scores: Record<string, number> = {};
             const DECAY_FACTOR = 0.05; // Tunable: Higher means faster decay (more focus on recent events). 0.05 keeps history longer.
             const currentChIndex = timelineIndex.value;

             edgeTimeline.forEach(event => {
                 const evtChId = String(event.chapter_id);
                 const evtChIndex = chapterIndexMap.get(evtChId);
                 
                 // Skip future events
                 if (evtChIndex === undefined || evtChIndex > currentChIndex) return;

                 // Calculate Decay: 1.0 at current chapter, decreases as we go back
                 const timeDiff = currentChIndex - evtChIndex;
                 const decay = 1.0 / (1.0 + DECAY_FACTOR * timeDiff);

                 // Get Text
                 const text = (event.relation || event.description || "").toLowerCase();
                 if (!text) return;

                 // Match Keywords
                 for (const [type, data] of Object.entries(RELATIONSHIP_LEXICON)) {
                     // Check if any keyword matches
                     for (const keyword of data.keywords) {
                         if (text.includes(keyword)) {
                             // Use absolute score for label selection (strength of evidence)
                             scores[type] = (scores[type] || 0) + (Math.abs(data.score) * decay);
                             break; // Count once per type per event
                         }
                     }
                 }
             });

             // Find max score
             let maxScore = 0;
             let bestLabel: string | undefined = undefined;

             for (const [type, score] of Object.entries(scores)) {
                 if (score > maxScore) {
                     maxScore = score;
                     bestLabel = type;
                 }
             }
             
             // Return the Chinese label from Lexicon
             return bestLabel ? RELATIONSHIP_LEXICON[bestLabel].label : undefined;
        };

        const getDynamicLabel = (source: string, target: string, edgeTimeline: any[]): string | undefined => {
            // Priority A: Analyzed Stages (LLM)
            // Check store.relationshipStageIndex
            if (store.relationshipStageIndex) {
                const currentCh = store.chapters[timelineIndex.value];
                // Fallback to timelineIndex + 1 if index not available (should be now)
                const currentChNum = currentCh ? (currentCh.index || timelineIndex.value + 1) : (timelineIndex.value + 1);

                const stage = store.relationshipStageIndex.find(s => 
                    ((s.source_entity === source && s.target_entity === target) || 
                     (s.source_entity === target && s.target_entity === source)) &&
                    s.start_chapter <= currentChNum && s.end_chapter >= currentChNum
                );
                if (stage) return stage.stage_label;
            }

            // Priority B: Lexicon Scoring (Rule-based)
            const lexiconLabel = calculateLexiconLabel(edgeTimeline);
            if (lexiconLabel) return lexiconLabel;

            // Priority C: Raw Interactions (Fallback)
            // Handled by caller if this returns undefined
            return undefined; 
        };

        // --- Clustering Helper ---
        // Collect neighbors by relationship label to create clustering forces
        const neighborGroups = new Map<string, string[]>(); // Label -> NodeID[]
        const focusNodeId = selectedEntity.value?.name || (selectedNodes.value.length === 1 ? selectedNodes.value[0].name : null);

        store.graphData.edges.forEach((edge) => {
            if (!edge.timeline) return;

            // Strict consistency check: Both source and target must be visible nodes
            if (!activeNodeIds.has(edge.source) || !activeNodeIds.has(edge.target)) {
                return;
            }

            // --- Deduplication Logic ---
            // Create a canonical key: sorted pair of names
            const [u, v] = [edge.source, edge.target].sort();
            const edgeKey = `${u}__${v}`;
            
            // If we already processed this pair, merge data (or skip if data is identical)
            // Assuming `store.graphData.edges` might have duplicates.
            // Ideally, backend should merge. But here we do it defensively.
            // Since we need to accumulate `weight` and `timeline`, let's check existing.
            let existingEdge = uniqueEdges.get(edgeKey);
            if (!existingEdge) {
                existingEdge = {
                    source: u,
                    target: v,
                    weight: 0, // Will be summed below
                    timeline: [] // Will be merged
                };
                uniqueEdges.set(edgeKey, existingEdge);
            }
            
            // Merge timeline events
            // We clone the timeline to avoid mutating the original store object in a way that persists weirdly
            existingEdge.timeline.push(...edge.timeline);
        });

        // Now iterate unique edges
        uniqueEdges.forEach((edge, edgeKey) => {
            // --- Deduplicate & Sort Timeline ---
            // 1. Deduplicate based on unique signature (Chapter + Description)
            const seenEvents = new Set<string>();
            edge.timeline = edge.timeline.filter((e: any) => {
                const sig = `${e.chapter_id}|${e.description || ''}|${e.relation || ''}`;
                if (seenEvents.has(sig)) return false;
                seenEvents.add(sig);
                return true;
            });

            // 2. Sort by Chapter Index (Ascending)
            edge.timeline.sort((a: any, b: any) => {
                const idxA = chapterIndexMap.get(String(a.chapter_id)) ?? -1;
                const idxB = chapterIndexMap.get(String(b.chapter_id)) ?? -1;
                return idxA - idxB;
            });

            let weight = 0;
            let label = '';
            let isVisible = false;

            // --- Highlighting Logic ---
            // If any node is selected, we dim everything else unless connected
            const hasSelection = !!selectedEntity.value || selectedNodes.value.length > 0;
            
            // Check if this edge is connected to selection
            const isConnectedToSelection = 
                (selectedEntity.value && (edge.source === selectedEntity.value.name || edge.target === selectedEntity.value.name)) ||
                (selectedNodes.value.length > 0 && (selectedNodes.value.some(n => n.name === edge.source || n.name === edge.target)));

            // Determine if this specific edge is being hovered (or its endpoint)
            // Requirement: "Select red node -> hover connected edge/node -> Highlight THAT edge/node"
            let isHoveredConnection = false;
            if (hasSelection && isConnectedToSelection) {
                if (hoveredNodeId.value) {
                    // If hovering a node, is it one of the endpoints of this edge?
                    // And is it NOT the selected node itself? (Highlight the connection to the neighbor)
                    if (hoveredNodeId.value === edge.source || hoveredNodeId.value === edge.target) {
                        isHoveredConnection = true;
                    }
                }
                
                // Also check if the edge itself is hovered
                if (hoveredEdgeId.value && hoveredEdgeId.value === edgeKey) {
                    isHoveredConnection = true;
                }
            }

            // Show label only if connected to selection (User request: only on click)
            const showDynamicLabel = isConnectedToSelection;

            let color = undefined;
            let opacity = 1.0;
            let width = 1;
            
            if (hasSelection) {
                if (isConnectedToSelection) {
                    if (hoveredNodeId.value || hoveredEdgeId.value) {
                         // Hovering something in selection mode
                         if (isHoveredConnection) {
                             // This is the specific connection we are looking at
                             color = { color: '#6366f1', opacity: 1.0, highlight: '#6366f1' }; // Bright Indigo
                             opacity = 1.0;
                             width = 3; // Thicker
                         } else {
                             // Connected, but not the one being hovered -> Dim slightly
                             color = { color: '#a5b4fc', opacity: 0.3, highlight: '#a5b4fc' }; // Indigo-200, dim
                             opacity = 0.3;
                             width = 1;
                         }
                    } else {
                        // Not hovering anything, show all connected normally
                        color = { color: '#6366f1', opacity: 1.0, highlight: '#6366f1' }; // Indigo
                        opacity = 1.0;
                        width = 2;
                    }
                } else {
                    // Unrelated -> Transparent
                    color = { color: '#e5e7eb', opacity: 0.05, highlight: '#e5e7eb' }; // Almost invisible
                    opacity = 0.05;
                }
            } else {
                // Default state
                color = { color: '#d1d5db', highlight: '#6366f1' };
                width = 1;
            }

            if (graphMode.value === 'cumulative') {
                // Sum weights of all events where chapter_index <= timelineIndex
                let lastRelation = undefined;

                for (const event of edge.timeline) {
                    const evtChId = String(event.chapter_id);
                    const chIndex = chapterIndexMap.get(evtChId);
                    
                    if (chIndex !== undefined && chIndex <= timelineIndex.value) {
                        weight += (event.weight || 1);
                        if (event.relation) lastRelation = event.relation;
                    }
                }
                isVisible = weight >= minWeight.value;
                
                if (showDynamicLabel && isVisible) {
                    // Try Priority A & B
                    const stageLabel = getDynamicLabel(edge.source, edge.target, edge.timeline);
                    if (stageLabel) {
                        label = stageLabel;
                    } else if (lastRelation) {
                        // Priority C
                        label = lastRelation;
                    }
                }

            } else { // Focus Mode
                // Only events matching current chapter ID
                for (const event of edge.timeline) {
                    const evtChId = String(event.chapter_id);
                    if (evtChId === currentChapterId) {
                        weight += (event.weight || 1);
                        label = event.relation || ''; // Always show relation in Focus mode if present? Or follow same rule?
                        // Design spec says "Dynamic Label on Hover".
                        // But Focus mode naturally shows current interaction.
                        // Let's keep existing logic for Focus mode label (it shows relation by default if present)
                        // But maybe we want to enforce the "Dynamic Label" style?
                        // If Focus mode already shows relation, that's fine.
                        // But let's apply the Priority A check even in Focus mode if interaction is generic?
                        // Actually, Focus mode shows EXACTLY what happened in this chapter. 
                        // The Stage Label is a high-level summary.
                        // If we have a specific interaction "Punch", showing "Enemy" stage label might be redundant or helpful context.
                        // Let's stick to existing logic for Focus mode unless hovered?
                        // Let's apply dynamic label if hovered, overriding specific interaction?
                        // No, specific interaction is more precise for Focus mode.
                        // So only apply dynamic label logic to Cumulative mode mainly, or if Focus mode has no relation label.
                    }
                }
                isVisible = weight >= 1; 
                
                // If hovered and no specific label, maybe show stage?
                if (isVisible && showDynamicLabel && !label) {
                     const stageLabel = getDynamicLabel(edge.source, edge.target, edge.timeline);
                     if (stageLabel) label = stageLabel;
                }
            }

            if (isVisible) {
                // If hasSelection and NOT connected, hide it effectively (or keep very faint)
                // Actually Vis.js opacity handling is tricky.
                // Let's filter it out if we want "only target and connected nodes" visible?
                // User said "others become almost transparent".
                
                activeEdges.push({
                    id: edgeKey, // Set ID to allow hover detection
                    from: edge.source,
                    to: edge.target,
                    value: weight,
                    label: showDynamicLabel ? (label || undefined) : undefined, // Hide label if not focused
                    font: { 
                        align: 'middle', 
                        size: 12, 
                        strokeWidth: 0, // No stroke, use background
                        color: '#374151',
                        background: 'rgba(255, 255, 255, 0.9)' // White background for readability
                    },
                    color: color,
                    width: width
                });
                
                // Accumulate node weights (only if visible?)
                // If we want layout to remain stable, we should include all edges but make them invisible?
                // But user complained "graph unstable/shakes".
                // This usually happens when edges appear/disappear.
                // If we just change color/opacity, layout should be stable.
                nodeWeights[edge.source] = (nodeWeights[edge.source] || 0) + weight;
                nodeWeights[edge.target] = (nodeWeights[edge.target] || 0) + weight;

                // --- Clustering Logic: Collect neighbors ---
                if (focusNodeId) {
                    // Only cluster if connected to focus node
                    if (edge.source === focusNodeId || edge.target === focusNodeId) {
                        const neighborId = edge.source === focusNodeId ? edge.target : edge.source;
                        // Use the displayed label for grouping. If hidden or empty, group as 'Unknown'
                        const groupLabel = (showDynamicLabel && label) ? label : 'Unknown';
                        
                        const neighbors = neighborGroups.get(groupLabel) || [];
                        neighbors.push(neighborId);
                        neighborGroups.set(groupLabel, neighbors);
                    }
                }
            }
        });

        // Add Invisible Clustering Edges (Spatial Grouping)
        if (focusNodeId && neighborGroups.size > 0) {
             neighborGroups.forEach((neighbors, groupLabel) => {
                 // Sort neighbors to form a consistent chain (spatial stability)
                 neighbors.sort();
                 
                 // Connect neighbors in a chain: A -> B -> C -> D
                 // This pulls them together spatially
                 for (let i = 0; i < neighbors.length - 1; i++) {
                     const u = neighbors[i];
                     const v = neighbors[i+1];
                     
                     // Ensure unique ID for clustering edge
                     const clusterEdgeId = `cluster_${focusNodeId}_${groupLabel}_${i}`;
                     
                     activeEdges.push({
                         id: clusterEdgeId,
                         from: u,
                         to: v,
                         color: { opacity: 0 }, // Invisible
                         width: 0,
                         physics: true, // Enable physics to pull nodes
                         smooth: { type: 'continuous', roundness: 0 },
                         length: 50, // Pull them close (shorter than standard spring)
                         value: 1 // Minimal weight
                     });
                 }
             });
        }
        
    } catch (err: any) {
        console.error("Error processing graph edges:", err);
        lastError.value = err.toString();
    }

    // 3. Filter Nodes based on Edges
    const processedNodeIds = new Set<string>();
    
    // Check if we have a selection to determine transparency
    const hasSelection = !!selectedEntity.value || selectedNodes.value.length > 0;

    // Collect connected nodes for highlighting logic
    const connectedNodeIds = new Set<string>();
    if (hasSelection) {
        activeEdges.forEach(e => {
            const isSourceSelected = (selectedEntity.value?.name === e.from) || (selectedNodes.value.some(n => n.name === e.from));
            const isTargetSelected = (selectedEntity.value?.name === e.to) || (selectedNodes.value.some(n => n.name === e.to));
            
            if (isSourceSelected) connectedNodeIds.add(e.to);
            if (isTargetSelected) connectedNodeIds.add(e.from);
        });
    }

    const visNodes = activeNodes.map(node => {
        if (processedNodeIds.has(node.name)) return null;
        
        const degree = nodeWeights[node.name] || 0;
        
        // Visibility filters (Focus/Cumulative)
        if (graphMode.value === 'focus' && degree === 0) return null;
        if (graphMode.value === 'cumulative' && degree === 0) return null;

        processedNodeIds.add(node.name);
        
        // Transparency Logic
        let nodeColor = typeColors[node.type] || typeColors['Other'];
        let opacity = 1.0;
        let borderWidth = 2;
        let borderColor = undefined;

        // Hex to RGBA helper
        const hexToRgba = (hex: string, alpha: number) => {
            if (!hex) return `rgba(156, 163, 175, ${alpha})`; // gray-400 fallback
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        };

        if (hasSelection) {
             const isSelected = (selectedEntity.value?.name === node.name) || (selectedNodes.value.some(n => n.name === node.name));
             const isConnected = connectedNodeIds.has(node.name);
             
             if (isSelected) {
                 // Selected Node: Highlight Border Red
                 borderColor = '#ef4444'; // Red-500
                 borderWidth = 4;
                 opacity = 1.0;
             } else if (isConnected) {
                 // Connected Node: Check Hover State
                 if (hoveredNodeId.value || hoveredEdgeId.value) {
                      // If this node is hovered, or if this node is connected to the selected node via the hovered edge?
                      // Currently hoveredNodeId only tracks node hover.
                      // The requirement: "Select Red, Hover Connected Edge/Node -> Highlight That, Dim Others"
                      
                      let isThisNodeHighlighted = false;
                      
                      // 1. Is this node directly hovered?
                      if (hoveredNodeId.value === node.name) {
                          isThisNodeHighlighted = true;
                      }
                      
                      // 2. Is this node part of the hovered edge?
                      if (hoveredEdgeId.value) {
                          const [u, v] = hoveredEdgeId.value.split('__');
                          if (u === node.name || v === node.name) {
                              isThisNodeHighlighted = true;
                          }
                      }

                      if (isThisNodeHighlighted) {
                          // This node is being hovered -> Full Opacity
                          opacity = 1.0;
                      } else {
                          // Another connected node is being hovered -> Dim this one
                          opacity = 0.3;
                      }
                 } else {
                     // No hover -> Full Opacity
                     opacity = 1.0;
                 }
             } else {
                 // Unrelated Node: Transparent
                 opacity = 0.1;
             }
        }
        
        const baseRgba = hexToRgba(nodeColor, opacity);
        const borderRgba = borderColor || baseRgba;

        const finalColor = {
            background: baseRgba,
            border: borderRgba,
            highlight: {
                background: hexToRgba(nodeColor, 1.0),
                border: '#ef4444'
            }
        };

        return {
            id: node.name,
            label: node.name,
            value: Math.log(degree + 1) * 10 + 5,
            color: finalColor,
            borderWidth: borderWidth,
            shape: typeShapes[node.type] || typeShapes['Other'],
            title: node.description,
            font: { color: opacity < 0.5 ? 'rgba(0,0,0,0)' : '#374151' } // Fully hide label if transparent
        };
    }).filter(n => n !== null);

    // Update DataSets with Diffing to prevent physics reset
    const newNodeIds = new Set(visNodes.map(n => n.id));
    const oldNodeIds = nodesDataSet.getIds();
    const nodesToRemove = oldNodeIds.filter(id => !newNodeIds.has(id));
    nodesDataSet.remove(nodesToRemove);
    nodesDataSet.update(visNodes);
    
    const newEdgeIds = new Set(activeEdges.map(e => e.id));
    const oldEdgeIds = edgesDataSet.getIds();
    const edgesToRemove = oldEdgeIds.filter(id => !newEdgeIds.has(id));
    edgesDataSet.remove(edgesToRemove);
    edgesDataSet.update(activeEdges);

    // Update Physics based on Mode & Selection (Only if changed)
    // We need to track the current physics mode to avoid resetting it constantly
    const currentMode = hasSelection ? 'selection' : graphMode.value;
    
    // We store the last applied mode in a ref to compare
    if (lastAppliedPhysicsMode.value !== currentMode) {
        if (network.value) {
            if (hasSelection) {
                 network.value.setOptions({
                    physics: {
                        barnesHut: {
                            gravitationalConstant: -40000, // Stronger repulsion
                            springLength: 300, // Much longer springs to separate nodes
                            springConstant: 0.02 // Softer springs
                        }
                    }
                });
            } else if (graphMode.value === 'focus') {
                 network.value.setOptions({
                    physics: {
                        barnesHut: {
                            gravitationalConstant: -20000, // Stronger repulsion
                            springLength: 200 // Longer springs
                        }
                    }
                });
            } else {
                 network.value.setOptions({
                    physics: {
                        barnesHut: {
                            gravitationalConstant: -10000,
                            springLength: 120
                        }
                    }
                });
            }
        }
        lastAppliedPhysicsMode.value = currentMode;
    }
};

// --- Interactions ---

const toggleType = (type: string) => {
    if (selectedTypes.value.includes(type)) {
        selectedTypes.value = selectedTypes.value.filter(t => t !== type);
    } else {
        selectedTypes.value = [...selectedTypes.value, type]; // Immutable update
    }
};

const prevChapter = () => {
    if (timelineIndex.value > 0) timelineIndex.value--;
};

const nextChapter = () => {
    if (timelineIndex.value < maxTimelineIndex.value) timelineIndex.value++;
};

// Watchers
watch([() => store.graphData, selectedTypes, minWeight, timelineIndex, graphMode, selectedEntity, selectedNodes], () => {
    updateGraphData();
}, { deep: true });

// Lifecycle
onMounted(async () => {
    await store.loadGraphData();
    // Load relationship stage index for dynamic labels
    store.loadRelationshipStageIndex();
    initGraph();
    
    // Keyboard shortcuts
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});

const handleKeydown = (e: KeyboardEvent) => {
    if (store.viewMode !== 'graph') return;
    
    if (e.key === 'ArrowLeft') prevChapter();
    if (e.key === 'ArrowRight') nextChapter();
    if (e.key === 'Escape') {
        selectedEntity.value = null;
        selectedNodes.value = [];
        // No need to call updateGraphData() explicitly as watcher handles it?
        // Actually watcher handles selectedEntity changes.
    }
};

// Computed Display Description
const displayDescription = computed(() => {
    if (!selectedEntity.value) return '';
    
    // Find history entry for current chapter or latest before it
    if (!selectedEntity.value.history) return selectedEntity.value.description;

    const currentChapterId = store.chapters[timelineIndex.value]?.id;
    if (!currentChapterId) return selectedEntity.value.description;

    if (graphMode.value === 'focus') {
        // Exact match
        const entry = selectedEntity.value.history.find(h => h.chapter_id === currentChapterId);
        return entry ? entry.content : "未在本章出现";
    } else {
        // Latest up to current
        // Assuming history is sorted? Or we need to sort.
        // Let's assume history is chronological.
        // We find the last entry where chapter index <= timelineIndex
        // This requires chapter index mapping.
        // Simplified: Just show the main description which is usually the aggregated one.
        return selectedEntity.value.description;
    }
});

</script>

<template>
  <div class="h-full flex relative overflow-hidden">
    <!-- Main Canvas -->
    <div ref="container" class="flex-1 bg-gray-50 outline-none"></div>

    <!-- Controls Overlay -->
    <div class="absolute top-4 left-4 bg-white/90 backdrop-blur p-4 rounded-xl shadow-lg border border-gray-200 w-64 z-10 flex flex-col gap-4">
        <!-- Mode Switch -->
        <div class="flex bg-gray-100 p-1 rounded-lg">
            <button 
                @click="graphMode = 'cumulative'"
                class="flex-1 py-1 text-xs font-bold rounded-md transition-all"
                :class="graphMode === 'cumulative' ? 'bg-white shadow text-indigo-600' : 'text-gray-500'"
            >
                全局累积
            </button>
            <button 
                @click="graphMode = 'focus'"
                class="flex-1 py-1 text-xs font-bold rounded-md transition-all"
                :class="graphMode === 'focus' ? 'bg-white shadow text-indigo-600' : 'text-gray-500'"
            >
                单章专注
            </button>
        </div>

        <!-- Timeline Control -->
        <div class="space-y-2">
            <div class="flex justify-between text-xs font-bold text-gray-500 uppercase">
                <span>Timeline</span>
                <!-- Hide ID, just show chapter index/progress -->
                <span>{{ timelineIndex + 1 }} / {{ maxTimelineIndex + 1 }}</span>
            </div>
            
            <!-- Slider -->

            <input 
                type="range" 
                min="0" 
                :max="maxTimelineIndex" 
                v-model.number="timelineIndex"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            >

            <!-- Navigation Buttons -->
            <div class="flex gap-2">
                <button @click="prevChapter" :disabled="timelineIndex <= 0" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded px-2 py-1 text-xs disabled:opacity-50">
                    &larr; Prev
                </button>
                <button @click="nextChapter" :disabled="timelineIndex >= maxTimelineIndex" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded px-2 py-1 text-xs disabled:opacity-50">
                    Next &rarr;
                </button>
            </div>
            
            <!-- Chapter Jump -->
            <select v-model.number="timelineIndex" class="w-full text-xs border-gray-200 rounded bg-gray-50">
                <option v-for="(chap, idx) in store.chapters" :key="chap.id" :value="idx">
                    {{ idx + 1 }}: {{ chap.title }}
                </option>
            </select>
        </div>

        <hr class="border-gray-100">

        <!-- Type Filters -->
        <div class="space-y-2">
            <span class="text-xs font-bold text-gray-500 uppercase">Filters & Legend</span>
            <div class="flex flex-col gap-1.5">
                <button 
                    v-for="type in availableTypes" 
                    :key="type"
                    @click="toggleType(type)"
                    class="px-2 py-1.5 rounded-lg text-xs font-medium transition-all border flex items-center justify-between group"
                    :class="selectedTypes.includes(type) 
                        ? 'bg-white border-gray-200 shadow-sm hover:border-indigo-300' 
                        : 'bg-gray-50 text-gray-400 border-transparent hover:bg-gray-100'"
                >
                    <div class="flex items-center gap-2">
                         <!-- Legend Icon -->
                        <div 
                            class="w-3 h-3 flex items-center justify-center"
                            :style="{ color: typeColors[type] }"
                        >
                            <!-- Dot -->
                            <div v-if="typeShapes[type] === 'dot'" class="w-2.5 h-2.5 rounded-full bg-current"></div>
                            <!-- Square -->
                            <div v-else-if="typeShapes[type] === 'square'" class="w-2.5 h-2.5 bg-current rounded-[1px]"></div>
                            <!-- Triangle (CSS) -->
                            <div v-else-if="typeShapes[type] === 'triangle'" class="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[9px] border-l-transparent border-r-transparent border-b-current mb-0.5"></div>
                             <!-- Diamond (CSS) -->
                            <div v-else-if="typeShapes[type] === 'diamond'" class="w-2 h-2 bg-current rotate-45"></div>
                            <!-- Star (SVG) -->
                            <svg v-else-if="typeShapes[type] === 'star'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3">
                                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                            </svg>
                             <!-- Hexagon (SVG) -->
                            <svg v-else-if="typeShapes[type] === 'hexagon'" viewBox="0 0 24 24" fill="currentColor" class="w-3 h-3">
                                <path d="M12 2l8.66 5v10L12 22l-8.66-5V7L12 2z"/>
                            </svg>
                        </div>
                        <span :class="selectedTypes.includes(type) ? 'text-gray-700' : 'text-gray-400'">
                            {{ typeLabels[type] || type }}
                        </span>
                    </div>
                    
                    <!-- Checkmark -->
                    <div class="w-4 h-4 rounded-full border flex items-center justify-center transition-colors"
                        :class="selectedTypes.includes(type) ? 'border-indigo-500 bg-indigo-500 text-white' : 'border-gray-300'"
                    >
                        <svg v-if="selectedTypes.includes(type)" xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </button>
            </div>
        </div>

        <!-- Weight Slider -->
        <div class="space-y-1" v-if="graphMode === 'cumulative'">
            <div class="flex justify-between text-xs text-gray-400">
                <span>Min Interactions</span>
                <span>{{ minWeight }}</span>
            </div>
            <input 
                type="range" 
                min="1" 
                max="10" 
                v-model.number="minWeight"
                class="w-full h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-400"
            >
        </div>

        <hr class="border-gray-100" v-if="graphMode === 'cumulative'">

        <!-- Batch Analysis Button -->
        <button 
            v-if="graphMode === 'cumulative'"
            @click="openBatchDialog"
            class="w-full py-2 px-3 bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-50 hover:border-indigo-300 rounded-lg text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-2"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Batch Analyze ({{ stats.edges }})
        </button>
        
        <!-- Stats -->
        <div class="text-[10px] text-gray-400 font-mono text-center pt-2">
            {{ stats.nodes }} Nodes · {{ stats.edges }} Edges
        </div>

        <!-- Debug Info (Temporary) -->
        <div class="text-[10px] text-red-500 font-mono bg-red-50 p-2 rounded border border-red-200 opacity-70 hover:opacity-100">
            <div>Idx: {{ timelineIndex }} / {{ maxTimelineIndex }}</div>
            <div>ChID: {{ store.chapters[timelineIndex]?.id }}</div>
            <div>Mode: {{ graphMode }}</div>
            <div>MapSize: {{ debugMapSize }}</div>
            <div v-if="timelineIndex >= 11">Debug: Ch 12+ Active</div>
        </div>
    </div>

    <!-- Entity Details Panel -->
    <EntityDetailContainer 
        v-if="selectedEntity" 
        :entity="selectedEntity" 
        :description="displayDescription"
        :type-colors="typeColors"
        @close="selectedEntity = null"
    >
        <template #actions>
            <button 
                @click="openChronicle"
                class="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold shadow-sm transition-colors flex items-center justify-center gap-2"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                查看编年史
            </button>
        </template>
        
        <template #modules>
            <!-- 渐进式世界观模块 -->
            <ConceptEvolutionCard 
                :stages="selectedEntity.concept_evolution || []" 
                :entity-name="selectedEntity.name"
                @update="(newStages) => { if (selectedEntity) selectedEntity.concept_evolution = newStages }"
            />
        </template>
    </EntityDetailContainer>

    <!-- Relationship Selection Panel -->
    <div v-if="selectedNodes.length === 2" class="absolute bottom-8 left-1/2 transform -translate-x-1/2 bg-white/95 backdrop-blur shadow-xl rounded-xl p-4 border border-gray-200 z-30 flex items-center gap-4 transition-all animate-in fade-in slide-in-from-bottom-4">
        <div class="flex items-center gap-2">
            <div class="flex -space-x-2">
                <div class="w-8 h-8 rounded-full bg-indigo-100 border-2 border-white flex items-center justify-center text-xs font-bold text-indigo-800">
                    {{ selectedNodes[0].name[0] }}
                </div>
                <div class="w-8 h-8 rounded-full bg-pink-100 border-2 border-white flex items-center justify-center text-xs font-bold text-pink-800">
                    {{ selectedNodes[1].name[0] }}
                </div>
            </div>
            <div class="flex flex-col">
                <span class="text-xs font-medium text-gray-500">Compare</span>
                <span class="text-sm font-bold text-gray-900 leading-none">
                    {{ selectedNodes[0].name }} & {{ selectedNodes[1].name }}
                </span>
            </div>
        </div>
        
        <div class="h-8 w-px bg-gray-200 mx-2"></div>
        
        <button 
            @click="openRelationshipDrawer"
            class="py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors flex items-center gap-2"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            View Arc
        </button>
        
        <button 
            @click="handleAnalyzeRelationship"
            class="py-2 px-4 bg-white hover:bg-gray-50 text-indigo-600 border border-indigo-200 hover:border-indigo-300 text-sm font-medium rounded-lg shadow-sm transition-colors flex items-center gap-2"
            title="AI Analyze"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Analyze
        </button>

        <!-- Clear Cache Button -->
        <button 
            @click="handleClearCache"
            class="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-200"
            title="Clear Analysis Cache"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
        </button>
        
        <button 
            @click="selectedNodes = []; network?.unselectAll()"
            class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    </div>

    <!-- Relationship Drawer -->
    <RelationshipEvolutionDrawer 
        v-if="selectedNodes.length === 2"
        :is-open="isRelationshipDrawerOpen"
        :source-entity="selectedNodes[0]"
        :target-entity="selectedNodes[1]"
        :events="relationshipEvents"
        :is-loading="isRelationshipLoading"
        @close="isRelationshipDrawerOpen = false"
        @jump-to-chapter="handleChronicleJump"
    />

    <!-- Chronicle Drawer -->
    <EntityChronicleDrawer 
        :is-open="isChronicleOpen"
        :entity-name="selectedEntity?.name || ''"
        :events="chronicleEvents"
        :is-loading="isChronicleLoading"
        @close="isChronicleOpen = false"
        @jump-to-chapter="handleChronicleJump"
    />

    <!-- Batch Analysis Dialog -->
    <BatchAnalysisDialog
        :is-open="isBatchDialogOpen"
        :visible-edges="visibleEdgesForBatch"
        @close="isBatchDialogOpen = false"
    />
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}
</style>
