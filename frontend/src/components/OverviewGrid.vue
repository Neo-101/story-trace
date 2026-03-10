<script setup lang="ts">
import { useNovelStore } from '@/stores/novel';
import { computed, watch, nextTick, ref, onMounted, onUnmounted } from 'vue';
import type { Chapter, PlotSegment, PlotArc } from '@/types';

const store = useNovelStore();

// --- Scroll Sync ---
const activeChapterId = ref<string | null>(null);
let observer: IntersectionObserver | null = null;

onMounted(() => {
  // Initialize IntersectionObserver
  observer = new IntersectionObserver((entries) => {
    // Find the first visible entry
    const visibleEntry = entries.find(e => e.isIntersecting);
    if (visibleEntry) {
      // Extract ID from 'card-ID'
      const id = visibleEntry.target.id.replace('card-', '');
      activeChapterId.value = id;
    }
  }, {
    root: document.getElementById('overview-container'),
    threshold: 0.5 // Trigger when 50% visible
  });
});

onUnmounted(() => {
  if (observer) observer.disconnect();
});

// Load entities for filtering
onMounted(() => {
  if (store.currentRun) {
    store.loadGlobalEntities();
  }
});

// Watch run change to reload entities
watch(() => store.currentRun, (newRun) => {
  if (newRun) {
    store.loadGlobalEntities();
  }
});

// --- State & Computed ---

const searchQuery = ref('');
const filterPov = ref('All');
const filterIntensity = ref('All'); // Intensity Filter: All, High, Medium, Low

// --- Intensity Calculation ---

// 1. Calculate raw scores for all chapters
const chapterScores = computed(() => {
  const map = new Map<string, number>();
  if (store.chapters.length === 0) return map;

  store.chapters.forEach(c => {
    const stats = c.stats || { entity_count: 0, relationship_count: 0 };
    const score = (stats.entity_count * 1.5) + (stats.relationship_count * 3.0);
    map.set(c.id, score);
  });
  return map;
});

// 2. Calculate thresholds based on percentiles (33% and 66%)
const intensityThresholds = computed(() => {
  const scores = Array.from(chapterScores.value.values()).sort((a, b) => a - b);
  if (scores.length === 0) return { low: 0, high: 0 };
  
  const p33 = scores[Math.floor(scores.length * 0.33)] || 0;
  const p66 = scores[Math.floor(scores.length * 0.66)] || 0;
  
  return { low: p33, high: p66 };
});

// 3. Helper to determine intensity level
const getIntensityLevel = (chapterId: string) => {
  const score = chapterScores.value.get(chapterId) || 0;
  const { low, high } = intensityThresholds.value;
  
  if (score >= high) return 'High';
  if (score >= low) return 'Medium';
  return 'Low';
};

const getIntensityColor = (chapterId: string) => {
  const level = getIntensityLevel(chapterId);
  if (level === 'Low') return 'bg-emerald-400'; // Green for Low/Build-up
  if (level === 'Medium') return 'bg-amber-400'; // Yellow for Medium/Progression
  return 'bg-rose-500'; // Red for High/Climax
};

// --- Filtering Logic ---

const povOptions = computed(() => {
  // Extract unique entities that have chapter_ids (appear in chapters)
  return store.globalEntities
    .filter(e => e.chapter_ids && e.chapter_ids.length > 0)
    .map(e => ({ name: e.name, label: e.name }));
});

const filteredChapters = computed(() => {
  let chapters = store.chapters;

  // 1. Search
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    chapters = chapters.filter(c => 
      c.title.toLowerCase().includes(q) || 
      (c.headline && c.headline.toLowerCase().includes(q))
    );
  }

  // 2. POV Filter
  if (filterPov.value !== 'All') {
    const entity = store.globalEntities.find(e => e.name === filterPov.value);
    if (entity && entity.chapter_ids) {
      const allowedIds = new Set(entity.chapter_ids);
      chapters = chapters.filter(c => allowedIds.has(c.id));
    } else {
      // If selected POV has no data, return empty
      chapters = [];
    }
  }

  // 3. Intensity Filter
  if (filterIntensity.value !== 'All') {
      chapters = chapters.filter(c => getIntensityLevel(c.id) === filterIntensity.value);
  }

  return chapters;
});

