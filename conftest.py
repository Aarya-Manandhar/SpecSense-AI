import sys
from pathlib import Path

# Add backend directory and workspace root to sys.path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"

for directory in (backend_dir, root_dir):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
