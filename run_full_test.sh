#!/bin/bash
# Complete Autonomous SLAM + Navigation Test
# Runs all terminals with proper timing and feedback

set -e

REPO_DIR="$HOME/Documents/GitHub/hws_repo"
cd "$REPO_DIR"

source /opt/ros/humble/setup.bash
source install/setup.bash

echo "=================================================="
echo "  TEAM 14 - AUTONOMOUS SLAM + NAV2 TEST"
echo "=================================================="
echo ""

# Terminal 1: SLAM + RViz
echo "[1/3] Starting SLAM + Gazebo + RViz..."
ros2 launch robot_project autonomous_slam.launch.py \
    slam_mode:=rgbd \
    run_explorer:=false \
    use_rviz:=true &
SLAM_PID=$!

echo "      ⏳ Waiting 75 seconds for SLAM to stabilize..."
sleep 75

# Terminal 2: Nav2
echo ""
echo "[2/3] Starting Nav2 navigation stack..."
ros2 launch robot_project navigation.launch.py &
NAV2_PID=$!

echo "      ⏳ Waiting 40 seconds for Nav2 to initialize..."
sleep 40

# Terminal 3: Waypoint Navigator
echo ""
echo "[3/3] Starting random waypoint navigation..."
echo "      Robot should now autonomously navigate to waypoints!"
echo ""
echo "=================================================="
echo "  NAVIGATION STARTED - Check RViz for robot motion"
echo "=================================================="
echo ""

ros2 run robot_project random_waypoint_nav \
    --ros-args \
    -p goal_timeout:=120.0 \
    -p mode:=coverage \
    -p num_waypoints:=10

# Cleanup
echo ""
echo "=================================================="
echo "  TEST COMPLETE"
echo "=================================================="
echo ""
echo "Saving SLAM data..."
python3 src/robot_project/robot_project/save_slam_data.py

echo "Files saved to: project/results/data/screenshots/"
