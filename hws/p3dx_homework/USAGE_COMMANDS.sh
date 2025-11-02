#!/bin/bash
# Pioneer 3-DX ROS 2 Simulation - Quick Start Commands
# Usage: Source this file or copy-paste commands to terminal

# =============================================================================
# SETUP COMMANDS (One-time)
# =============================================================================

# Install ROS 2 Humble packages
install_dependencies() {
    sudo apt update
    sudo apt install -y \
        ros-humble-gazebo-ros-pkgs \
        ros-humble-robot-state-publisher \
        ros-humble-joint-state-publisher \
        ros-humble-joint-state-publisher-gui \
        ros-humble-xacro \
        ros-humble-ros2-control \
        ros-humble-ros2-controllers \
        ros-humble-diff-drive-controller \
        ros-humble-plotjuggler-ros \
        ros-humble-teleop-twist-keyboard
}

# Build workspace
build_workspace() {
    cd ~/p3dx_ws
    source /opt/ros/humble/setup.bash
    colcon build --symlink-install
    source install/setup.bash
}

# Clean rebuild
clean_build() {
    cd ~/p3dx_ws
    rm -rf build/ install/ log/
    source /opt/ros/humble/setup.bash
    colcon build --symlink-install
    source install/setup.bash
}

# =============================================================================
# RUNTIME COMMANDS (Use in separate terminals)
# =============================================================================

# Terminal 1: Launch Gazebo Simulation
launch_gazebo() {
    source /opt/ros/humble/setup.bash
    source ~/p3dx_ws/install/setup.bash
    ros2 launch p3dx_gazebo p3dx.launch.py
}

# Terminal 2: Run cmd_vel Publisher (Auto circular motion)
run_cmd_vel() {
    source /opt/ros/humble/setup.bash
    source ~/p3dx_ws/install/setup.bash
    ros2 run p3dx_gazebo cmd_vel_publisher.py
}

# Terminal 2 (Alternative): Manual keyboard control
run_teleop() {
    source /opt/ros/humble/setup.bash
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
}

# Terminal 3: Launch RViz
launch_rviz() {
    source /opt/ros/humble/setup.bash
    source ~/p3dx_ws/install/setup.bash
    rviz2 -d ~/p3dx_ws/src/p3dx/p3dx_description/rviz/p3dx_view.rviz
}

# Terminal 3 (Alternative): Launch RViz without config
launch_rviz_blank() {
    source /opt/ros/humble/setup.bash
    rviz2
}

# Terminal 4: Plotjuggler (X-Y odometry plot)
launch_plotjuggler() {
    source /opt/ros/humble/setup.bash
    ros2 run plotjuggler plotjuggler
}

# Terminal 4 (Alternative): Python matplotlib trajectory plotter
run_trajectory_plot() {
    source /opt/ros/humble/setup.bash
    source ~/p3dx_ws/install/setup.bash
    python3 ~/p3dx_ws/src/p3dx/p3dx_gazebo/scripts/plot_trajectory.py
}

# =============================================================================
# DEBUGGING & MONITORING COMMANDS
# =============================================================================

# Check ROS version and user info
check_system() {
    echo "=== ROS 2 Version ==="
    ros2 --version
    echo ""
    echo "=== User Info ==="
    whoami
    hostname
    echo ""
    echo "=== Gazebo Version ==="
    gazebo --version
}

# List all active topics
list_topics() {
    source /opt/ros/humble/setup.bash
    ros2 topic list
}

# Monitor odometry topic
monitor_odom() {
    source /opt/ros/humble/setup.bash
    ros2 topic echo /odom
}

# Check odometry once
check_odom_once() {
    source /opt/ros/humble/setup.bash
    ros2 topic echo /odom --once
}

# Check topic frequency
check_topic_hz() {
    source /opt/ros/humble/setup.bash
    ros2 topic hz /odom
}

# List all nodes
list_nodes() {
    source /opt/ros/humble/setup.bash
    ros2 node list
}

# Check robot_description
check_robot_description() {
    source /opt/ros/humble/setup.bash
    ros2 topic echo /robot_description --once
}

