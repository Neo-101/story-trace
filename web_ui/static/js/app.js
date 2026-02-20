// Main Application Logic
// Orchestrates API, Graph, and UI state

import { API } from './api.js';
import { GraphController } from './graph.js';

const { createApp, ref, computed, nextTick, watch } = window.Vue;

const app = createApp({
    setup() {
        // --- State ---
        const novels = ref([]);
        const runs = ref([]);
        const chapters = ref([]);
        
        const selectedNovel = ref(null);
        const selectedRun = ref(null);
        const selectedChapterId = ref(null);
        const currentChapter = ref(null);
        
        const loading = ref(false);
        const activeSummaryIndex = ref(-1);
        const viewMode = ref('overview'); // 'overview', 'focus', 'encyclopedia', 'graph'
        const entityScope = ref('chapter'); // 'chapter', 'book'
        const globalEntities = ref([]);
        
        // Graph State
        const graphData = ref({ nodes: [], edges: [] });
        const graphLoading = ref(false);
        const timelineIndex = ref(0);
        const graphFilterMode = ref('cumulative'); // 'cumulative', 'focus'
        const graphStats = ref({ nodes: 0, edges: 0 });
        
        // Advanced Graph Filters
        const minGraphWeight = ref(1);
        const availableEntityTypes = ['Person', 'Location', 'Organization', 'Item', 'Concept', 'Other'];
        const visibleEntityTypes = ref([...availableEntityTypes]);

        // Graph Controller Instance
        const graphController = new GraphController('graph-container', {
            onStatsUpdate: (stats) => {
                graphStats.value = stats;
            }
        });

        // --- Computed ---
        const groupedEntities = computed(() => {
            let sourceList = [];
            if (entityScope.value === 'chapter') {
                if (!currentChapter.value || !currentChapter.value.entities) return {};
                sourceList = currentChapter.value.entities;
            } else {
                sourceList = globalEntities.value;
            }
            
            const groups = {};
            sourceList.forEach(ent => {
                const typeName = ent.type || 'Other';
                if (!groups[typeName]) groups[typeName] = [];
                groups[typeName].push(ent);
            });
            return groups;
        });

        const currentTimelineChapter = computed(() => {
            if (chapters.value.length === 0) return null;
            return chapters.value[timelineIndex.value];
        });

        const timelineLabels = computed(() => {
            const count = chapters.value.length;
            if (count === 0) return [];
            if (count <= 5) return chapters.value.map(c => ({ text: c.title }));
            const mid = Math.floor(count / 2);
            return [
                { text: chapters.value[0].title },
                { text: chapters.value[mid].title },
                { text: chapters.value[count - 1].title }
            ];
        });

        const highlightedContent = computed(() => {
            if (!currentChapter.value) return '';
            let content = currentChapter.value.content;
            if (!content) return '';

            const escapeHtml = (unsafe) => {
                return unsafe
                        .replace(/&/g, "&amp;")
                        .replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;")
                        .replace(/"/g, "&quot;")
                        .replace(/'/g, "&#039;");
            }

            const summaries = currentChapter.value.summary_sentences || [];
            const markers = [];
            
            summaries.forEach((sent, sIdx) => {
                if (sent.source_spans) {
                    sent.source_spans.forEach(span => {
                        markers.push({ pos: span.start_index, type: 'start', id: sIdx });
                        markers.push({ pos: span.end_index, type: 'end', id: sIdx });
                    });
                }
            });

            markers.sort((a, b) => a.pos - b.pos);

            let result = '';
            let lastPos = 0;
            
            for (let i = 0; i < markers.length; i++) {
                const m = markers[i];
                if (m.pos > lastPos) {
                    result += escapeHtml(content.substring(lastPos, m.pos));
                }
                
                if (m.type === 'start') {
                    result += `<span id="span-${m.id}" class="highlight-span" data-summary-idx="${m.id}">`;
                } else {
                    result += `</span>`;
                }
                lastPos = m.pos;
            }
            
            if (lastPos < content.length) {
                result += escapeHtml(content.substring(lastPos));
            }

            return result;
        });

        // --- Methods ---
        
        // Initial Load
        API.fetchNovels().then(data => novels.value = data);

        const fetchRuns = async () => {
            if (!selectedNovel.value) return;
            loading.value = true;
            selectedRun.value = null;
            selectedChapterId.value = null;
            currentChapter.value = null;
            try {
                const hash = selectedNovel.value.hashes[0];
                runs.value = await API.fetchRuns(selectedNovel.value.name, hash);
                if (runs.value.length > 0) {
                    selectedRun.value = runs.value[0];
                    // Ensure we start in overview mode
                    viewMode.value = 'overview';
                    // Reset selected chapter to trigger scroll when selected again
                    selectedChapterId.value = null;
                    await fetchChapters();
                }
            } finally {
                loading.value = false;
            }
        };

        const fetchChapters = async () => {
            if (!selectedRun.value) return;
            loading.value = true;
            try {
                const hash = selectedNovel.value.hashes[0];
                chapters.value = await API.fetchChapters(selectedNovel.value.name, hash, selectedRun.value.timestamp);
            } finally {
                loading.value = false;
            }
        };

        const fetchChapterDetail = async () => {
            if (!selectedChapterId.value) return;
            loading.value = true;
            try {
                const hash = selectedNovel.value.hashes[0];
                const data = await API.fetchChapterDetail(selectedNovel.value.name, hash, selectedRun.value.timestamp, selectedChapterId.value);
                currentChapter.value = data;
                activeSummaryIndex.value = -1;
                entityScope.value = 'chapter';
            } finally {
                loading.value = false;
            }
        };

        const fetchGlobalEntities = async () => {
            if (!selectedNovel.value || !selectedRun.value) return;
            if (globalEntities.value.length > 0) return;
            
            loading.value = true;
            try {
                const hash = selectedNovel.value.hashes[0];
                globalEntities.value = await API.fetchGlobalEntities(selectedNovel.value.name, hash, selectedRun.value.timestamp);
            } finally {
                loading.value = false;
            }
        };

        const fetchGraphData = async () => {
            if (!selectedNovel.value || !selectedRun.value) return;
            
            if (graphData.value.nodes.length > 0) {
                nextTick(() => initGraph());
                return;
            }

            graphLoading.value = true;
            try {
                const hash = selectedNovel.value.hashes[0];
                graphData.value = await API.fetchGraphData(selectedNovel.value.name, hash, selectedRun.value.timestamp);
                nextTick(() => initGraph());
            } finally {
                graphLoading.value = false;
            }
        };

        const initGraph = () => {
            if (graphData.value.nodes.length === 0) return;
            
            // Init Vis.js
            graphController.init(graphData.value.nodes, graphData.value.edges);
            
            // Initial filter
            updateGraphFilter();
        };

        const updateGraphFilter = () => {
            graphController.updateFilter(
                graphData.value, 
                chapters.value, 
                timelineIndex.value, 
                graphFilterMode.value,
                minGraphWeight.value,
                new Set(visibleEntityTypes.value)
            );
        };

        const setGraphFilterMode = (mode) => {
            graphFilterMode.value = mode;
            updateGraphFilter();
        };
        
        const setEntityScope = (scope) => {
            entityScope.value = scope;
            if (scope === 'book') fetchGlobalEntities();
        };

        const selectChapter = (id) => {
            selectedChapterId.value = id;
            fetchChapterDetail();
        };

        const enterIntensiveReading = async (id) => {
            selectedChapterId.value = id;
            // Set loading true immediately to prevent UI interaction
            loading.value = true;
            try {
                // Wait for data fetch
                await fetchChapterDetail();
                // Only switch view after data is ready
                viewMode.value = 'focus';
            } catch (e) {
                console.error("Failed to enter intensive reading:", e);
            } finally {
                loading.value = false;
            }
        };

        const showOverview = () => {
            viewMode.value = 'overview';
            // Optional: Scroll to top or reset filters
        };

        const scrollToSpan = (spans) => {
            if (!spans || spans.length === 0) return;
            const summaryIdx = currentChapter.value.summary_sentences.findIndex(s => s.source_spans === spans);
            activeSummaryIndex.value = summaryIdx;
            nextTick(() => {
                const el = document.getElementById(`span-${summaryIdx}`);
                if (el) {
                    document.querySelectorAll('.active-span').forEach(e => e.classList.remove('active-span'));
                    el.classList.add('active-span');
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
        };

        const formatTime = (ts) => {
            if (ts.length === 15) {
                return `${ts.slice(0,4)}-${ts.slice(4,6)}-${ts.slice(6,8)} ${ts.slice(9,11)}:${ts.slice(11,13)}`;
            }
            return ts;
        };
        
        // --- Watchers ---
        
        const scrollToCard = (id) => {
            if (!id || viewMode.value !== 'overview') return;
            nextTick(() => {
                const el = document.getElementById('card-' + id);
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    // Visual feedback
                    el.classList.add('ring-4', 'ring-indigo-300');
                    setTimeout(() => el.classList.remove('ring-4', 'ring-indigo-300'), 1500);
                } else {
                    console.warn(`Card for chapter ${id} not found in DOM.`);
                }
            });
        };

        watch(selectedChapterId, (newId) => {
            scrollToCard(newId);
        });

        // Also watch chapters loaded, in case selection happens before render
        watch(chapters, () => {
            if (selectedChapterId.value) {
                scrollToCard(selectedChapterId.value);
            }
        });

        watch(viewMode, (newVal) => {
            if (newVal === 'graph') {
                if (chapters.value.length > 0 && timelineIndex.value === 0) {
                    timelineIndex.value = chapters.value.length - 1;
                }
                fetchGraphData();
            }
        });

        watch(chapters, (newVal) => {
            if (newVal.length > 0 && viewMode.value === 'graph') {
                if (timelineIndex.value === 0) {
                    timelineIndex.value = newVal.length - 1;
                }
                updateGraphFilter();
            }
        });

        // Debug
        const debugOutput = ref("Ready to debug...");
        const runDebug = () => {
            let log = `Chapters: ${chapters.value.length}\n`;
            log += `Edges: ${graphData.value.edges.length}\n`;
            log += `Timeline Index: ${timelineIndex.value}\n`;
            
            if (chapters.value.length > 0) {
                log += `First Chap ID: '${chapters.value[0].id}'\n`;
                
                const chapIdToIndex = {};
                chapters.value.forEach((c, i) => chapIdToIndex[c.id] = i);
                
                if (graphData.value.edges.length > 0) {
                    const edge = graphData.value.edges[0];
                    if (edge.timeline && edge.timeline.length > 0) {
                        const event = edge.timeline[0];
                        const cid = event.chapter_id;
                        log += `Event Chap ID: '${cid}'\n`;
                        log += `Index in Map: ${chapIdToIndex[cid]}\n`;
                        log += `Current Filter Idx: ${timelineIndex.value}\n`;
                        log += `Condition: ${chapIdToIndex[cid]} <= ${timelineIndex.value} ?\n`;
                    } else {
                        log += `Edge[0] timeline is empty or missing!\n`;
                    }
                }
            }
            debugOutput.value = log;
        };

        return {
            novels, runs, chapters,
            selectedNovel, selectedRun, selectedChapterId, currentChapter,
            loading, activeSummaryIndex, viewMode, groupedEntities,
            entityScope, 
            
            // Methods
            fetchRuns, fetchChapters, fetchChapterDetail,
            selectChapter, enterIntensiveReading, showOverview,
            scrollToSpan, formatTime, setEntityScope,
            
            // Computed
            highlightedContent, currentTimelineChapter, timelineLabels,

            // Graph
            graphLoading, timelineIndex, graphStats, graphFilterMode,
            minGraphWeight, availableEntityTypes, visibleEntityTypes,
            setGraphFilterMode, updateGraphFilter,
            fitGraph: () => graphController.fit(),
            
            // Debug
            debugOutput, runDebug
        };
    }
});

app.mount('#app');
