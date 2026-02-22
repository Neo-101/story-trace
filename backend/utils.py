from pathlib import Path
import json
from core.config import settings

def get_novel_path(novel_name: str, file_hash: str, timestamp: str) -> str:
    """Returns the absolute path to the run directory"""
    return str(settings.OUTPUT_DIR / novel_name / file_hash / timestamp)

def resolve_run_path(novel_name: str, file_hash: str, timestamp: str) -> str:
    """解析实际的运行路径（处理缓存链接）"""
    base_path = Path(get_novel_path(novel_name, file_hash, timestamp))
    ref_file = base_path / "ref_link.json"
    
    if ref_file.exists():
        try:
            with open(ref_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                target_ts = data.get("target_timestamp")
                if target_ts:
                    return get_novel_path(novel_name, file_hash, target_ts)
        except:
            pass
    return str(base_path)

def get_output_dir() -> str:
    return str(settings.OUTPUT_DIR)
