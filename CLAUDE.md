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

## Primary Launch Files

### Recommended: Hybrid SLAM with PyGame Control
```bash
# Fresh SLAM with manual/auto control (RECOMMENDED)
ros2 launch robot_project slam_hybrid.launch.py

# Start in specific mode
ros2 launch robot_project slam_hybrid.launch.py start_mode:=auto
ros2 launch robot_project slam_hybrid.launch.py start_mode:=manual

# Custom parameters
ros2 launch robot_project slam_hybrid.launch.py base_speed:=1.2 use_rviz:=false
```

### Nav2 Navigation (separate terminal after SLAM starts)
```bash
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
```

### Other Launch Files
```bash
# Full navigation (SLAM + Nav2 combined)
ros2 launch robot_project full_navigation.launch.py

# View existing map database
ros2 launch robot_project view_map.launch.py

# HW2: Sensor integration test
ros2 launch robot_hw1 hw2.launch.py

# HW3: Office world with corridor navigator
ros2 launch robot_hw1 hw3.launch.py
```

## Hybrid SLAM Controller

The `hybrid_slam_controller.py` provides PyGame-based control for SLAM mapping.

### Control Modes
- **MANUAL** (default): Direct WASD control, no obstacle avoidance
- **AUTO**: Depth-based autonomous exploration with obstacle avoidance
- **TURBO**: Auto mode with 2x speed multiplier

### Keyboard Controls
| Key | Action |
|-----|--------|
| WASD | Move forward/left/backward/right |
| 1-5 | Speed levels (0.2x to 2.0x) |
| Q/E | 90° left/right spin |
| R | 180° U-turn |
| SPACE | Toggle Auto/Manual mode |
| T | Turbo mode toggle |
| P | Pause/Resume (use before Nav2 goal) |
| ESC | Emergency stop |

### Nav2 Integration
When using Nav2 with hybrid controller:
1. Press **P** to pause controller
2. Set 2D Goal Pose in RViz
3. Nav2 controls robot to goal
4. Press **P** to resume manual control

## Architecture

### Package Structure
- **src/robot_hw1/** - Main ROS 2 Python package
  - `robot_hw1/` - Python nodes (cmd_vel_publisher, noisy_odom_publisher, corridor_navigator)
  - `urdf/p3dx_hw2.urdf.xacro` - Robot URDF with RGBD camera and IMU
  - `worlds/empty_office.world` - Gazebo world with ground plane (critical for physics)

- **src/robot_project/** - SLAM + Navigation package
  - `robot_project/hybrid_slam_controller.py` - PyGame SLAM controller
  - `robot_project/map_metrics.py` - 3D map quality metrics
  - `launch/slam_hybrid.launch.py` - Main SLAM launch file
  - `config/robot_localization.yaml` - EKF sensor fusion config

- **hw3/src/cpr_office_gazebo/** - Office environment (ROS 1 port)

### Key ROS Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | Twist | Velocity commands |
| `/odometry/filtered` | Odometry | EKF-fused odometry |
| `/map` | OccupancyGrid | 2D map from RTAB-Map |
| `/rtabmap/cloud_map` | PointCloud2 | 3D point cloud map |
| `/camera/rgbd_camera/depth/image_raw` | Image | Depth image |
| `/scan` | LaserScan | Converted from depth |
| `/goal_pose` | PoseStamped | Nav2 navigation goal |

### TF Tree
```
map → odom → base_link → camera_link
                      → imu_link
                      → front_sonar / back_sonar
```

### SLAM Timing (slam_hybrid.launch.py)
```
T=0s    Gazebo starts
T=2s    Office geometry spawn
T=4s    Robot spawn (z=0.1)
T=6s    EKF sensor fusion
T=7s    Depth → LaserScan
T=9s    RTAB-Map SLAM
T=15s   RViz
T=18s   Hybrid Controller (MANUAL mode)
T=23s   Controller active (after 5s delay)
```

## Database Management

```bash
# RTAB-Map database location
~/.ros/rtabmap.db

# Check database size
ls -lh ~/.ros/rtabmap.db

# Backup database (use SQLite API for safe copy during active SLAM)
cp ~/.ros/rtabmap.db ~/maps/backup_$(date +%Y%m%d_%H%M%S).db

# Backups directory
~/maps/
```

## Debugging

```bash
# Check SLAM status
ros2 node list | grep rtabmap
ros2 topic hz /map

# Verify TF tree
ros2 run tf2_tools view_frames

# Check camera
ros2 topic hz /camera/rgbd_camera/depth/image_raw

# Monitor map metrics (auto-saved to project/results/data/)
ros2 topic echo /map_metrics
```

## Known Issues and Workarounds

- **Robot falling through ground:** Ensure `empty_office.world` has ground_plane model. Check with: `grep ground_plane src/robot_hw1/worlds/empty_office.world`
- **Map drift/reset during SLAM:** Loop closure false positives. Fixed with strict parameters in slam_hybrid.launch.py (Vis/MinInliers, RGBD/OptimizeMaxError)
- **Nav2 "failed to create plan":** Usually costmap issue. Verify /map is publishing: `ros2 topic echo /map --once`
- **PyGame keyboard not working:** Click on PyGame window to give it focus
- **RViz libpthread crash:** Use apt package: `sudo apt install ros-humble-rviz2`
- **Controller conflicts with Nav2:** Press P to pause controller before using 2D Goal Pose
