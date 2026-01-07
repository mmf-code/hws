#!/bin/bash

# Complete HW2 Startup Script - Opens Everything in Separate Terminals

WORKSPACE=~/Documents/GitHub/hws_repo

echo "═══════════════════════════════════════════════════════"
echo "  HW2 - Complete System Launcher"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "This will open 5 terminals:"
echo "  1. Gazebo (with colored objects)"
echo "  2. RViz"
echo "  3. Robot Motion (cmd_vel)"
echo "  4. Camera Viewer"
echo "  5. IMU Plotter"
echo ""
echo "Press Ctrl+C in THIS terminal to stop everything"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Kill any existing processes
pkill -9 gzserver gzclient 2>/dev/null

# Terminal 1: Gazebo + Robot
echo "[1/5] Launching Gazebo with objects..."
gnome-terminal --title="HW2: Gazebo" -- bash -c "
cd $WORKSPACE
source /opt/ros/humble/setup.bash
source install/setup.bash
echo 'Starting Gazebo with colored objects...'
ros2 launch robot_hw1 hw2.launch.py use_rviz:=false world:=$WORKSPACE/worlds/hw2_world.world
exec bash
" &
sleep 8  # Wait for Gazebo to load

# Terminal 2: RViz
echo "[2/5] Launching RViz..."
gnome-terminal --title="HW2: RViz" -- bash -c "
cd $WORKSPACE
source /opt/ros/humble/setup.bash
source install/setup.bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0
export LD_LIBRARY_PATH=\$(echo \"\$LD_LIBRARY_PATH\" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:\$//')
echo 'Starting RViz...'
rviz2 -d $WORKSPACE/install/robot_hw1/share/robot_hw1/rviz/hw2_config.rviz
exec bash
" &
sleep 3

# Terminal 3: Robot Motion
echo "[3/5] Launching Robot Motion Controller..."
gnome-terminal --title="HW2: Robot Motion" -- bash -c "
cd $WORKSPACE
source /opt/ros/humble/setup.bash
source install/setup.bash
echo 'Starting circular motion...'
ros2 run robot_hw1 cmd_vel_publisher
exec bash
" &
sleep 2

# Terminal 4: Camera Viewer
echo "[4/5] Launching Camera Viewer..."
gnome-terminal --title="HW2: Camera" -- bash -c "
cd $WORKSPACE
source /opt/ros/humble/setup.bash
source install/setup.bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0
export LD_LIBRARY_PATH=\$(echo \"\$LD_LIBRARY_PATH\" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:\$//')
echo 'Starting Camera Viewer...'
/opt/ros/humble/lib/rqt_image_view/rqt_image_view /camera/rgb/image_raw
exec bash
" &
sleep 2

# Terminal 5: IMU Plotter
echo "[5/5] Launching IMU Plotter..."
gnome-terminal --title="HW2: IMU Plots" -- bash -c "
cd $WORKSPACE
source /opt/ros/humble/setup.bash
source install/setup.bash
echo 'Starting IMU Plots...'
/opt/ros/humble/lib/rqt_plot/rqt_plot /imu/data/angular_velocity/x /imu/data/angular_velocity/y /imu/data/angular_velocity/z /imu/data/linear_acceleration/x /imu/data/linear_acceleration/y /imu/data/linear_acceleration/z
exec bash
" &

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  All Terminals Launched!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "You should now see:"
echo "  ✓ Gazebo with robot and colored objects"
echo "  ✓ RViz with odometry path"
echo "  ✓ Robot moving in circles"
echo "  ✓ Camera view showing objects"
echo "  ✓ IMU graphs updating"
echo ""
echo "To record video:"
echo "  Ctrl + Alt + Shift + R (start/stop)"
echo ""
echo "Press Ctrl+C here to kill all processes"
echo ""

# Wait for user interrupt
trap 'echo "Cleaning up..."; pkill -P $$; pkill -9 gzserver gzclient; exit' INT
wait