const filteredChapterIds = computed(() => new Set(filteredChapters.value.map(c => c.id)));

// --- Grouping Logic ---

// 1. All Chapters (Unfiltered) - For Sidebar & Timeline Structure
const allChaptersByVolume = computed(() => {
  const groups: Record<string, Chapter[]> = {};
  const noVolumeKey = "未分卷";
  
  store.chapters.forEach(chap => {
    const vol = chap.volume_title || noVolumeKey;
    if (!groups[vol]) groups[vol] = [];
    groups[vol].push(chap);
  });
  
  return groups;
});

// 2. Filtered Chapters (Grouped) - For Main Grid Fallback
const groupedChapters = computed(() => {
  const groups: Record<string, Chapter[]> = {};
  const noVolumeKey = "未分卷";
  
  filteredChapters.value.forEach(chap => {
    const vol = chap.volume_title || noVolumeKey;
    if (!groups[vol]) groups[vol] = [];
    groups[vol].push(chap);
  });
  
  return groups;
});

// Ordered Volume Keys (Based on All Chapters to keep sidebar stable)
const volumeKeys = computed(() => {
  const groups = allChaptersByVolume.value; // Use unfiltered keys to keep sidebar stable
  return Object.keys(groups).sort((a, b) => {
    const noVolumeKey = "未分卷";
    if (a === noVolumeKey) return -1;
    if (b === noVolumeKey) return 1;
    
    const chapA = groups[a][0];
    const chapB = groups[b][0];
    return (chapA?.index || 0) - (chapB?.index || 0);
  });
});

// --- Segmentation Logic ---

// Computed Segments (Grouped by Volume)
const segmentedVolumes = computed(() => {
  const result: Record<string, PlotSegment[]> = {};
  
  // Use backend segments if available
  if (store.segments.length > 0) {
      // Map segments to volumes
      // And attach chapter objects (because API response only has indices)
      
      // First, create a map of index -> chapter for fast lookup
      const chapterMap = new Map<number, Chapter>();
      store.chapters.forEach(c => chapterMap.set(c.index, c));
      
      store.segments.forEach(seg => {
          const vol = seg.volume_title || "未分卷";
          if (!result[vol]) result[vol] = [];
          
          // Hydrate chapters AND Apply Filter
          const chapters: Chapter[] = [];
          const start = seg.start_chapter_index;
          const end = seg.end_chapter_index;
          
          if (start !== undefined && end !== undefined) {
             for (let i = start; i <= end; i++) {
                const c = chapterMap.get(i);
                // Check if chapter exists AND passes filter
                if (c && filteredChapterIds.value.has(c.id)) {
                    chapters.push(c);
                }
             }
          } else {
             // Fallback if no indices
             seg.chapters.forEach(c => {
                 if (filteredChapterIds.value.has(c.id)) {
                     chapters.push(c);
                 }
             });
          }
          
          result[vol].push({
              ...seg,
              chapters: chapters
          });
      });
      
      return result;
  }

  // Fallback: Group by volume as single segment (if backend not ready)
  Object.entries(groupedChapters.value).forEach(([volTitle, chapters]) => {
        result[volTitle] = [{
            id: `seg-${volTitle}-0`,
            volume_title: volTitle,
            title: "全卷概览",
            synopsis: "",
            chapters: chapters,
            avg_intensity: 0 
        }];
  });
  
  return result;
});

// Watch for DOM updates to observe new elements (Moved here to avoid TDZ)
watch(segmentedVolumes, () => {
  nextTick(() => {
    if (!observer) return;
    observer.disconnect(); // Reset
    
    const cards = document.querySelectorAll('[id^="card-"]');
    cards.forEach(card => observer?.observe(card));
  });
});

// Accordion State for Volumes
const expandedVolumes = ref<Set<string>>(new Set());

// Accordion State for Arcs (Key: arc.id)
const expandedArcs = ref<Set<string>>(new Set());

// Accordion State for Segments (Key: segment.id)
const expandedSegments = ref<Set<string>>(new Set());

// Initialize: Expand all Volumes by default
watch(() => volumeKeys.value, (keys) => {
  if (keys.length > 0 && expandedVolumes.value.size === 0) {
    keys.forEach(k => expandedVolumes.value.add(k));
  }
}, { immediate: true });

