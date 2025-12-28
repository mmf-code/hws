# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS 2 robotics homework repository for **KON414E - Principles of Robot Autonomy** course. Contains Pioneer 3-DX differential drive robot simulation using ROS 2 Humble and Gazebo Classic on Ubuntu 22.04. The repository has three main components:

- **HW1** (p3dx_homework/): Reference implementation - ROS 1 to ROS 2 port of Pioneer 3-DX packages
- **HW2** (src/robot_hw1/): Sensor integration - circular motion with noisy odometry simulation
- **HW3** (src/robot_hw1/ + src/robot_project/): Autonomous navigation - SLAM and Nav2 with office world

## Build Commands

```bash
# Source ROS 2 and build entire workspace
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

# Build specific package only
colcon build --symlink-install --packages-select robot_hw1
colcon build --symlink-install --packages-select cpr_office_gazebo
colcon build --symlink-install --packages-select robot_project
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
# Launch full system (Gazebo, RViz, corridor navigator)
ros2 launch robot_hw1 hw3.launch.py

# Launch without RViz
ros2 launch robot_hw1 hw3.launch.py use_rviz:=false

# Launch without autonomous controller (manual control)
ros2 launch robot_hw1 hw3.launch.py run_controller:=false
```

### HW3: Full Navigation (SLAM + Nav2)
```bash
# Launch with RTAB-Map SLAM and Nav2 navigation
ros2 launch robot_project full_navigation.launch.py
```

## Debugging and Sensor Verification

```bash
# Check available topics
ros2 topic list | grep -E 'camera|imu|odom'

# Monitor publishing rates
ros2 topic hz /imu/data
ros2 topic hz /camera/rgbd_camera/image_raw

# View sensor data
ros2 topic echo /imu/data --once
rqt_image_view /camera/rgbd_camera/image_raw

# Plot IMU angular velocity
ros2 run rqt_plot rqt_plot /imu/data/angular_velocity/x /imu/data/angular_velocity/y /imu/data/angular_velocity/z

# Check transform tree
ros2 run tf2_ros tf2_echo map base_link
ros2 run tf2_tools view_frames
```

## Architecture

### Package Structure
- **src/robot_hw1/** - Main ROS 2 Python package (ament_python)
  - `robot_hw1/` - Python executable nodes
    - `cmd_vel_publisher.py` - Circular motion controller for HW2
    - `noisy_odom_publisher.py` - Adds realistic odometry drift to Gazebo data
    - `corridor_navigator.py` - Depth-based reactive obstacle avoidance (HW3)
  - `launch/hw2.launch.py` - Gazebo + robot spawn + robot state publisher
  - `launch/hw3.launch.py` - Office world + rviz + corridor navigator
  - `launch/robot_hw1.launch.py` - Generic robot launch (used by other packages)
  - `urdf/p3dx_hw2.urdf.xacro` - Robot URDF with RGBD camera and IMU sensors
  - `rviz/` - RViz configuration files
  - `worlds/` - Gazebo world files (empty_office.world)
  - `config/` - Robot controller and sensor configurations
  - `meshes/` - STL mesh files for robot visualization

- **src/robot_project/** - HW3 Final project package (SLAM + Navigation)
  - `launch/full_navigation.launch.py` - RTAB-Map SLAM + Nav2 bringup
  - `config/` - Nav2 behavior server parameters
  - `rviz/` - Navigation RViz configs

- **hw3/src/cpr_office_gazebo/** - Office environment package (ported from ROS 1)
  - Provides office world URDF and meshes

- **p3dx_homework/** - HW1 reference (original ROS 1 to ROS 2 port)
  - Historical reference for Pioneer 3-DX integration

### Key ROS Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | Twist | Velocity commands to diff_drive plugin |
| `/odom` | Odometry | Noisy odometry with drift (HW2) |
| `/odom_clean` | Odometry | Ground truth odometry from Gazebo |
| `/camera/rgbd_camera/image_raw` | Image | RGB image from RGBD camera (HW3) |
| `/camera/rgbd_camera/depth/image_raw` | Image | Depth image (HW3) |
| `/camera/rgb/image_raw` | Image | RGB image (HW2 naming) |
| `/camera/depth/points` | PointCloud2 | Depth point cloud (HW2) |
| `/imu/data` | Imu | IMU sensor data (100Hz) |
| `/goal_pose` | PoseStamped | Navigation goal (HW3 full navigation) |
| `/amcl_pose` | PoseWithCovarianceStamped | Robot localization estimate |

### Robot Sensors (URDF Configuration)
- **RGBD Camera:** Front-mounted, 90° FOV, 0.1-4.0m depth range, 30Hz update rate
- **IMU:** Center-mounted, 100Hz, Gaussian noise configured in p3dx_hw2.urdf.xacro

### Data Flow
1. Launch file starts Gazebo, spawns robot model, publishes TF tree
2. Gazebo physics plugin outputs ground truth `/odom_clean`
3. `noisy_odom_publisher` subscribes to `/odom_clean`, adds realistic drift, publishes `/odom` (HW2)
4. Controller sends Twist commands via `/cmd_vel` to differential drive plugin
5. Camera and IMU Gazebo plugins publish raw sensor data on respective topics

### Corridor Navigator Algorithm (HW3)

The `corridor_navigator.py` node uses reactive control dividing depth image into 5 regions:

```
+--------+------+--------+------+--------+
|  FAR   | LEFT | CENTER | RIGHT|  FAR   |
|  LEFT  |      |        |      | RIGHT  |
+--------+------+--------+------+--------+
  0-15%  15-35%  35-65%  65-85%  85-100%
```

**Control Modes:**
- **Normal:** All clear - move forward at 0.3 m/s
- **Approaching:** Center < 0.8m - reduce speed, turn toward open side
- **Critical:** Center < 0.4m - stop, aggressive turn
- **Corner:** All blocked - reverse slightly, sharp turn
- **Stuck Recovery:** No progress > 1.5s - backup and sharp turn

## Development Workflow

### Adding New Python Nodes
1. Create node file in `src/robot_hw1/robot_hw1/`
2. Add entry point in `src/robot_hw1/setup.py` under `console_scripts`
3. Run `colcon build --symlink-install` to register
4. Launch with `ros2 run robot_hw1 <node_name>`

### Modifying Robot Model
1. Edit `src/robot_hw1/urdf/p3dx_hw2.urdf.xacro`
2. For sensor parameters, modify the xacro properties at the top of the file
3. Run `colcon build --symlink-install` to regenerate URDF
4. Verify with `ros2 param list` after launching

### Adding New Data Files
1. Place files in appropriate subdirectory (worlds/, rviz/, config/, etc.)
2. Register in `src/robot_hw1/setup.py` under `data_files`
3. Run `colcon build --symlink-install`
4. Reference in launch files using `get_package_share_directory()`

## Known Issues and Workarounds

- **RViz libpthread crash:** Use apt package instead of snap: `sudo apt install ros-humble-rviz2`. If display issues occur, set `export QT_QPA_PLATFORM=xcb`
- **Gazebo slow first startup:** Initial physics engine load takes 10-15 seconds, subsequent launches are faster
- **Camera initialization delay:** Wait 5-10 seconds after launch before relying on camera data
- **Topic naming differs between HW2/HW3:** HW2 uses `/camera/rgb/...`, HW3 uses `/camera/rgbd_camera/...` - check URDF sensor configuration in launch file
- **Transform lookup failures:** Ensure `robot_state_publisher` is running and robot URDF is loaded. Check with `ros2 run tf2_tools view_frames`
