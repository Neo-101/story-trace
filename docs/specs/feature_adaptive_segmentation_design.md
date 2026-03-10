# 自适应剧情分段系统设计 (Adaptive Plot Segmentation System)

## 1. 核心理念 (Philosophy)
传统小说结构往往受限于“卷-章”的物理划分，但真正的叙事节奏（Story Arc）是流动的。本系统的目标是**超越物理章节**，通过多维数据分析，自动识别并可视化“逻辑剧情段落 (Plot Segments)”。

每个段落代表一个完整的**叙事单元**（如：一场战斗、一次解谜、一段回忆），并为其生成**高层级摘要**。

## 2. 算法设计 (Algorithm Design)

### 2.1 分段信号源 (Segmentation Signals)
我们将综合以下三个维度的信号来判定“切分点”：

1.  **强度突变 (Intensity Shift)**:
    *   监控 `Intensity Score` 的导数（变化率）。
    *   **判定逻辑**: 当强度从 Low 持续跃升至 High（高潮开始），或从 High 骤降至 Low（高潮结束），极可能意味着剧情段落的切换。
    
2.  **实体共现漂移 (Entity Co-occurrence Drift)**:
    *   计算相邻章节的实体集合 Jaccard 相似度。
    *   **判定逻辑**: 如果第 N 章与第 N+1 章的主要角色集合相似度低于阈值（例如 0.3），说明场景发生了切换（如：从主角团视角切换到反派视角）。

3.  **时间/空间关键词 (Contextual Markers)**:
    *   分析 `Headline` 或首段文本。
    *   **判定逻辑**: 出现“次日”、“三年后”、“与此同时”、“另一边”等转折词。

### 2.2 聚类流程 (Clustering Process)
1.  **预处理**: 为所有章节计算特征向量 `V_i = [Intensity, Entity_Set, Time_Marker]`.
2.  **边界检测**: 遍历章节序列，计算相邻章节的“连贯性得分” `Coherence(i, i+1)`。
3.  **切分**: 当 `Coherence` 低于动态阈值时，插入“切分点”。
4.  **后处理 (合并)**:
    *   如果某段落仅包含 1 章且强度极低，尝试将其合并到前一段（避免碎片化）。
    *   确保每个段落长度在 3-10 章之间（符合阅读心理学）。

## 3. 智能摘要 (Intelligent Summarization)

对于每个生成的段落 `Segment[i]`（包含章节 $C_m$ 到 $C_n$）：
1.  **Prompt**: 输入该段落内所有章节的 `Headline` 和 `Summary`。
2.  **LLM Task**: "请将以上连续章节的摘要合并为一个连贯的剧情梗概（100字以内），并提炼一个 4-8 字的小标题。"
3.  **Output**:
    *   `Segment Title`: 例如“营救行动”、“黑客入侵”。
    *   `Segment Synopsis`: "主角团潜入敌方基地，遭遇伏击，最终在艾丽的掩护下成功撤离。"

## 4. UI/UX 设计 (Interface)

### 4.1 概览页增强 (OverviewGrid Enhancement)
在现有的“卷视图”内部，增加一层**“剧情容器”**：

*   **视觉分组**:
    *   原本平铺的章节卡片，现在被包裹在若干个**浅色背景的圆角矩形容器**中。
    *   容器之间有明显的间距，代表剧情的“呼吸感”。
    
*   **段落头部 (Segment Header)**:
    *   容器左上角显示 **LLM 生成的小标题**（如“营救行动”）。
    *   旁边显示该段落的**平均强度指示器**（色点）。
    *   Hover 标题时，Tooltip 显示段落梗概。

*   **段落摘要卡片 (Optional)**:
    *   在每个容器的开头，插入一张特殊的“宽卡片”或“引导卡”，显示该段落的总结。

### 4.2 时间轴映射 (Timeline Mapping)
侧边栏的时间轴也同步更新：
*   在微型色块之间增加微小的**垂直间隙**，对应右侧的段落切分。
*   Hover 某个区域时，高亮整个段落。

## 5. 数据结构 (Data Structure)

```typescript
interface PlotSegment {
  id: string;
  volume_title: string; // 所属物理卷
  title: string;        // LLM 生成的段落标题
  synopsis: string;     // LLM 生成的段落梗概
  chapter_ids: string[]; // 包含的章节 ID 列表
  avg_intensity: number;
}

// Store State
segments: PlotSegment[];
```

## 6. 实施路线图 (Roadmap)

1.  **Phase 1: 启发式分段 (Heuristic Segmentation)**
    *   先不依赖 LLM，仅基于“实体相似度”和“强度突变”进行规则切分。
    *   在前端即时计算，验证切分效果是否符合直觉。

2.  **Phase 2: UI 容器化 (UI Containerization)**
    *   改造 `OverviewGrid`，支持渲染嵌套结构。

3.  **Phase 3: LLM 摘要增强 (LLM Enrichment)**
    *   后端新增 `generate_segment_summary` 任务。
    *   将分段结果持久化到数据库。
