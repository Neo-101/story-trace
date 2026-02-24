import json
import os
from typing import List, Dict, Tuple
from collections import defaultdict, Counter
import zhconv
from data_protocol.models import ChapterSummary, Entity, AggregatedEntity, AggregatedRelationship, ExtendedAggregatedEntity, ConceptStage
from core.world_builder.concept_aggregator import ConceptAggregator

class EntityAggregator:
    """
    实体与关系聚合器 (World Builder)
    负责将分散在各个章节中的实体和关系信息汇总成全局档案。
    """

    def __init__(self, alias_file=None):
        self.aliases = self._load_aliases(alias_file)
        self.concept_aggregator = ConceptAggregator()

    def _load_aliases(self, alias_file):
        """加载别名配置文件"""
        if not alias_file:
            # 默认路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            alias_file = os.path.join(base_dir, "config", "aliases.json")
        
        if os.path.exists(alias_file):
            try:
                with open(alias_file, 'r', encoding='utf-8') as f:
                    print(f"DEBUG: Loaded aliases from {alias_file}")
                    return json.load(f)
            except Exception as e:
                print(f"WARNING: Failed to load aliases from {alias_file}: {e}")
                return {}
        return {}

    def _normalize_text(self, text: str) -> str:
        """
        标准化文本：去除首尾空格，应用别名映射，并转为简体中文。
        解决繁简混杂及别名导致同一实体被识别为两个节点的问题。
        """
        if not text:
            return ""
        
        text = text.strip()
        
        # 1. 应用别名映射 (在转简体之前还是之后？建议之前，如果别名表里的key也是原文形式)
        # 但为了稳健，先转简体再查别名？或者查两次？
        # 假设 aliases.json 中的 key 已经尽可能涵盖了常见形式。
        # 策略：先查一次 -> 转简体 -> 再查一次 (防止 alias key 是简体的)
        
        if text in self.aliases:
            text = self.aliases[text]
            
        text = zhconv.convert(text, 'zh-cn')
        
        if text in self.aliases:
            text = self.aliases[text]
            
        return text

    def aggregate_entities(self, summaries: List[ChapterSummary]) -> List[ExtendedAggregatedEntity]:
        """
        聚合所有章节的实体。
        
        Args:
            summaries: 章节总结列表

        Returns:
            List[ExtendedAggregatedEntity]: 聚合后的全局实体列表，按出现频率降序排列。
        """
        # Key: name (normalized), Value: dict to accumulate data
        # Fix: Group by name only, not (name, type), to prevent duplicate nodes with same ID but different types
        entity_map: Dict[str, Dict] = defaultdict(lambda: {
            "name": "",
            "types": Counter(), # Track frequency of each type
            "descriptions": [],
            "history": [],
            "chapter_ids": set(),
            "count": 0,
            "concept_evolution_raw": [] # List of (chapter_index, ConceptStage)
        })

        for summary in summaries:
            # Try to extract chapter index from summary if available
            # Note: summary object might not have chapter_index if it's the Pydantic model
            # But usually it comes from DB conversion which might attach it?
            # Actually ChapterSummary model doesn't have chapter_index.
            # We need to rely on the order or parse it from ID?
            # The summaries passed here are usually converted from DB chapters which have index.
            # Let's assume summaries are passed in order, or we can parse chapter_id.
            
            # Hack: Try to parse index from chapter_id or title if needed for sorting
            # But concept_aggregator needs (index, stage).
            # If we don't have index, we can use a counter if summaries are sorted.
            # But better to use chapter_id if it contains index.
            pass
            
            if not summary.entities:
                continue
                
            for entity in summary.entities:
                # 标准化处理：去除首尾空格，转简体，应用别名
                name = self._normalize_text(entity.name)
                type_ = entity.type.strip()
                
                if not name:
                    continue

                # Key is now just the name
                key = name
                entry = entity_map[key]
                
                if not entry["name"]:
                    entry["name"] = name
                
                # Accumulate type
                if type_:
                    entry["types"][type_] += 1
                
                if entity.description:
                    entry["descriptions"].append(entity.description)
                    entry["history"].append({
                        "chapter_id": str(summary.chapter_id).strip(),
                        "content": entity.description
                    })
                
                entry["chapter_ids"].add(str(summary.chapter_id).strip())
                entry["count"] += 1

                # Module 2: Concept Evolution
                # Check if entity has concept_evolution field (it might be in extra fields or attached dynamically)
                if hasattr(entity, 'concept_evolution') and entity.concept_evolution:
                    # We need a chapter index. 
                    idx = 0
                    
                    if hasattr(summary, 'chapter_index') and summary.chapter_index is not None:
                         idx = summary.chapter_index
                    else:
                        # Fallback: Try to get index from chapter_id string
                        import re
                        match = re.search(r'ch_(\d+)', str(summary.chapter_id))
                        if match:
                            idx = int(match.group(1))
                    
                    # Add all stages from this chapter to the raw list
                    for stage in entity.concept_evolution:
                        # Ensure stage is a ConceptStage object
                        if isinstance(stage, dict):
                            stage = ConceptStage(**stage)
                        
                        entry["concept_evolution_raw"].append((idx, stage))

        results = []
        for key, data in entity_map.items():
            # 描述合并策略：
            # 1. 优先选择最长的描述（通常包含更多细节）
            # 2. 如果没有描述，使用空字符串
            descriptions = data["descriptions"]
            final_desc = max(descriptions, key=len) if descriptions else "暂无描述"
            
            # 类型决策策略：选择出现频率最高的类型
            # 如果没有记录到类型，默认为 'Unknown'
            # data["types"] is a Counter
            most_common_type = data["types"].most_common(1)
            final_type = most_common_type[0][0] if most_common_type else "Unknown"

            # 章节列表排序
            sorted_chapters = sorted(list(data["chapter_ids"]))

            # Module 2: Aggregate Concept Evolution
            # Use the ConceptAggregator to process the raw list of (chapter_index, stage) tuples
            concept_evolution = []
            if data["concept_evolution_raw"]:
                concept_evolution = self.concept_aggregator.aggregate_evolution(data["concept_evolution_raw"])

            agg_entity = ExtendedAggregatedEntity(
                name=data["name"],
                type=final_type,
                description=final_desc,
                history=data["history"],
                chapter_ids=sorted_chapters,
                count=data["count"],
                concept_evolution=concept_evolution
            )
            results.append(agg_entity)

        # 按出现频率降序排列
        return sorted(results, key=lambda x: x.count, reverse=True)

    def aggregate_relationships(self, summaries: List[ChapterSummary]) -> List[AggregatedRelationship]:
        """
        聚合所有章节的关系。
        将多个章节中出现的 (A, B) 互动合并为一条带有时间线的全局关系。
        """
        print(f"DEBUG: Aggregating relationships for {len(summaries)} summaries")
        # Key: (source, target), Value: dict
        # 注意：需要规范化 source/target 的顺序吗？
        # 目前不需要，因为 A->B (攻击) 和 B->A (被攻击) 是不同的方向。
        # 暂时保持有向图。
        rel_map: Dict[Tuple[str, str], Dict] = defaultdict(lambda: {
            "source": "",
            "target": "",
            "timeline": [],
            "weight": 0
        })

        total_rels = 0
        
        for summary in summaries:
            if not summary.relationships:
                continue
                
            total_rels += len(summary.relationships)
            valid_rel_count = 0
            for rel in summary.relationships:
                # 标准化处理：转简体，应用别名
                s = self._normalize_text(rel.source)
                t = self._normalize_text(rel.target)
                
                # 简单的数据清洗：跳过无效数据
                if not s or not t:
                    print(f"DEBUG: Skipped invalid rel: '{rel.source}'->'{rel.target}' => '{s}'->'{t}'")
                    continue
                    
                key = (s, t)
                entry = rel_map[key]
                
                if not entry["source"]:
                    entry["source"] = s
                    entry["target"] = t
                
                valid_rel_count += 1
                
                # 添加到时间线
                entry["timeline"].append({
                    "chapter_id": str(summary.chapter_id).strip(),
                    "relation": rel.relation,
                    "description": rel.description,
                    "order": valid_rel_count  # 记录本章内的有效顺序 (1-based, 连续)
                })
                
                entry["weight"] += 1

        results = []
        for key, data in rel_map.items():
            # 按章节顺序排序时间线? 假设 summaries 已经是按顺序传入的
            # 如果不确定，可以在这里 sort timeline by chapter_id (如果 id 可排序)
            
            agg_rel = AggregatedRelationship(
                source=data["source"],
                target=data["target"],
                timeline=data["timeline"],
                weight=data["weight"]
            )
            results.append(agg_rel)

        print(f"DEBUG: Total raw rels: {total_rels}, Final unique edges: {len(results)}")
        # 按权重降序排列
        return sorted(results, key=lambda x: x.weight, reverse=True)
