import sys
from pathlib import Path

# Add backend directory and workspace root to sys.path so app and backend packages resolve seamlessly
backend_dir = Path(__file__).resolve().parents[1]
repo_root = Path(__file__).resolve().parents[2]

for directory in (backend_dir, repo_root):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
