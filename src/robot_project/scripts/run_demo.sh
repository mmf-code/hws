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
    echo "❌ ERROR: Map database not found at $MAP_FILE"
    echo ""
    echo "First, create a map by running:"
    echo "  ros2 launch robot_project optimized_slam.launch.py"
    echo ""
    echo "Then verify the map:"
    echo "  bash src/robot_project/scripts/check_map.sh"
    echo ""
    exit 1
fi

echo "✓ Map database found: $(du -h $MAP_FILE | cut -f1)"
echo ""

# Check ROS installation
if ! command -v ros2 &> /dev/null; then
    echo "❌ ERROR: ROS 2 not found. Please source setup.bash:"
    echo "  source /opt/ros/humble/setup.bash"
    echo "  source install/setup.bash"
    exit 1
fi

echo "✓ ROS 2 found: $(ros2 --version)"
echo ""

# Source workspace
echo "Sourcing workspace..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_ROOT="$SCRIPT_DIR/../../.."
source "$WORKSPACE_ROOT/install/setup.bash"
echo "✓ Workspace sourced"
echo ""

echo "=========================================="
echo "Launching Localization + Navigation Demo"
echo "=========================================="
echo ""
echo "This launch file will:"
echo "  1. Start Gazebo with office world"
echo "  2. Spawn Pioneer 3-DX robot"
echo "  3. Fuse IMU + wheel odometry (EKF)"
echo "  4. Load saved 3D map (RTAB-Map localization mode)"
echo "  5. Generate 2D projection for navigation"
echo "  6. Start Nav2 stack for path planning"
echo "  7. Open RViz for visualization"
echo ""
echo "Wait ~30 seconds for everything to initialize..."
echo ""
echo "Then in ANOTHER TERMINAL, run:"
echo "  ros2 run robot_project random_waypoint_nav"
echo ""
echo "Press Enter to start, or Ctrl+C to cancel..."
read -r

# Launch
export ROS_DOMAIN_ID=0  # Default domain
ros2 launch robot_project localization_navigation.launch.py
