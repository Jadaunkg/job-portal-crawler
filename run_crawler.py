#!/usr/bin/env python
"""
Crawler Runner Script
Run from project root: python run_crawler.py [command]
"""

import sys
import os
from pathlib import Path

# Add project root and src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# Change to project root for relative imports
os.chdir(project_root)

# Import after path setup
if __name__ == "__main__":
    # Import here to ensure paths are set up first
    from src.main import main
    sys.exit(main())
