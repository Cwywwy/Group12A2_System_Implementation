# -*- coding: utf-8 -*-
"""
run_01_sample.py
Author: Group12A2 DSW Team
Purpose: Entry point that rebuilds the manufacturing sample frame and checklist.
Module: scripts

Revision History
-----------------
2026-11-05  initial version.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sample_frame import main  # noqa: E402

if __name__ == "__main__":
    main()
