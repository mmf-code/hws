# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS 2 robotics homework repository for **KON414E - Principles of Robot Autonomy** course. Contains Pioneer 3-DX differential drive robot simulation using ROS 2 Humble and Gazebo Classic on Ubuntu 22.04.

## Build Commands

```bash
# Source ROS 2 and build workspace
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

# Build specific package only
colcon build --symlink-install --packages-select robot_hw1

# Build hw3 office world package (if not already built)
colcon build --symlink-install --packages-select cpr_office_gazebo
```

## Running Simulations

### HW2: Sensor Integration
```bash
# Terminal 1: Launch Gazebo simulation
ros2 launch robot_hw1 hw2.launch.py use_rviz:=false

# Terminal 2: Start robot motion (circular path)
ros2 run robot_hw1 cmd_vel_publisher

# Terminal 3: Launch RViz visualization
rviz2 -d install/robot_hw1/share/robot_hw1/rviz/hw2_config.rviz
```

### HW3: Office World Navigation
```bash
# Launch full system (Gazebo, RViz, corridor navigator, PlotJuggler)
ros2 launch robot_hw1 hw3.launch.py

# Launch without RViz
ros2 launch robot_hw1 hw3.launch.py use_rviz:=false

# Launch without autonomous controller (manual control)
ros2 launch robot_hw1 hw3.launch.py run_controller:=false
```

## Verifying Sensors

```bash
# Check available topics
ros2 topic list | grep -E 'camera|imu|odom'

# Monitor publishing rates
ros2 topic hz /imu/data
ros2 topic hz /camera/rgbd_camera/image_raw

# View sensor data
ros2 topic echo /imu/data --once
rqt_image_view /camera/rgbd_camera/image_raw

# IMU plot (angular velocity)
ros2 run rqt_plot rqt_plot /imu/data/angular_velocity/x /imu/data/angular_velocity/y /imu/data/angular_velocity/z
```

## Architecture

### Package Structure
- `src/robot_hw1/` - Main ROS 2 Python package (ament_python build type)
  - `robot_hw1/` - Python nodes
    - `cmd_vel_publisher.py` - Circular motion controller (HW2)
    - `noisy_odom_publisher.py` - Odometry with drift simulation
    - `corridor_navigator.py` - Depth-based obstacle avoidance (HW3)
  - `urdf/p3dx_hw2.urdf.xacro` - Robot model with RGBD camera and IMU
  - `launch/hw2.launch.py` - HW2 launch (sensor integration)
  - `launch/hw3.launch.py` - HW3 launch (office world navigation)
  - `rviz/` - RViz config files
  - `worlds/` - Gazebo world files
- `hw3/src/cpr_office_gazebo/` - Office world package (ported from ROS 1)
- `p3dx_homework/` - HW1 reference (original ROS 1 to ROS 2 port)

### Key ROS Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | Twist | Velocity commands |
| `/odom` | Odometry | Noisy odometry with drift simulation |
| `/odom_clean` | Odometry | Ideal odometry from Gazebo |
| `/camera/rgbd_camera/image_raw` | Image | RGB camera (HW3 naming) |
| `/camera/rgbd_camera/depth/image_raw` | Image | Depth image (HW3) |
| `/camera/rgbd_camera/points` | PointCloud2 | Point cloud |
| `/camera/rgb/image_raw` | Image | RGB camera (HW2 naming) |
| `/camera/depth/points` | PointCloud2 | Depth point cloud (HW2) |
| `/imu/data` | Imu | IMU sensor data (100Hz) |

### Robot Sensors (URDF)
- **RGBD Camera:** Front-mounted, 90deg FOV, 0.1-4.0m depth range, 30Hz
- **IMU:** Center-mounted, 100Hz, with configurable Gaussian noise

### Data Flow
1. Launch file starts Gazebo, spawns robot, publishes TF via robot_state_publisher
2. Controller node sends Twist commands to `/cmd_vel`
3. Gazebo diff_drive plugin outputs `/odom_clean`
4. `noisy_odom_publisher` adds realistic drift to produce `/odom`
5. Camera and IMU plugins publish sensor data

### Corridor Navigator Algorithm (HW3)

The navigator divides the depth image into 5 regions:
```
+--------+------+--------+------+--------+
|  FAR   | LEFT | CENTER | RIGHT|  FAR   |
|  LEFT  |      |        |      | RIGHT  |
+--------+------+--------+------+--------+
  0-15%  15-35%  35-65%  65-85%  85-100%
```

Movement modes:
- **Normal:** All clear - forward at 0.3 m/s
- **Approaching:** Center < 0.8m - slow down, turn toward open side
- **Critical:** Center < 0.4m - stop, aggressive turn
- **Corner:** All directions blocked - reverse slightly, sharp turn
- **Stuck Recovery:** No progress for 1.5s - backup and aggressive turn

## File Modification Guide

- **Robot model changes:** Edit `src/robot_hw1/urdf/p3dx_hw2.urdf.xacro`
- **New Python nodes:** Add to `src/robot_hw1/robot_hw1/`, register in `setup.py` entry_points
- **Launch modifications:** Edit files in `src/robot_hw1/launch/`
- **New data files:** Register in `setup.py` data_files section
- After any changes: `colcon build --symlink-install`

## Known Issues

- **RViz libpthread crash:** Use apt version (`sudo apt install ros-humble-rviz2`), not snap. Set `export QT_QPA_PLATFORM=xcb` if needed.
- **Gazebo slow startup:** First launch takes 10-15 seconds for physics initialization
- **Camera delay:** Wait 5-10 seconds after launch for camera plugin initialization
- **Topic naming:** HW2 uses `/camera/rgb/...`, HW3 uses `/camera/rgbd_camera/...` - check URDF sensor configuration
