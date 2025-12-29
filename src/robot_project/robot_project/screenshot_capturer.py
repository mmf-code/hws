#!/usr/bin/env python3
"""
Auto Screenshot Capturer for SLAM Visualization
Captures high-quality screenshots at key moments during navigation
"""

import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

class ScreenshotCapturer:
    def __init__(self, output_dir="project/results/data/screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.capture_count = 0

    def capture_screenshot(self, name_prefix="slam"):
        """Capture high-quality screenshot using gnome-screenshot or import"""
        self.capture_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{name_prefix}_{self.capture_count}_{timestamp}.png"

        try:
            # Try gnome-screenshot first (best quality)
            cmd = ["gnome-screenshot", "-f", str(filename)]
            subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            print(f"✅ Screenshot saved: {filename}")
            return str(filename)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Fallback to ImageMagick import
                cmd = ["import", "-window", "root", str(filename)]
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
                print(f"✅ Screenshot saved (ImageMagick): {filename}")
                return str(filename)
            except Exception as e:
                print(f"❌ Screenshot failed: {e}")
                return None

    def capture_sequence(self, interval=5, duration=30):
        """Capture screenshot sequence every N seconds for M seconds"""
        end_time = time.time() + duration
        while time.time() < end_time:
            self.capture_screenshot("sequence")
            time.sleep(interval)

    def capture_rviz_view(self, view_name="initial"):
        """Capture with specific view name"""
        return self.capture_screenshot(f"rviz_{view_name}")

if __name__ == "__main__":
    capturer = ScreenshotCapturer()

    # Capture initial state
    print("[1/3] Capturing initial SLAM state...")
    capturer.capture_screenshot("slam_initial")
    time.sleep(2)

    # Capture during navigation (simulated)
    print("[2/3] Waiting for navigation...")
    time.sleep(5)
    capturer.capture_screenshot("slam_during_navigation")

    # Capture final state
    print("[3/3] Capturing final SLAM map...")
    time.sleep(2)
    capturer.capture_screenshot("slam_final")

    print(f"\n✅ All screenshots saved to: {capturer.output_dir}")