const toggleVolume = (vol: string) => {
  if (expandedVolumes.value.has(vol)) {
    expandedVolumes.value.delete(vol);
  } else {
    expandedVolumes.value.add(vol);
  }
};

const toggleArc = (arcId: string) => {
  if (expandedArcs.value.has(arcId)) {
    expandedArcs.value.delete(arcId);
  } else {
    expandedArcs.value.add(arcId);
  }
};

const toggleSegment = (segId: string) => {
  if (expandedSegments.value.has(segId)) {
    expandedSegments.value.delete(segId);
  } else {
    expandedSegments.value.add(segId);
  }
};

// --- Arc Logic ---
const computedArcs = computed(() => {
    const result: Record<string, PlotArc[]> = {};
    
    if (store.arcs.length > 0) {
        // Hydrate Arcs with Segments
        // We need to map segments to arcs based on chapter range
        // Since segments are already computed in segmentedVolumes (which are grouped by volume),
        // we might need a flat list of segments first?
        // Or we can iterate over segmentedVolumes and assign them to arcs.
        
        // Actually, store.arcs contains the arcs. We need to attach segments to them.
        // And segments need to attach chapters.
        
        // 1. Flatten all segments from store.segments (already flat)
        // 2. Hydrate segments with chapters (same logic as segmentedVolumes)
        
        // Let's reuse segmentedVolumes logic but structure it into Arcs
        
        // First, hydrate all segments with chapters
        const chapterMap = new Map<number, Chapter>();
        store.chapters.forEach(c => chapterMap.set(c.index, c));
        
        const hydratedSegments = store.segments.map(seg => {
             const chapters: Chapter[] = [];
             const start = seg.start_chapter_index ?? 0;
             const end = seg.end_chapter_index ?? Infinity;
             for (let i = start; i <= end; i++) {
                  const c = chapterMap.get(i);
                  if (c) chapters.push(c);
             }
             return { ...seg, chapters };
        });
        
        // Now group segments into Arcs
        store.arcs.forEach(arc => {
            const vol = arc.volume_title || "未分卷";
            if (!result[vol]) result[vol] = [];
            
            // Find segments that fall into this arc
            // Simple logic: segment start >= arc start AND segment end <= arc end
            const arcSegments = hydratedSegments.filter(s => 
                (s.start_chapter_index ?? 0) >= (arc.start_chapter_index ?? 0) &&
                (s.end_chapter_index ?? Infinity) <= (arc.end_chapter_index ?? Infinity)
            );
            
            result[vol].push({
                ...arc,
                segments: arcSegments
            });
        });
        
        // Handle "Orphan" segments (those not covered by any Arc)?
        // For simplicity, assume Arcs cover everything or we just display Arcs.
    }
    
    return result;
});

// Initialize: Collapse all Arcs by default (Moved here to avoid TDZ)
watch(() => computedArcs.value, (arcs) => {
    // Keep arcs collapsed by default
}, { immediate: true });

// Initialize: Collapse all Segments by default (Moved here to avoid TDZ)
watch(() => segmentedVolumes.value, (vols) => {
    // Keep segments collapsed by default
}, { immediate: true });

const scrollToVolume = (vol: string) => {
  const el = document.getElementById(`vol-${vol}`);
  if (el) {
    // Offset for sticky header if needed
    const yOffset = -80; 
    const y = el.getBoundingClientRect().top + window.pageYOffset + yOffset;
    window.scrollTo({top: y, behavior: 'smooth'});
    
    // Ensure expanded
    if (!expandedVolumes.value.has(vol)) {
      expandedVolumes.value.add(vol);
    }
  }
};

