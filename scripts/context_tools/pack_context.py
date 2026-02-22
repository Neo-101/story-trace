import os
import argparse
from pathlib import Path
from typing import List, Set

# --- Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE = PROJECT_ROOT / "docs" / "project_stats" / "project_context_packed.txt"
CONTEXT_IGNORE_FILE = Path(__file__).parent / ".contextignore"

# Default Ignore List (Fallbacks)
DEFAULT_IGNORE_DIRS = {
    ".git", ".idea", ".vscode", "__pycache__", "node_modules", 
    "venv", "env", "output", "dist", "build", "legacy_archive",
    ".pytest_cache", "coverage", "htmlcov", ".mypy_cache"
}

def load_ignore_rules() -> tuple[set, set]:
    """Load ignore rules from .contextignore or use defaults."""
    ignore_dirs = DEFAULT_IGNORE_DIRS.copy()
    ignore_files = {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
        "storytrace.db", ".DS_Store", "Thumbs.db",
        "poetry.lock", "bun.lockb"
    }
    
    if CONTEXT_IGNORE_FILE.exists():
        print(f"Loading ignore rules from {CONTEXT_IGNORE_FILE}")
        with open(CONTEXT_IGNORE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Simple heuristic: if no extension, treat as dir (imperfect but works for typical .gitignore)
                if "." in line and not line.startswith("."):
                     ignore_files.add(line)
                else:
                     ignore_dirs.add(line)
    return ignore_dirs, ignore_files

# Load Rules
EXCLUDE_DIRS, EXCLUDE_FILES = load_ignore_rules()

# Only include these source code extensions
INCLUDE_EXTENSIONS = {
    ".py", ".ts", ".vue", ".js", ".json" # Core logic files
}

def is_excluded(path: Path) -> bool:
    """Check if path should be excluded based on rules."""
    # Check directories in path
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
            
    # Check filename
    if path.name in EXCLUDE_FILES:
        return True
        
    # Check extension (Allow listed extensions OR generic files like Dockerfile)
    if path.suffix not in INCLUDE_EXTENSIONS and path.name != "Dockerfile":
        return True
        
    return False

def pack_project():
    """Scan and pack project content into a single file."""
    print(f"Packing project context from: {PROJECT_ROOT}")
    print(f"Excluding: {', '.join(sorted(list(EXCLUDE_DIRS)))}")
    
    packed_content = []
    file_count = 0
    total_lines = 0
    
    # Header
    packed_content.append(f"# Project Context Pack")
    packed_content.append(f"# Generated for LLM Context Window Optimization")
    packed_content.append(f"# Focus: Core Architecture (Backend + Core Logic)")
    packed_content.append(f"# Root: {PROJECT_ROOT.name}")
    packed_content.append("-" * 40 + "\n")

    # Walk through directory
    # Use sorted walk for deterministic output
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Modify dirs in-place to skip excluded directories during traversal
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        
        # Sort for consistency
        dirs.sort()
        files.sort()
        
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(PROJECT_ROOT)
            
            if is_excluded(rel_path):
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                # Add file marker
                packed_content.append(f"\n{'='*20} FILE: {rel_path} {'='*20}\n")
                packed_content.append(content)
                
                file_count += 1
                total_lines += len(content.splitlines())
                print(f"Packed: {rel_path}")
                
            except Exception as e:
                print(f"Error reading {rel_path}: {e}")

    # Write to output file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(packed_content))
        
    print(f"\nDone! Packed {file_count} files ({total_lines} lines) into {OUTPUT_FILE}")

if __name__ == "__main__":
    pack_project()
