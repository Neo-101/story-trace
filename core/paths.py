import os
from pathlib import Path
from core.config import settings

class PathManager:
    """
    统一管理文件系统路径结构。
    """
    
    @staticmethod
    def get_output_root() -> Path:
        """获取输出根目录"""
        return settings.OUTPUT_DIR

    @staticmethod
    def get_novel_root(novel_name: str, file_hash: str) -> Path:
        """output/novel_name/hash/"""
        return PathManager.get_output_root() / novel_name / file_hash

    @staticmethod
    def get_run_dir(novel_name: str, file_hash: str, timestamp: str) -> Path:
        """output/novel_name/hash/timestamp/"""
        return PathManager.get_novel_root(novel_name, file_hash) / timestamp

    @staticmethod
    def get_cache_dir() -> Path:
        """output/.cache/"""
        return PathManager.get_output_root() / ".cache"
        
    @staticmethod
    def get_chapter_file_path(output_dir: Path, title: str, volume_title: str = None) -> Path:
        """
        根据章节信息生成文件路径。
        如果有 volume_title，则创建子目录。
        """
        # 清理非法字符
        clean_title = "".join([c for c in title if c not in r'\/:*?"<>|'])
        
        if volume_title:
            clean_vol = "".join([c for c in volume_title if c not in r'\/:*?"<>|'])
            return output_dir / clean_vol / f"{clean_title}.txt"
        else:
            return output_dir / f"{clean_title}.txt"
