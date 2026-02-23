import os
import json
from pathlib import Path
from typing import Dict, List, Any

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "project_stats"

IGNORE_DIRS = {
    ".git", ".idea", ".vscode", "__pycache__", "node_modules", 
    "venv", "env", "output", "dist", "build", "legacy_archive",
    ".pytest_cache", "coverage", "htmlcov", ".mypy_cache",
    "cache" # Ignore cache directory
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

def count_lines(file_path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0

def scan_directory(path: Path) -> Dict[str, Any]:
    """Recursively scan directory and build tree structure with stats."""
    stats = {
        "name": path.name,
        "type": "directory",
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "total_lines": 0,
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
                    stats["file_count"] += child_stats["file_count"]
            
            elif item.is_file():
                if item.suffix in CODE_EXTENSIONS or item.name == "Dockerfile":
                    lines = count_lines(item)
                    stats["total_lines"] += lines
                    stats["file_count"] += 1
                    stats["children"].append({
                        "name": item.name,
                        "type": "file",
                        "path": str(item.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                        "lines": lines
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
    else:
        line_count = stats.get("lines", 0)
    
    line_info = f" ({line_count} lines)"
    
    output = f"{indent}{icon} {stats['name']}{line_info}\n"
    
    if "children" in stats:
        for child in stats["children"]:
            output += generate_human_report(child, level + 1)
            
    return output

def generate_llm_json(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a compact JSON for LLM consumption."""
    # Simplified structure for LLM: path -> lines
    # Flattening might be better for LLM token efficiency, but tree preserves context.
    # Let's keep a simplified tree.
    
    node = {
        "name": stats["name"],
        "lines": stats.get("lines", stats.get("total_lines", 0)),
    }
    
    if stats["type"] == "directory":
        node["files"] = stats["file_count"]
        # Only include children if it's a directory
        node["children"] = [generate_llm_json(child) for child in stats["children"]]
        
    return node

def main():
    print("Scanning project...")
    project_stats = scan_directory(PROJECT_ROOT)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Human Report
    human_report = f"# Project Statistics: {PROJECT_ROOT.name}\n"
    human_report += f"Total Files: {project_stats['file_count']}\n"
    human_report += f"Total Lines of Code: {project_stats['total_lines']}\n"
    human_report += "=" * 40 + "\n\n"
    human_report += generate_human_report(project_stats)
    
    human_report_path = OUTPUT_DIR / "project_stats_human.txt"
    with open(human_report_path, "w", encoding="utf-8") as f:
        f.write(human_report)
    
    # 2. LLM Report (JSON)
    llm_report = {
        "project": PROJECT_ROOT.name,
        "summary": {
            "total_files": project_stats['file_count'],
            "total_lines": project_stats['total_lines'],
            "description": "Line counts exclude empty lines. Ignored dirs: node_modules, output, .git, etc."
        },
        "structure": generate_llm_json(project_stats)
    }
    
    llm_report_path = OUTPUT_DIR / "project_stats_llm.json"
    with open(llm_report_path, "w", encoding="utf-8") as f:
        json.dump(llm_report, f, indent=2)

    print(f"Done.")
    print(f"Human Report: {human_report_path} ({project_stats['total_lines']} lines)")
    print(f"LLM Report:   {llm_report_path}")

if __name__ == "__main__":
    main()
