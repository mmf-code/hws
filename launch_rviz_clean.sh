#!/bin/bash

# RViz Launcher - Start clean without config (to test if config file is the issue)

# Source ROS
source /opt/ros/humble/setup.bash
source ~/Documents/GitHub/hws_repo/install/setup.bash

# Force system pthread library
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0

# Remove snap paths
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:$//')

# Launch RViz WITHOUT config (start fresh)
echo "Starting RViz without config file..."
echo "If this works, manually add displays in RViz GUI:"
echo "  1. Add → RobotModel"
echo "  2. Add → Camera → Topic: /camera/rgbd_camera/image_raw"
echo "  3. Add → PointCloud2 → Topic: /camera/rgbd_camera/points"
echo "  4. Add → Odometry → Topic: /odom"
echo "  5. Set Fixed Frame: odom"
echo ""
rviz2
