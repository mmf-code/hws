#!/bin/bash

# RViz Launcher with Snap libpthread Fix
# This script forces system pthread library to avoid snap conflicts

# Source ROS
source /opt/ros/humble/setup.bash
source ~/Documents/GitHub/hws_repo/install/setup.bash

# Force system pthread library (override snap's pthread)
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0

# Also remove snap paths from LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:$//')

# Launch RViz
rviz2 -d ~/Documents/GitHub/hws_repo/install/robot_hw1/share/robot_hw1/rviz/hw2_config.rviz
