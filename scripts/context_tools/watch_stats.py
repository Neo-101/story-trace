import os
import json
import time
import sys
import tiktoken
from pathlib import Path
from typing import Dict, List, Any
from watchfiles import watch

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "project_stats"

IGNORE_DIRS = {
    ".git", ".idea", ".vscode", "__pycache__", "node_modules", 
    "venv", "env", "output", "dist", "build", "legacy_archive",
    ".pytest_cache", "coverage", "htmlcov", ".mypy_cache",
    "docs" # Ignore docs to prevent loop
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
    "storytrace.db", ".DS_Store", "Thumbs.db",
    "poetry.lock", "bun.lockb"
}
# Only count code lines for these extensions
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".vue", ".html", ".css", ".scss", ".json", 
    ".md", ".yaml", ".yml", ".sh", ".bat", ".ps1"
}

# Initialize tokenizer (cl100k_base is used by GPT-4/3.5)
enc = tiktoken.get_encoding("cl100k_base")

def count_stats(file_path: Path) -> tuple[int, int]:
    """Count non-empty lines and tokens in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        lines = sum(1 for line in content.splitlines() if line.strip())
        tokens = len(enc.encode(content))
        return lines, tokens
    except Exception:
        return 0, 0

def scan_directory(path: Path) -> Dict[str, Any]:
    """Recursively scan directory and build tree structure with stats."""
    stats = {
        "name": path.name,
        "type": "directory",
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "total_lines": 0,
        "total_tokens": 0,
        "file_count": 0,
        "children": []
    }

    try:
        # Sort for consistent output
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        
        for item in items:
            # Skip ignored
            if item.name in IGNORE_DIRS or item.name in IGNORE_FILES:
                continue
            if item.name.startswith("."): # Skip hidden files/dirs by default unless explicitly allowed
                continue

            if item.is_dir():
                child_stats = scan_directory(item)
                # Only include directories that have content
                if child_stats["total_lines"] > 0 or child_stats["file_count"] > 0:
                    stats["children"].append(child_stats)
                    stats["total_lines"] += child_stats["total_lines"]
                    stats["total_tokens"] += child_stats["total_tokens"]
                    stats["file_count"] += child_stats["file_count"]
            
            elif item.is_file():
                if item.suffix in CODE_EXTENSIONS or item.name == "Dockerfile":
                    lines, tokens = count_stats(item)
                    stats["total_lines"] += lines
                    stats["total_tokens"] += tokens
                    stats["file_count"] += 1
                    stats["children"].append({
                        "name": item.name,
                        "type": "file",
                        "path": str(item.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                        "lines": lines,
                        "tokens": tokens
                    })
    except PermissionError:
        pass

    return stats

def generate_human_report(stats: Dict[str, Any], level: int = 0) -> str:
    """Generate a human-readable tree view."""
    indent = "  " * level
    icon = "📁" if stats.get("type") == "directory" else "📄"
    
    if stats.get("type") == "directory":
        line_count = stats.get("total_lines", 0)
        token_count = stats.get("total_tokens", 0)
    else:
        line_count = stats.get("lines", 0)
        token_count = stats.get("tokens", 0)
    
    # Format tokens (e.g., 1.2k)
    if token_count > 1000:
        token_str = f"{token_count/1000:.1f}k"
    else:
        token_str = str(token_count)
        
    line_info = f" ({line_count} lines, {token_str} tokens)"
    
    output = f"{indent}{icon} {stats['name']}{line_info}\n"
    
    if "children" in stats:
        for child in stats["children"]:
            output += generate_human_report(child, level + 1)
            
    return output

def generate_llm_json(stats: Dict[str, Any], include_tokens: bool = False) -> Dict[str, Any]:
    """Generate a compact JSON for LLM consumption."""
    node = {
        "name": stats["name"],
        "lines": stats.get("lines", stats.get("total_lines", 0)),
    }
    
    if include_tokens:
        node["tokens"] = stats.get("tokens", stats.get("total_tokens", 0))
    
    if stats["type"] == "directory":
        node["files"] = stats["file_count"]
        # Only include children if it's a directory
        node["children"] = [generate_llm_json(child, include_tokens) for child in stats["children"]]
        
    return node

def run_scan():
    """Execute scan and generate reports"""
    print(f"[{time.strftime('%H:%M:%S')}] Scanning project...")
    project_stats = scan_directory(PROJECT_ROOT)
    
    # 1. Human Report
    human_report = f"# Project Statistics: {PROJECT_ROOT.name}\n"
    human_report += f"Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    human_report += f"Total Files: {project_stats['file_count']}\n"
    human_report += f"Total Lines: {project_stats['total_lines']}\n"
    human_report += f"Total Tokens: {project_stats['total_tokens']}\n"
    human_report += "=" * 40 + "\n\n"
    human_report += generate_human_report(project_stats)
    
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_DIR / "project_stats_human.txt", "w", encoding="utf-8") as f:
            f.write(human_report)
        
        # 2. LLM Report (Lines Only - Legacy)
        llm_report = {
            "project": PROJECT_ROOT.name,
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            "summary": {
                "total_files": project_stats['file_count'],
                "total_lines": project_stats['total_lines'],
                "total_tokens": project_stats['total_tokens']
            },
            "structure": generate_llm_json(project_stats, include_tokens=False)
        }
        
        with open(OUTPUT_DIR / "project_stats_llm.json", "w", encoding="utf-8") as f:
            json.dump(llm_report, f, indent=2)

        # 3. Token Report (New!)
        token_report = {
            "project": PROJECT_ROOT.name,
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S'),
            "summary": {
                "total_files": project_stats['file_count'],
                "total_tokens": project_stats['total_tokens'],
                "tokenizer": "cl100k_base (OpenAI)"
            },
            "structure": generate_llm_json(project_stats, include_tokens=True)
        }
        
        with open(OUTPUT_DIR / "project_stats_tokens.json", "w", encoding="utf-8") as f:
            json.dump(token_report, f, indent=2)
            
        print(f"[{time.strftime('%H:%M:%S')}] Reports updated (Human + LLM + Tokens).")
    except Exception as e:
        print(f"Error writing reports: {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        run_scan()
        return

    print("=== StoryTrace Stats Watcher (Token Enhanced) ===")
    print("Watching for file changes (Ctrl+C to stop)...")
    print(f"Ignoring: {', '.join(list(IGNORE_DIRS)[:5])}...")
    
    # Initial run
    run_scan()
    
    # Watch loop
    try:
        for changes in watch('.', ignore_permission_denied=True):
            valid_changes = False
            for change_type, path in changes:
                p = Path(path)
                if p.name in IGNORE_FILES:
                    continue
                # Output dir and docs dir (where reports are) should be ignored
                if "output" in p.parts or ".git" in p.parts or "node_modules" in p.parts or "docs" in p.parts:
                    continue
                    
                valid_changes = True
                break
            
            if valid_changes:
                run_scan()
                
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
