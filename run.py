#!/usr/bin/env python3
"""Convenience script to run Espanded from source."""

import sys
from pathlib import Path

# Add src to path so we can import espanded
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from espanded.main import main

if __name__ == "__main__":
    main()
