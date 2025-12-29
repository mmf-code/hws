#!/bin/bash

# Team 14 Final Demo - Random Waypoint Navigation
# Completes KON414E Requirement 7:
# "Use 2D projection of the computed 3D map for navigation.
#  Assign random points in the environment to move the robot autonomously"

set -e

echo "=========================================="
echo "Team 14 - Final Demo Setup"
echo "=========================================="
echo ""

# Check if map exists
MAP_FILE="$HOME/.ros/rtabmap.db"
if [ ! -f "$MAP_FILE" ]; then
    echo "ERROR: Map database not found at $MAP_FILE"
    echo ""
    echo "First, create a map by running:"
    echo "  ros2 launch robot_project optimized_slam.launch.py"
    echo ""
    exit 1
fi

MAP_SIZE=$(du -h $MAP_FILE | cut -f1)
echo "MAP FOUND: $MAP_FILE"
echo "SIZE: $MAP_SIZE"
echo ""

# Check ROS installation
if ! command -v ros2 &> /dev/null; then
    echo "ERROR: ROS 2 not found. Please source setup.bash first"
    exit 1
fi

echo "ROS 2: $(ros2 --version)"
echo ""

# Source workspace
echo "Sourcing workspace..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_ROOT="$SCRIPT_DIR/../../.."
source /opt/ros/humble/setup.bash
source "$WORKSPACE_ROOT/install/setup.bash"
echo "Workspace ready"
echo ""

echo "=========================================="
echo "Launching SLAM + Navigation Demo"
echo "=========================================="
echo ""
echo "This will:"
echo "  1. Start Gazebo with office world"
echo "  2. Spawn Pioneer 3-DX robot"
echo "  3. Load $MAP_SIZE RTAB-Map database"
echo "  4. Generate 2D projection for navigation"
echo "  5. Open RViz for visualization"
echo ""
echo "After launch (~20 sec), run in NEW TERMINAL:"
echo ""
echo "  source /opt/ros/humble/setup.bash"
echo "  source ~/Documents/GitHub/hws_repo/install/setup.bash"
echo "  ros2 run robot_project simple_goal_nav"
echo ""
echo "Press ENTER to start, Ctrl+C to cancel..."
read -r

# Launch
export ROS_DOMAIN_ID=0
ros2 launch robot_project optimized_slam.launch.py use_rviz:=true