# Kill all Gazebo processes
kill_gazebo() {
    pkill -9 gzserver
    pkill -9 gzclient
    pkill -9 gazebo
}

# Kill all ROS nodes
kill_ros_nodes() {
    pkill -9 -f ros2
}

# =============================================================================
# SCREENSHOT & VIDEO RECORDING
# =============================================================================

# Take screenshot (requires gnome-screenshot)
take_screenshot() {
    gnome-screenshot
}

# Take screenshot of selected area
take_screenshot_area() {
    gnome-screenshot -a
}

# Record screen (built-in Gnome - start/stop with same command)
record_screen() {
    echo "Press Ctrl+Alt+Shift+R to start/stop recording"
    echo "Video saved to ~/Videos/"
}

# Install screen recorder
install_screen_recorder() {
    sudo apt install -y simplescreenrecorder
    simplescreenrecorder
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Full system check
full_check() {
    echo "======================================"
    echo "Pioneer 3-DX ROS 2 System Check"
    echo "======================================"
    check_system
    echo ""
    echo "=== Workspace Build Status ==="
    if [ -d ~/p3dx_ws/install ]; then
        echo "✓ Workspace built"
        ls ~/p3dx_ws/install/
    else
        echo "✗ Workspace not built - run 'build_workspace'"
    fi
    echo ""
    echo "=== Active ROS Topics ==="
    list_topics 2>/dev/null || echo "No ROS nodes running"
}

# Quick start (launch everything in background)
quick_start() {
    echo "Starting Pioneer 3-DX simulation..."

    # Terminal 1: Gazebo
    gnome-terminal --tab --title="Gazebo" -- bash -c "source /opt/ros/humble/setup.bash; source ~/p3dx_ws/install/setup.bash; ros2 launch p3dx_gazebo p3dx.launch.py; exec bash"

    sleep 10

    # Terminal 2: cmd_vel
    gnome-terminal --tab --title="cmd_vel" -- bash -c "source /opt/ros/humble/setup.bash; source ~/p3dx_ws/install/setup.bash; ros2 run p3dx_gazebo cmd_vel_publisher.py; exec bash"

    # Terminal 3: RViz
    gnome-terminal --tab --title="RViz" -- bash -c "source /opt/ros/humble/setup.bash; source ~/p3dx_ws/install/setup.bash; rviz2 -d ~/p3dx_ws/src/p3dx/p3dx_description/rviz/p3dx_view.rviz; exec bash"

    # Terminal 4: Plotjuggler
    gnome-terminal --tab --title="Plotjuggler" -- bash -c "source /opt/ros/humble/setup.bash; ros2 run plotjuggler plotjuggler; exec bash"

    echo "All terminals launched!"
}

# =============================================================================
# HELP MENU
# =============================================================================

show_help() {
    cat << EOF
Pioneer 3-DX ROS 2 Simulation - Command Reference

SETUP:
  install_dependencies  - Install required ROS 2 packages
  build_workspace      - Build the workspace
  clean_build          - Clean and rebuild workspace

LAUNCH:
  launch_gazebo        - Start Gazebo simulation
  run_cmd_vel          - Run automatic circular motion
  run_teleop           - Manual keyboard control
  launch_rviz          - Open RViz with config
  launch_plotjuggler   - Open Plotjuggler for plots
  quick_start          - Launch all in separate terminals

DEBUGGING:
  check_system         - Show ROS version and system info
  list_topics          - List all active ROS topics
  monitor_odom         - Watch odometry messages
  check_odom_once      - Get one odometry message
  list_nodes           - List all ROS nodes
  kill_gazebo          - Kill all Gazebo processes
  full_check           - Complete system check

RECORDING:
  take_screenshot      - Take screenshot
  take_screenshot_area - Screenshot selected area
  record_screen        - Instructions for screen recording
  install_screen_recorder - Install SimpleScreenRecorder

Usage:
  source USAGE_COMMANDS.sh
  <function_name>

Example:
  source USAGE_COMMANDS.sh
  launch_gazebo
EOF
}

# If script is sourced, show help
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    show_help
fi
