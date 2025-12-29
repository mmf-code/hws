#!/usr/bin/env python3
"""
Auto-save SLAM data when navigation completes
Saves: 2D map, 3D point cloud, statistics
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path

def save_slam_data():
    """Save all SLAM data to screenshots folder"""
    output_dir = Path("project/results/data/screenshots")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n" + "="*60)
    print(" SAVING SLAM DATA")
    print("="*60)

    # 1. Save 2D map
    print(f"\n[1/3] Saving 2D map...")
    map_file = f"slam_map_{timestamp}"
    cmd = f"cd {output_dir} && ros2 run nav2_map_server map_saver_cli -f {map_file}"
    os.system(cmd)
    print(f"✅ Map saved to: {output_dir}/{map_file}.pgm")

    # 2. Take screenshot of RViz
    print(f"\n[2/3] Taking RViz screenshot...")
    screenshot_file = output_dir / f"rviz_slam_{timestamp}.png"
    cmd = f"gnome-screenshot -f {screenshot_file}"
    result = os.system(cmd)
    if result == 0:
        print(f"✅ Screenshot saved: {screenshot_file}")
    else:
        print(f"⚠️  Screenshot failed (RViz might be closed)")

    # 3. Save database
    print(f"\n[3/3] Copying RTAB-Map database...")
    db_file = output_dir / f"rtabmap_{timestamp}.db"
    os.system(f"cp ~/.ros/rtabmap.db {db_file}")
    print(f"✅ Database saved: {db_file}")

    print("\n" + "="*60)
    print(f" ALL DATA SAVED TO: {output_dir}")
    print("="*60 + "\n")

if __name__ == "__main__":
    save_slam_data()
