import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def get_novel_path(novel_name: str, file_hash: str, timestamp: str):
    return os.path.join(OUTPUT_DIR, novel_name, file_hash, timestamp)

def resolve_run_path(novel_name: str, file_hash: str, timestamp: str):
    """解析实际的运行路径（处理缓存链接）"""
    base_path = get_novel_path(novel_name, file_hash, timestamp)
    ref_file = os.path.join(base_path, "ref_link.json")
    if os.path.exists(ref_file):
        try:
            with open(ref_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                target_ts = data.get("target_timestamp")
                if target_ts:
                    return get_novel_path(novel_name, file_hash, target_ts)
        except:
            pass
    return base_path

def get_output_dir():
    return OUTPUT_DIR
