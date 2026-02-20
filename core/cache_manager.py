import os
import json
import hashlib
from typing import Dict, Optional, List
from data_protocol.models import ChapterSummary

class CacheManager:
    """
    负责章节级别的缓存管理。
    缓存键 (Key) 由以下因素决定：
    1. 章节内容哈希 (Content Hash)
    2. Prompt 哈希 (Prompt Hash)
    3. 模型配置哈希 (Model Config Hash)
    """

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _calculate_key(self, content: str, prompt_hash: str, model_config: Dict) -> str:
        """计算缓存唯一键"""
        # 1. Content Hash
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # 2. Model Config Hash (ensure consistent ordering)
        config_str = json.dumps(model_config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode('utf-8')).hexdigest()

        # Combine
        combined = f"{content_hash}_{prompt_hash}_{config_hash}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    def get_cached_summary(self, content: str, prompt_hash: str, model_config: Dict) -> Optional[ChapterSummary]:
        """尝试获取缓存的总结"""
        key = self._calculate_key(content, prompt_hash, model_config)
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return ChapterSummary(**data)
            except Exception as e:
                print(f"[Cache] Error reading cache {key}: {e}")
                return None
        return None

    def save_summary(self, content: str, prompt_hash: str, model_config: Dict, summary: ChapterSummary):
        """保存总结到缓存"""
        key = self._calculate_key(content, prompt_hash, model_config)
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                # model_dump is Pydantic v2, dict() is v1. Use model_dump if available.
                data = summary.model_dump() if hasattr(summary, 'model_dump') else summary.dict()
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Cache] Error writing cache {key}: {e}")
