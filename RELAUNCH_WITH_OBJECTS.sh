#!/bin/bash

# Quick Relaunch Script with Objects in World

echo "═══════════════════════════════════════════════════════"
echo "  HW2 Relaunch with Colored Objects"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "This will launch Gazebo with:"
echo "  - Red Box (2m ahead)"
echo "  - Green Cylinder (left front)"
echo "  - Blue Box (left rear)"
echo "  - Yellow Sphere (right rear)"
echo ""
echo "IMPORTANT:"
echo "  1. Close current Gazebo first (Ctrl+C in terminal)"
echo "  2. Keep RViz, Camera, and IMU Plot open"
echo "  3. Run this script"
echo ""
echo "Press Enter to continue..."
read

# Kill any existing Gazebo processes
pkill -9 gzserver gzclient

echo "Waiting 3 seconds..."
sleep 3

# Source ROS
source /opt/ros/humble/setup.bash
source ~/Documents/GitHub/hws_repo/install/setup.bash

# Launch with custom world
echo "Launching Gazebo with objects..."
ros2 launch robot_hw1 hw2.launch.py use_rviz:=false world:=$(pwd)/worlds/hw2_world.world
