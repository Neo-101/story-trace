import re
from typing import Optional

class IdentifierGenerator:
    """
    负责全项目统一的 ID 生成逻辑。
    确保 Splitter 生成的 ID 和数据库迁移时解析的 ID 一致。
    """

    @staticmethod
    def generate_chapter_id(index: int, prefix: str = "ch") -> str:
        """
        生成标准章节 ID。
        格式: {prefix}_{index}
        例如: ch_1, vol_1_ch_5
        
        Args:
            index: 1-based index
            prefix: 前缀，默认为 'ch'
        """
        return f"{prefix}_{index}"

    @staticmethod
    def parse_chapter_index(chapter_id: str) -> Optional[int]:
        """
        从 ID 中解析出数字索引。
        例如: "ch_42" -> 42, "vol_1_ch_5" -> 5
        """
        if not chapter_id:
            return None
            
        # 尝试匹配最后的数字部分
        # 匹配 _(\d+)$
        match = re.search(r'_(\d+)$', chapter_id)
        if match:
            return int(match.group(1))
            
        return None

    @staticmethod
    def generate_volume_id(index: int) -> str:
        """生成分卷 ID"""
        return f"vol_{index}"
    
    @staticmethod
    def generate_batch_id(start: int, end: int) -> str:
        """生成批次 ID"""
        return f"batch_{start}_{end}"
