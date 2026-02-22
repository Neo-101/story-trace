import argparse
import sys
import os
import shutil
import subprocess
from pathlib import Path
from core.config import settings
from core.db.engine import create_db_and_tables

def clean_cache():
    """清理缓存目录"""
    cache_dir = settings.OUTPUT_DIR / ".cache"
    if cache_dir.exists():
        print(f"Removing cache: {cache_dir}")
        shutil.rmtree(cache_dir)
        print("Done.")
    else:
        print("Cache directory does not exist.")

def clean_outputs():
    """清理所有输出文件"""
    output_dir = settings.OUTPUT_DIR
    if output_dir.exists():
        response = input(f"WARNING: This will delete ALL data in {output_dir}. Are you sure? (y/N): ")
        if response.lower() == 'y':
            for item in output_dir.iterdir():
                if item.name == ".gitkeep":
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            print("Done.")
    else:
        print("Output directory does not exist.")

def reset_db():
    """重置数据库"""
    db_path = Path("storytrace.db") # TODO: parse from settings properly if needed
    if db_path.exists():
        print(f"Removing database: {db_path}")
        db_path.unlink()
    
    print("Creating new database...")
    create_db_and_tables()
    print("Done.")

def check_env():
    """环境自检"""
    print("=== Environment Check ===")
    print(f"Base Dir: {settings.BASE_DIR}")
    print(f"Output Dir: {settings.OUTPUT_DIR}")
    print(f"DB Path: {settings.database_path}")
    print(f"OpenRouter Key: {'Set' if settings.OPENROUTER_API_KEY else 'Not Set'}")
    
    # Check dependencies
    try:
        import fastapi
        print("FastAPI: Installed")
    except ImportError:
        print("FastAPI: Missing")
        
    try:
        import sqlmodel
        print("SQLModel: Installed")
    except ImportError:
        print("SQLModel: Missing")

    print("=== End Check ===")

def context_tools(tool_name: str):
    """运行 Context 工具"""
    script_map = {
        "watch": "scripts/context_tools/watch_stats.py",
        "pack": "scripts/context_tools/pack_context.py",
        "stats": "scripts/context_tools/generate_stats.py"
    }
    
    script_path = script_map.get(tool_name)
    if not script_path:
        print(f"Unknown context tool: {tool_name}")
        print(f"Available tools: {', '.join(script_map.keys())}")
        return

    print(f"Running {tool_name}...")
    subprocess.run([sys.executable, script_path])

def main():
    parser = argparse.ArgumentParser(description='StoryTrace Management Script')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    subparsers.add_parser('clean-cache', help='Clear the .cache directory')
    subparsers.add_parser('clean-all', help='Clear ALL outputs')
    subparsers.add_parser('reset-db', help='Delete and recreate SQLite database')
    subparsers.add_parser('check', help='Check environment configuration')
    
    context_parser = subparsers.add_parser('context', help='Manage project context for LLMs')
    context_parser.add_argument('tool', choices=['watch', 'pack', 'stats'], help='Tool to run (watch, pack, stats)')
    
    args = parser.parse_args()
    
    if args.command == 'clean-cache':
        clean_cache()
    elif args.command == 'clean-all':
        clean_outputs()
    elif args.command == 'reset-db':
        reset_db()
    elif args.command == 'check':
        check_env()
    elif args.command == 'context':
        context_tools(args.tool)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
