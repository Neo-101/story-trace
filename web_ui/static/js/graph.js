// Graph Controller for StoryTrace
// Handles Vis.js initialization and updates

export class GraphController {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.network = null;
        this.nodes = null;
        this.edges = null;
        this.options = options;
        
        // Stats callback
        this.onStatsUpdate = options.onStatsUpdate || (() => {});
    }

    destroy() {
        if (this.network) {
            this.network.destroy();
            this.network = null;
        }
        this.nodes = null;
        this.edges = null;
    }

    init(nodesData, edgesData) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        if (container.clientHeight === 0) {
            console.warn(`[Graph] Container #${this.containerId} has 0 height. Graph may not be visible.`);
        }

        this.destroy();

        // Nodes
        const uniqueNodes = new Map();
        nodesData.forEach(n => {
            if (!uniqueNodes.has(n.name)) {
                uniqueNodes.set(n.name, n);
            }
        });

        this.nodes = new window.vis.DataSet(
            Array.from(uniqueNodes.values()).map(n => ({
                id: n.name,
                label: n.name,
                group: n.type,
                value: n.count, // Size based on count
                title: `${n.name} (${n.type})\n${n.description}`, // Tooltip
                hidden: false // Explicitly visible by default
            }))
        );

        // Edges (Start empty, fill later via filter)
        this.edges = new window.vis.DataSet([]);

        const data = { nodes: this.nodes, edges: this.edges };
        
        const defaultOptions = {
            nodes: {
                shape: 'dot',
                scaling: {
                    min: 14,
                    max: 30,
                    label: {
                        enabled: true,
                        min: 14,
                        max: 30,
                        maxVisible: 30,
                        drawThreshold: 5
                    }
                },
                font: {
                    size: 14,
                    face: 'Tahoma'
                }
            },
            groups: {
                Person: { shape: 'dot', color: { background: '#fbbf24', border: '#d97706' } }, // Yellow Circle
                Location: { shape: 'square', color: { background: '#60a5fa', border: '#2563eb' } }, // Blue Square
                Organization: { shape: 'triangle', color: { background: '#a78bfa', border: '#7c3aed' } }, // Purple Triangle
                Item: { shape: 'diamond', color: { background: '#34d399', border: '#059669' } }, // Green Diamond
                Concept: { shape: 'star', color: { background: '#f472b6', border: '#db2777' } }, // Pink Star
                Other: { shape: 'dot', color: { background: '#9ca3af', border: '#4b5563' } } // Gray
            },
            edges: {
                arrows: 'to',
                color: { color: '#cbd5e1', highlight: '#6366f1' },
                smooth: { type: 'continuous' }
            },
            physics: {
                stabilization: false,
                barnesHut: {
                    gravitationalConstant: -10000,
                    springConstant: 0.04,
                    springLength: 120
                }
            }
        };

        this.network = new window.vis.Network(container, data, defaultOptions);
        
        // Auto-fit on stabilize
        this.network.on("stabilized", () => {
            this.network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
        });
        
        // Double click event
        this.network.on("doubleClick", (params) => {
            if (params.nodes.length > 0) {
                console.log("Selected node:", params.nodes[0]);
            }
        });

        return this.network;
    }

    updateFilter(graphData, chapters, timelineIndex, filterMode, minWeight = 1, visibleTypes = null) {
        // Safety check: ensure network and datasets are initialized
        if (!this.network || !this.nodes || !this.edges || !chapters.length) {
            console.warn("[Graph] Update skipped: Network not ready or no chapters.");
            return;
        }

        const currentChapIdx = timelineIndex;
        // const currentChapId = chapters[currentChapIdx]?.id;
        
        console.log(`Update Graph: Mode=${filterMode}, ChapterIndex=${currentChapIdx}, MinWeight=${minWeight}`);

        const rawEdges = graphData.edges;
        const newEdges = [];
        const activeNodeIds = new Set();

        // Build chapter index map
        const chapIdToIndex = {};
        chapters.forEach((c, i) => chapIdToIndex[c.id] = i);

        // First pass: collect relevant edges
        const potentialEdges = [];
        
        rawEdges.forEach(edge => {
            let lastInteraction = null;
            let weight = 0;
            
            if (filterMode === 'cumulative') {
                edge.timeline.forEach(event => {
                    const evtIdx = chapIdToIndex[event.chapter_id];
                    if (evtIdx !== undefined && evtIdx <= currentChapIdx) {
                        lastInteraction = event;
                        weight++;
                    }
                });
            } else {
                // Focus Mode
                edge.timeline.forEach(event => {
                    const evtIdx = chapIdToIndex[event.chapter_id];
                    if (evtIdx !== undefined && evtIdx === currentChapIdx) {
                        lastInteraction = event;
                        weight = 1;
                    }
                });
            }

            // Filter by weight (only in cumulative mode or if explicit weight filter is desired)
            // In Focus mode, weight is usually 1, so we might not want to filter by weight > 1 unless we have multi-interaction support in focus mode.
            // But let's apply it generally if user sets minWeight > 1.
            const effectiveMinWeight = filterMode === 'focus' ? 1 : minWeight;
            if (lastInteraction && weight >= effectiveMinWeight) {
                potentialEdges.push({
                    rawEdge: edge,
                    interaction: lastInteraction,
                    weight: weight
                });
                // We will add activeNodeIds later after type filtering
            }
        });

        // Sort and renumber for Focus Mode
        if (filterMode === 'focus') {
            potentialEdges.sort((a, b) => {
                const orderA = a.interaction.order || 0;
                const orderB = b.interaction.order || 0;
                return orderA - orderB;
            });
            
            potentialEdges.forEach((item, index) => {
                item.displayOrder = index + 1;
            });
        }

        // Build final edges
        potentialEdges.forEach(item => {
            const edge = item.rawEdge;
            const lastInteraction = item.interaction;
            const weight = item.weight;
            
            let label, title, width;

            if (filterMode === 'focus') {
                const displayOrder = item.displayOrder !== undefined ? item.displayOrder : lastInteraction.order;
                const orderPrefix = displayOrder ? `[${displayOrder}] ` : '';
                label = `${orderPrefix}${lastInteraction.relation}`;
                title = `[${lastInteraction.chapter_id}] #${lastInteraction.order || '?'} ${lastInteraction.relation}: ${lastInteraction.description}`;
                width = Math.max(1, Math.min(5, weight)); // Linear scale for focus
            } else {
                // Cumulative Mode: Simplified View
                label = undefined; // Hide label
                title = `${weight} interactions\nLast: ${lastInteraction.relation} (${lastInteraction.chapter_id})`;
                width = Math.log2(weight + 1) * 2; // Logarithmic scale
            }
            
            // Check if nodes are visible based on type
            const sourceNode = this.nodes.get(edge.source);
            const targetNode = this.nodes.get(edge.target);
            
            // Note: sourceNode/targetNode might be null if graphData.nodes is incomplete or nodes were removed. 
            // But usually they should be in this.nodes if they are in graphData.edges.
            // However, we need to check visibleTypes against the node data.
            // Since this.nodes contains all nodes, we can look them up.
            
            // We need to know the type of source and target. 
            // The edge object usually contains just source/target IDs. 
            // We can look up types from this.nodes.
            
            const isTypeVisible = (nodeId) => {
                if (!visibleTypes) return true; // No filter
                const node = this.nodes.get(nodeId);
                if (!node) return true; // Should not happen, but keep safe
                const type = node.group || 'Other';
                return visibleTypes.has(type);
            };

            if (isTypeVisible(edge.source) && isTypeVisible(edge.target)) {
                newEdges.push({
                    from: edge.source,
                    to: edge.target,
                    label: label,
                    title: title,
                    width: width,
                    arrows: {
                        to: { enabled: true, scaleFactor: 1, type: 'arrow' }
                    }
                });
                activeNodeIds.add(edge.source);
                activeNodeIds.add(edge.target);
            }
        });

        console.log(`[Graph] New Edges: ${newEdges.length}, Active Nodes: ${activeNodeIds.size}`);

        // Update Vis.js Data using stored DataSets
        this.edges.clear();
        this.edges.add(newEdges);
        
        const allNodes = this.nodes.get();
        
        const updatedNodes = allNodes.map(node => ({
            id: node.id,
            hidden: !activeNodeIds.has(node.id)
        }));
        this.nodes.update(updatedNodes);
        
        // Physics adjustment
        if (filterMode === 'focus') {
            this.network.setOptions({
                physics: {
                    barnesHut: { gravitationalConstant: -20000, springConstant: 0.02, springLength: 200 }
                }
            });
        } else {
            this.network.setOptions({
                physics: {
                    barnesHut: { gravitationalConstant: -10000, springConstant: 0.04, springLength: 120 }
                }
            });
        }
        
        // Auto-fit
        this.network.fit({ animation: { duration: 1000, easingFunction: 'easeInOutQuad' } });

        // Update stats
        this.onStatsUpdate({
            nodes: activeNodeIds.size,
            edges: newEdges.length
        });
    }

    fit() {
        if (this.network) {
            this.network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        }
    }
}
