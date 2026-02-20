import os
import json
import re
from typing import List, Dict, Optional
from data_protocol.models import ChapterSummary

class ResultMerger:
    """
    负责将不同时间戳运行的结果进行合并 (Best-Effort Merging)。
    """
    
    @staticmethod
    def _extract_chapter_number(chapter_id: str) -> float:
        """从 chapter_id 提取数字用于排序 (例如 'ch_10' -> 10.0)"""
        if not chapter_id:
            return 0.0
        
        # 尝试提取数字
        match = re.search(r'(\d+(\.\d+)?)', chapter_id)
        if match:
            return float(match.group(1))
        return 0.0

    def merge_summaries(self, run_path: str) -> List[ChapterSummary]:
        """
        加载指定 run_path 的 summary，并尝试从同级目录的其他 run 中补全缺失章节。
        
        Args:
            run_path: 当前选中的运行结果目录 (例如 .../20240220_120000)
            
        Returns:
            合并后的 ChapterSummary 列表，按章节号排序。
        """
        base_summaries = []
        
        # 1. 加载 Base Run (当前选中的)
        base_file = os.path.join(run_path, "summaries.json")
        if os.path.exists(base_file):
            try:
                with open(base_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        try:
                            # 兼容旧数据: 确保必要字段存在
                            if "entities" not in item: item["entities"] = []
                            if "relationships" not in item: item["relationships"] = []
                            base_summaries.append(ChapterSummary(**item))
                        except Exception as e:
                            print(f"Skipping malformed summary in base run: {e}")
            except Exception as e:
                print(f"Error loading base run: {e}")
        
        # 建立 map: chapter_id -> summary
        # 优先信赖当前选中的 run
        merged_map: Dict[str, ChapterSummary] = {}
        for s in base_summaries:
            merged_map[s.chapter_id] = s
            
        print(f"DEBUG: Base run has {len(merged_map)} chapters.")

        # 2. 扫描同级目录 (Sibling Runs)
        parent_dir = os.path.dirname(run_path) # .../file_hash/
        if not os.path.exists(parent_dir):
            return base_summaries
            
        # 获取所有 timestamp 目录
        all_runs = []
        for d in os.listdir(parent_dir):
            full_path = os.path.join(parent_dir, d)
            if os.path.isdir(full_path) and full_path != run_path: # 排除自己
                # 检查是否包含 summaries.json
                if os.path.exists(os.path.join(full_path, "summaries.json")):
                    all_runs.append(full_path)
        
        # 按时间倒序排序 (优先使用最新的其他 run)
        all_runs.sort(key=lambda x: os.path.basename(x), reverse=True)
        
        # 3. 补全缺失章节
        for other_run in all_runs:
            try:
                summary_file = os.path.join(other_run, "summaries.json")
                with open(summary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                added_count = 0
                for item in data:
                    chap_id = item.get("chapter_id")
                    if chap_id and chap_id not in merged_map:
                        try:
                            # 兼容性检查
                            if "entities" not in item: item["entities"] = []
                            if "relationships" not in item: item["relationships"] = []
                            
                            summary = ChapterSummary(**item)
                            merged_map[chap_id] = summary
                            added_count += 1
                        except Exception:
                            continue
                
                if added_count > 0:
                    print(f"DEBUG: Merged {added_count} chapters from {os.path.basename(other_run)}")
                    
            except Exception as e:
                print(f"Error reading sibling run {os.path.basename(other_run)}: {e}")
                continue

        # 4. 排序并返回
        result_list = list(merged_map.values())
        
        # 按章节号排序
        result_list.sort(key=lambda x: self._extract_chapter_number(x.chapter_id))
        
        print(f"DEBUG: Final merged result has {len(result_list)} chapters.")
        return result_list
