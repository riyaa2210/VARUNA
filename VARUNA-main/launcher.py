#!/usr/bin/env python
"""
Direct video analysis launcher
Runs YOLO detection on video.mp4 input
"""
import os
import sys

# Change to SIH directory
sih_dir = r"C:\Users\sharm\Downloads\SIH-20251206T045351Z-3-001\SIH-20251206T045351Z-3-001\SIH"
os.chdir(sih_dir)
sys.path.insert(0, sih_dir)

# Import and run main
if __name__ == "__main__":
    import main  # This will execute the module if __name__ == "__main__"
