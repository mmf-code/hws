#!/bin/bash

# IMU Data Plotter (Alternative to rqt_multiplot)

# Source ROS first
source /opt/ros/humble/setup.bash
source ~/Documents/GitHub/hws_repo/install/setup.bash

echo "═══════════════════════════════════════════"
echo "  IMU Data Plotter"
echo "═══════════════════════════════════════════"
echo ""
echo "Opening IMU plots..."
echo ""
echo "Topics:"
echo "  - Angular Velocity: /imu/data/angular_velocity/x,y,z"
echo "  - Linear Acceleration: /imu/data/linear_acceleration/x,y,z"
echo ""
echo "In the plot window, you should see:"
echo "  - Z angular velocity ~0.5 rad/s (robot turning)"
echo "  - Z linear acceleration ~9.8 m/s² (gravity)"
echo ""

# Launch rqt_plot with full path
/opt/ros/humble/lib/rqt_plot/rqt_plot /imu/data/angular_velocity/x /imu/data/angular_velocity/y /imu/data/angular_velocity/z /imu/data/linear_acceleration/x /imu/data/linear_acceleration/y /imu/data/linear_acceleration/z
