#!/bin/bash

# Simple Camera Viewer (Alternative to RViz image panel)

# Source ROS first
source /opt/ros/humble/setup.bash
source ~/Documents/GitHub/hws_repo/install/setup.bash

echo "═══════════════════════════════════════════"
echo "  Camera Image Viewer"
echo "═══════════════════════════════════════════"
echo ""
echo "Opening RGB camera view..."
echo "Topic: /camera/rgb/image_raw"
echo ""
echo "Press Ctrl+C to close"
echo ""

# Force system pthread library (same fix as RViz)
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0

# Also remove snap paths from LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:$//')

# Launch rqt_image_view with full path
/opt/ros/humble/lib/rqt_image_view/rqt_image_view /camera/rgb/image_raw
