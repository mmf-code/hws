#!/bin/bash
# Test script to validate TF synchronization fixes for Nav2 navigation

set -e

echo "============================================"
echo "TF Synchronization Fix - Test Script"
echo "============================================"

# Source ROS 2
source /opt/ros/humble/setup.bash
source /home/mmf/Documents/GitHub/hws_repo/install/setup.bash

echo ""
echo "Step 1: Verifying configuration changes..."
echo "============================================"

echo ""
echo "Checking RTAB-Map RGBD TF publishing..."
if grep -q "publish_tf: true" /home/mmf/Documents/GitHub/hws_repo/src/robot_project/config/rtabmap_rgbd.yaml; then
    echo "✅ RTAB-Map RGBD: publish_tf enabled"
else
    echo "❌ ERROR: RTAB-Map RGBD TF publishing not configured"
    exit 1
fi

echo ""
echo "Checking RTAB-Map ICP TF publishing..."
if grep -q "publish_tf: true" /home/mmf/Documents/GitHub/hws_repo/src/robot_project/config/rtabmap_icp.yaml; then
    echo "✅ RTAB-Map ICP: publish_tf enabled"
else
    echo "❌ ERROR: RTAB-Map ICP TF publishing not configured"
    exit 1
fi

echo ""
echo "Checking Gazebo TF publishing disabled..."
if grep -q "<publish_odom_tf>false</publish_odom_tf>" /home/mmf/Documents/GitHub/hws_repo/src/robot_hw1/urdf/p3dx_hw2.urdf.xacro; then
    echo "✅ Gazebo: publish_odom_tf disabled"
else
    echo "❌ ERROR: Gazebo TF publishing not disabled"
    exit 1
fi

echo ""
echo "Checking Nav2 transform tolerances..."
TOLERANCE_COUNT=$(grep "transform_tolerance: 1.5\|transform_tolerance: 0.5\|transform_tolerance: 0.3" /home/mmf/Documents/GitHub/hws_repo/src/robot_project/config/nav2_params.yaml | wc -l)
if [ "$TOLERANCE_COUNT" = "3" ]; then
    echo "✅ AMCL tolerance: 1.5"
    echo "✅ Controller tolerance: 0.5"
    echo "✅ Behavior Server tolerance: 0.3"
else
    echo "❌ ERROR: Not all tolerances updated (found $TOLERANCE_COUNT/3)"
    exit 1
fi

echo ""
echo "============================================"
echo "Configuration Validation: PASSED ✅"
echo "============================================"

echo ""
echo "Step 2: Ready for runtime testing"
echo "============================================"
echo ""
echo "To test the fixes, open multiple terminals and run:"
echo ""
echo "Terminal 1: Launch SLAM + Navigation"
echo "  ros2 launch robot_project full_navigation.launch.py"
echo ""
echo "Terminal 2: Monitor TF tree"
echo "  ros2 run tf2_tools view_frames"
echo "  # Wait 30s then Ctrl+C, check frames.pdf"
echo ""
echo "Terminal 3: Test TF lookups"
echo "  ros2 run tf2_ros tf2_echo map base_link"
echo "  # Watch for continuous updates, NO 'extrapolation into past' errors"
echo ""
echo "Terminal 4: Send navigation goal"
echo "  ros2 topic pub --once /goal_pose geometry_msgs/PoseStamped \"{"
echo "    header: {frame_id: 'map'},"
echo "    pose: {"
echo "      position: {x: 5.0, y: 2.0, z: 0.0},"
echo "      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}"
echo "    }"
echo "  }\""
echo ""
echo "Expected Results:"
echo "  ✅ Nav2 accepts goals without TF errors"
echo "  ✅ Robot moves FORWARD to waypoint (not just rotates)"
echo "  ✅ No 'requested time X but earliest data is at time Y' errors"
echo "  ✅ TF tree shows 'rtabmap' as map->odom publisher (not static_transform_publisher)"
echo ""
echo "============================================"