// Auto-Scroll Logic (preserved)
watch(() => store.selectedChapterId, (newId) => {
  if (!newId || store.viewMode !== 'overview') return;

  nextTick(() => {
    const el = document.getElementById(`card-${newId}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('ring-4', 'ring-indigo-300');
      setTimeout(() => el.classList.remove('ring-4', 'ring-indigo-300'), 1500);
    }
  });
});

const enterIntensiveReading = async (chapterId: string) => {
  store.selectedChapterId = chapterId;
  await store.loadChapterDetail(chapterId);
  store.viewMode = 'focus'; // Or 'reader' depending on your app routing
};

const isRefreshing = ref(false);
const refreshStructure = async () => {
  if (!store.currentNovel || isRefreshing.value) return;
  const hash = store.currentNovel.hashes[0];
  if (!hash) return;
  
  isRefreshing.value = true;
  try {
    console.log("Forcing regeneration of segments and arcs...");
    // 假设 store 中有一个可调用的方法，比如 generateArcs，用于触发后端生成 Arc
    // 临时跳过生成 Arc，等待后端接口就绪
    console.warn('generateArcs 方法尚未实现，跳过 Arc 生成');
    
    // Reload
    await store.loadSegments();
    await store.loadArcs();
  } catch (e) {
    console.error("Refresh failed:", e);
    alert("刷新失败，请查看控制台");
  } finally {
    isRefreshing.value = false;
  }
};

</script>

<template>
  <div class="h-full flex flex-col bg-gray-50/50">
    
    <!-- 1. Top Bar: Filters & Timeline (Horizontal) -->
    <!-- Alternatively, sidebar for timeline. User asked for "Sidebar or Topbar". -->
    <!-- Let's try a sticky Sidebar on the left for Timeline, and Topbar for Filter. -->
    
    <div class="flex h-full overflow-hidden">
      
      <!-- Sidebar Timeline -->
      <aside class="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col overflow-y-auto hidden md:flex">
        <div class="p-4 border-b border-gray-100 flex justify-between items-center">
          <div>
            <h2 class="font-bold text-gray-700">剧情时间轴</h2>
            <p class="text-xs text-gray-400 mt-1">共 {{ store.chapters.length }} 章</p>
          </div>
          <!-- Refresh Button -->
          <button 
            @click="refreshStructure" 
            class="p-1.5 rounded-full hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 transition-colors"
            :class="{'animate-spin text-indigo-500': isRefreshing}"
            title="重新生成剧情结构 (Arc/Segment)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <nav class="p-2 space-y-4">
          <div v-for="vol in volumeKeys" :key="vol" class="group">
            <!-- Volume Header -->
            <button 
              @click="scrollToVolume(vol)"
              class="w-full text-left px-2 py-1 rounded-md text-sm font-medium text-gray-600 hover:text-indigo-600 hover:bg-gray-50 flex items-center justify-between transition-colors mb-1"
            >
              <span class="truncate">{{ vol }}</span>
              <span class="text-[10px] text-gray-300">{{ allChaptersByVolume[vol].length }}</span>
            </button>
            
            <!-- Micro-Heatmap Chapters -->
            <div class="flex flex-wrap gap-[2px] px-2">
              <div 
                v-for="chap in allChaptersByVolume[vol]" 
                :key="chap.id"
                @click="enterIntensiveReading(chap.id)"
                class="w-1.5 h-4 rounded-sm transition-all duration-300 cursor-pointer hover:scale-125 hover:z-10"
                :class="[
                  getIntensityColor(chap.id),
                  filteredChapterIds.has(chap.id) ? 'opacity-100' : 'opacity-10 grayscale',
                  activeChapterId === chap.id ? 'ring-2 ring-white scale-125 z-20 shadow-md' : ''
                ]"
                :title="`${chap.title} (强度: ${(chapterScores.get(chap.id)||0).toFixed(2)})`"
              ></div>
            </div>
          </div>
        </nav>
      </aside>

      <!-- Main Content Area -->
      <main class="flex-1 flex flex-col h-full overflow-hidden relative">
        
        <!-- Filter Bar -->
        <header class="bg-white border-b border-gray-200 p-4 flex items-center gap-4 shadow-sm z-10 flex-shrink-0">
          <div class="relative flex-1 max-w-md">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索章节标题或概览..." 
              class="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-sm outline-none"
            >
          </div>
          
          <div class="flex items-center gap-2">
            <!-- Filter Placeholders -->
            <select v-model="filterPov" class="px-3 py-2 rounded-lg border border-gray-200 text-sm bg-white focus:border-indigo-500 outline-none cursor-pointer hover:border-indigo-300 transition-colors min-w-[140px]">
              <option value="All">全部视角</option>
              <option v-for="opt in povOptions" :key="opt.name" :value="opt.name">
                {{ opt.label }}
              </option>
            </select>
            
            <!-- Intensity Filter -->
            <select v-model="filterIntensity" class="px-3 py-2 rounded-lg border border-gray-200 text-sm bg-white focus:border-indigo-500 outline-none cursor-pointer hover:border-indigo-300 transition-colors min-w-[120px]">
              <option value="All">全部强度</option>
              <option value="High">高潮 (High)</option>
              <option value="Medium">推进 (Mid)</option>
              <option value="Low">铺垫 (Low)</option>
            </select>
            
             <button class="p-2 text-gray-400 hover:text-indigo-600 transition-colors" title="更多筛选">
               <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
               </svg>
             </button>
          </div>
        </header>

        <!-- Scrollable Grid -->
        <div class="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth" id="overview-container">
          
          <div v-for="vol in volumeKeys" :key="vol" :id="`vol-${vol}`" class="scroll-mt-20">
            
            <!-- Volume Header (Sticky) -->
            <div 
              @click="toggleVolume(vol)"
              class="sticky top-0 z-10 bg-white/95 backdrop-blur-sm px-4 py-3 rounded-xl border border-gray-200/50 shadow-sm mb-4 cursor-pointer hover:bg-gray-50 transition-colors flex items-center justify-between group select-none"
            >
              <div class="flex items-center gap-3">
                <span class="bg-indigo-100 text-indigo-700 p-1 rounded transition-transform duration-300" :class="expandedVolumes.has(vol) ? 'rotate-90' : ''">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </span>
                <h3 class="text-lg font-bold text-gray-800">{{ vol }}</h3>
                <span class="text-xs text-gray-400 font-mono">{{ groupedChapters[vol]?.length || 0 }} 章</span>
              </div>
              <div class="h-px bg-gray-100 flex-1 mx-4"></div>
            </div>

            <!-- Volume Grid (Accordion Body) -->
            <transition
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="opacity-0 -translate-y-2 max-h-0 overflow-hidden"
              enter-to-class="opacity-100 translate-y-0 max-h-[5000px] overflow-visible"
              leave-active-class="transition-all duration-200 ease-in"
              leave-from-class="opacity-100 max-h-[5000px]"
              leave-to-class="opacity-0 max-h-0 overflow-hidden"
            >
              <div v-show="expandedVolumes.has(vol)" class="px-2">
                <!-- Empty State for Volume -->
                <div v-if="(groupedChapters[vol]?.length || 0) === 0" class="py-8 text-center bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
                  <p class="text-sm text-gray-400">本卷无该角色出场</p>
                </div>

                <div v-else class="space-y-6">
                  
                  <!-- Arcs Loop (If Arcs Exist) -->
                  <div v-if="computedArcs[vol] && computedArcs[vol].length > 0" class="space-y-4">
                     <div 
                        v-for="arc in computedArcs[vol]" 
                        :key="arc.id"
                        class="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm"
                     >
                        <!-- Arc Header -->
                        <div 
                          class="flex flex-col gap-2 mb-2 px-1 cursor-pointer select-none"
                          @click="toggleArc(arc.id)"
                        >
                          <div class="flex items-center gap-3">
                            <div class="h-8 w-1.5 rounded-full bg-indigo-600"></div>
                            <h3 class="font-bold text-gray-800 text-lg flex items-center gap-2">
                              {{ arc.title }}
                              <span class="text-xs font-normal text-gray-400 bg-gray-50 border border-gray-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                                <span class="bg-indigo-50 text-indigo-600 px-1.5 rounded text-[10px] mr-1 font-medium">Arc</span>
                                <span>{{ (arc.end_chapter_index - arc.start_chapter_index + 1) }} 章</span>
                                <span class="text-gray-300 mx-0.5">|</span>
                                <span class="font-mono text-gray-500">
                                  #{{ arc.start_chapter_index }}~#{{ arc.end_chapter_index }}
                                </span>
                              </span>
                            </h3>
                             <!-- Expand Icon -->
                            <span class="text-gray-400 transition-transform duration-200" :class="expandedArcs.has(arc.id) ? 'rotate-90' : ''">
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                              </svg>
                            </span>
                            
                            <div class="flex-1 mx-2"></div>
                            
                            <!-- Arc Timeline (Aggregated from Segments) -->
                            <!-- We can show a simplified heatmap or just segment blocks -->
                            <div class="flex gap-1">
                                <div 
                                    v-for="seg in arc.segments"
                                    :key="seg.id"
                                    class="h-4 rounded-sm"
                                    :style="{ width: Math.max(seg.chapters.length * 2, 4) + 'px' }"
                                    :class="[
                                        // Use safe access for thresholds
                                        seg.avg_intensity >= (intensityThresholds.high || 0) ? 'bg-rose-400' : 
                                        (seg.avg_intensity >= (intensityThresholds.low || 0) ? 'bg-amber-300' : 'bg-emerald-300')
                                    ]"
                                    :title="`${seg.title} (${seg.chapters.length}章, 强度: ${seg.avg_intensity.toFixed(1)})`"
                                ></div>
                            </div>
                          </div>
                          
                          <!-- Arc Synopsis -->
                          <div class="pl-5 pr-2">
                             <p class="text-sm text-gray-600 leading-relaxed italic border-l-2 border-indigo-100 pl-3 py-1" v-if="arc.synopsis">
                               {{ arc.synopsis }}
                             </p>
                          </div>
                        </div>
                        
                        <!-- Segments List (Collapsible) -->
                        <transition
                          enter-active-class="transition-all duration-300 ease-out"
                          enter-from-class="opacity-0 -translate-y-2 max-h-0 overflow-hidden"
                          enter-to-class="opacity-100 translate-y-0 max-h-[5000px] overflow-visible"
                          leave-active-class="transition-all duration-200 ease-in"
                          leave-from-class="opacity-100 max-h-[5000px]"
                          leave-to-class="opacity-0 max-h-0 overflow-hidden"
                        >
                          <div v-show="expandedArcs.has(arc.id)" class="pl-4 border-l-2 border-dashed border-gray-100 ml-2 mt-4 space-y-4">
                              <div 
                                v-for="segment in arc.segments" 
                                :key="segment.id"
                                class="bg-gray-50/50 rounded-xl p-3 border border-gray-100/50 hover:border-indigo-100 transition-colors"
                              >
                                <!-- Segment Header (Reuse existing logic) -->
                                <div 
                                  class="flex flex-col gap-1 mb-2 px-1 cursor-pointer select-none"
                                  @click="toggleSegment(segment.id)"
                                >
                                  <div class="flex items-center gap-3">
                                    <div class="h-6 w-1 rounded-full bg-indigo-400"></div>
                                    <h4 class="font-bold text-gray-700 text-sm flex items-center gap-2">
                                      {{ segment.title }}
                                      <span class="text-[10px] font-normal text-gray-400 bg-white border border-gray-200 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                                        <span>{{ segment.chapters.length }} 章</span>
                                        <span class="text-gray-300 mx-0.5">|</span>
                                        <span v-if="segment.chapters.length > 0" class="font-mono text-gray-500">
                                          #{{ segment.chapters[0].index }}~#{{ segment.chapters[segment.chapters.length-1].index }}
                                        </span>
                                      </span>
                                    </h4>
                                    <!-- Expand Icon -->
                                    <span class="text-gray-400 transition-transform duration-200" :class="expandedSegments.has(segment.id) ? 'rotate-90' : ''">
                                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                                      </svg>
                                    </span>
                                    
                                    <div class="flex-1 mx-2"></div>
                                    
                                    <!-- Segment Timeline (Mini Heatmap) -->
                                    <div class="flex flex-wrap gap-[2px] items-center" @click.stop>
                                      <div 
                                        v-for="chap in segment.chapters" 
                                        :key="chap.id"
                                        @click="enterIntensiveReading(chap.id)"
                                        class="w-1.5 h-4 rounded-sm transition-all duration-300 cursor-pointer hover:scale-125 hover:z-10"
                                        :class="[
                                            getIntensityColor(chap.id),
                                            filteredChapterIds.has(chap.id) ? 'opacity-100' : 'opacity-10 grayscale',
                                            activeChapterId === chap.id ? 'ring-1 ring-white scale-125 z-20 shadow-sm' : ''
                                        ]"
                                        :title="`${chap.title} (强度: ${(chapterScores.get(chap.id)||0).toFixed(2)})`"
                                      ></div>
                                    </div>
                                  </div>
                                  
                                  <!-- Synopsis -->
                                  <div class="pl-4 pr-2">
                                    <p class="text-xs text-gray-500 leading-relaxed bg-white/50 p-2 rounded-md border border-gray-100/50" v-if="segment.synopsis">
                                      {{ segment.synopsis }}
                                    </p>
                                  </div>
                                </div>

                                <!-- Chapters Grid (Collapsible) -->
                                <transition
                                  enter-active-class="transition-all duration-300 ease-out"
                                  enter-from-class="opacity-0 -translate-y-2 max-h-0 overflow-hidden"
                                  enter-to-class="opacity-100 translate-y-0 max-h-[5000px] overflow-visible"
                                  leave-active-class="transition-all duration-200 ease-in"
                                  leave-from-class="opacity-100 max-h-[5000px]"
                                  leave-to-class="opacity-0 max-h-0 overflow-hidden"
                                >
                                  <div v-show="expandedSegments.has(segment.id)" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-2">
                                    <div 
                                      v-for="chap in segment.chapters" 
                                      :key="chap.id"
                                      :id="`card-${chap.id}`"
                                      @click="enterIntensiveReading(chap.id)"
                                      class="bg-white p-5 rounded-xl border border-gray-100 hover:border-indigo-400 hover:shadow-md cursor-pointer transition-all duration-200 group relative flex flex-col min-h-[160px]"
                                      :class="{'ring-2 ring-indigo-500 bg-indigo-50/10': store.selectedChapterId === chap.id}"
                                    >
                                      <div class="flex justify-between items-start mb-2">
                                        <h4 class="font-bold text-gray-800 text-base group-hover:text-indigo-600 transition-colors line-clamp-1" :title="chap.title">
                                          {{ chap.title }}
                                        </h4>
                                        <span class="text-[10px] font-mono text-gray-300 bg-gray-50 px-1.5 rounded">
                                          #{{ chap.index }}
                                        </span>
                                      </div>
                                      
                                      <div class="flex-1">
                                        <p class="text-xs text-gray-500 leading-relaxed line-clamp-4" v-if="chap.headline">
                                          {{ chap.headline }}
                                        </p>
                                        <p class="text-xs text-gray-300 italic mt-2" v-else>
                                          (暂无概览)
                                        </p>
                                      </div>

                                      <!-- Hover Action -->
                                      <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-1 group-hover:translate-y-0 duration-200">
                                        <span class="text-xs bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-full font-medium flex items-center gap-1 shadow-sm">
                                          阅读 <span class="text-xs">&rarr;</span>
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                </transition>
                              </div>
                          </div>
                        </transition>
                     </div>
                  </div>

                  <!-- Fallback: Segments Loop (If No Arcs or Fallback needed) -->
                  <div v-else>
                    <div 
                      v-for="segment in segmentedVolumes[vol]" 
                      :key="segment.id"
                      class="bg-gray-50/50 rounded-2xl p-4 border border-gray-100/50 hover:border-indigo-100 transition-colors"
                    >
                    <!-- Segment Header -->
                    <div 
                      class="flex flex-col gap-1 mb-2 px-1 cursor-pointer select-none"
                      @click="toggleSegment(segment.id)"
                    >
                      <div class="flex items-center gap-3">
                        <div class="h-6 w-1 rounded-full bg-indigo-400"></div>
                        <h4 class="font-bold text-gray-700 text-sm flex items-center gap-2">
                          {{ segment.title }}
                          <span class="text-[10px] font-normal text-gray-400 bg-white border border-gray-200 px-1.5 py-0.5 rounded-full flex items-center gap-1">
                            <span>{{ segment.chapters.length }} 章</span>
                            <span class="text-gray-300 mx-0.5">|</span>
                            <span v-if="segment.chapters.length > 0" class="font-mono text-gray-500">
                              #{{ segment.chapters[0].index }}~#{{ segment.chapters[segment.chapters.length-1].index }}
                            </span>
                          </span>
                        </h4>
                        <!-- Expand Icon -->
                        <span class="text-gray-400 transition-transform duration-200" :class="expandedSegments.has(segment.id) ? 'rotate-90' : ''">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                          </svg>
                        </span>
                        
                        <div class="flex-1 mx-2"></div>
                        
                        <!-- Segment Timeline (Mini Heatmap) -->
                        <div class="flex flex-wrap gap-[2px] items-center" @click.stop>
                          <div 
                            v-for="chap in segment.chapters" 
                            :key="chap.id"
                            @click="enterIntensiveReading(chap.id)"
                            class="w-1.5 h-4 rounded-sm transition-all duration-300 cursor-pointer hover:scale-125 hover:z-10"
                            :class="[
                                getIntensityColor(chap.id),
                                filteredChapterIds.has(chap.id) ? 'opacity-100' : 'opacity-10 grayscale',
                                activeChapterId === chap.id ? 'ring-1 ring-white scale-125 z-20 shadow-sm' : ''
                            ]"
                            :title="`${chap.title} (强度: ${(chapterScores.get(chap.id)||0).toFixed(2)})`"
                          ></div>
                        </div>
                      </div>
                      
                      <!-- Synopsis (Visible always or only when collapsed? Usually header info is always visible. Let's show it always for context) -->
                      <div class="pl-4 pr-2">
                        <p class="text-xs text-gray-500 leading-relaxed bg-white/50 p-2 rounded-md border border-gray-100/50" v-if="segment.synopsis">
                          {{ segment.synopsis }}
                        </p>
                      </div>
                    </div>

                    <!-- Chapters Grid (Collapsible) -->
                    <transition
                      enter-active-class="transition-all duration-300 ease-out"
                      enter-from-class="opacity-0 -translate-y-2 max-h-0 overflow-hidden"
                      enter-to-class="opacity-100 translate-y-0 max-h-[5000px] overflow-visible"
                      leave-active-class="transition-all duration-200 ease-in"
                      leave-from-class="opacity-100 max-h-[5000px]"
                      leave-to-class="opacity-0 max-h-0 overflow-hidden"
                    >
                      <div v-show="expandedSegments.has(segment.id)" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-2">
                        <div 
                          v-for="chap in segment.chapters" 
                          :key="chap.id"
                          :id="`card-${chap.id}`"
                          @click="enterIntensiveReading(chap.id)"
                          class="bg-white p-5 rounded-xl border border-gray-100 hover:border-indigo-400 hover:shadow-md cursor-pointer transition-all duration-200 group relative flex flex-col min-h-[160px]"
                          :class="{'ring-2 ring-indigo-500 bg-indigo-50/10': store.selectedChapterId === chap.id}"
                        >
                          <div class="flex justify-between items-start mb-2">
                            <h4 class="font-bold text-gray-800 text-base group-hover:text-indigo-600 transition-colors line-clamp-1" :title="chap.title">
                              {{ chap.title }}
                            </h4>
                            <span class="text-[10px] font-mono text-gray-300 bg-gray-50 px-1.5 rounded">
                              #{{ chap.index }}
                            </span>
                          </div>
                          
                          <div class="flex-1">
                            <p class="text-xs text-gray-500 leading-relaxed line-clamp-4" v-if="chap.headline">
                              {{ chap.headline }}
                            </p>
                            <p class="text-xs text-gray-300 italic mt-2" v-else>
                              (暂无概览)
                            </p>
                          </div>

                          <!-- Hover Action -->
                          <div class="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-1 group-hover:translate-y-0 duration-200">
                            <span class="text-xs bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-full font-medium flex items-center gap-1 shadow-sm">
                              阅读 <span class="text-xs">&rarr;</span>
                            </span>
                          </div>
                        </div>
                      </div>
                    </transition>
                  </div>
                  </div>
                </div>
              </div>
            </transition>
            
          </div>
          
          <!-- Empty State -->
          <div v-if="volumeKeys.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mb-2 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <p>暂无章节数据</p>
          </div>

        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Custom Scrollbar for Sidebar */
aside::-webkit-scrollbar {
  width: 4px;
}
aside::-webkit-scrollbar-track {
  background: transparent;
}
aside::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}
</style>