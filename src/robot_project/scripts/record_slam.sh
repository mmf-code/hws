#!/bin/bash

# Team 14 - Record SLAM Map
# Optimized for clean map recording without PC crashes
#
# Steps:
# 1. Launches Gazebo + Robot + EKF + Optimized RTAB-Map SLAM
# 2. You drive robot manually with teleop
# 3. Graceful Ctrl+C saves map cleanly
# 4. Verify with: bash src/robot_project/scripts/check_map.sh

set -e

echo "=========================================="
echo "Team 14 - SLAM Map Recording"
echo "=========================================="
echo ""
echo "This script will:"
echo "  1. Start Gazebo with office world"
echo "  2. Spawn Pioneer 3-DX robot"
echo "  3. Fuse IMU + wheel odometry (EKF)"
echo "  4. Start RTAB-Map SLAM (optimized for PC stability)"
echo "  5. Open RViz with map visualization"
echo ""
echo "Then YOU drive the robot manually to record the map"
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
echo "INSTRUCTIONS"
echo "=========================================="
echo ""
echo "1. WAIT for Gazebo, Robot, and RViz to fully load (~30 seconds)"
echo ""
echo "2. In ANOTHER TERMINAL, run teleop:"
echo "   ros2 run teleop_twist_keyboard teleop_twist_keyboard"
echo ""
echo "3. Drive robot around office slowly for 3-5 minutes"
echo "   - Cover different areas"
echo "   - Visit different rooms"
echo "   - Close loops (return to visited areas)"
echo ""
echo "4. When done, return robot to starting position (2.0, 0.0)"
echo ""
echo "5. Press Ctrl+C to GRACEFULLY STOP and SAVE MAP"
echo "   - RViz will close"
echo "   - RTAB-Map will save database"
echo "   - Map should be saved at: $HOME/.ros/rtabmap.db"
echo ""
echo "6. Verify map was saved:"
echo "   bash src/robot_project/scripts/check_map.sh"
echo ""
echo "=========================================="
echo ""
echo "IMPORTANT TIPS:"
echo "- Don't worry about the map quality while recording"
echo "- RViz might be slow - that's normal"
echo "- Each loop closure improves the map"
echo "- Ctrl+C on THIS TERMINAL will save gracefully"
echo "- If PC seems to struggle, reduce movement speed"
echo ""
echo "Press Enter to start recording, or Ctrl+C to cancel..."
read -r

echo ""
echo "Launching optimized SLAM..."
echo ""

export ROS_DOMAIN_ID=0  # Default domain
ros2 launch robot_project optimized_slam.launch.py use_rviz:=true

echo ""
echo "=========================================="
echo "Recording complete!"
echo "=========================================="
echo ""
echo "Checking map..."
bash "$SCRIPT_DIR/check_map.sh"
