# KON414E - Principles of Robot Autonomy

ROS 2 robotics coursework repository featuring Pioneer 3-DX differential drive robot simulation with Gazebo Classic on Ubuntu 22.04.

## Repository Structure

```
hws_repo/
├── p3dx_homework/          # HW1: ROS 1 → ROS 2 Port
├── src/
│   ├── robot_hw1/          # HW2 & HW3: Sensor Integration
│   └── robot_project/      # Final Project: 3D SLAM + Navigation
├── hw3/                    # Office World Environment
├── project/                # Final Project Documentation & Results
└── scripts/                # Utility Scripts
```

## Homework 1: Pioneer 3-DX ROS 2 Port

**Location:** `p3dx_homework/`

Full ROS 1 to ROS 2 port of Pioneer 3-DX packages with differential drive control, URDF/xacro robot model, and RViz visualization.

```bash
ros2 launch p3dx_gazebo gazebo.launch.py
```

## Homework 2: Sensor Integration

**Location:** `src/robot_hw1/`

RGBD camera and IMU integration with noisy odometry simulation for circular motion trajectory testing.

```bash
ros2 launch robot_hw1 hw2.launch.py
```

## Homework 3: Autonomous Navigation

**Location:** `src/robot_hw1/` + `hw3/`

SLAM and Nav2 integration with Clearpath Office World environment and corridor navigator node.

```bash
ros2 launch robot_hw1 hw3.launch.py
```

## Final Project: 3D SLAM and Autonomous Navigation

**Location:** `src/robot_project/` + `project/`
**Team 14:** Ceylan Tolunay, Atakan Yaman, Eren Yucetürk

### Requirements Status

| Step | Requirement | Status |
|------|-------------|--------|
| 1 | EKF Sensor Fusion (IMU + Wheel Odometry) | Complete |
| 2 | Depth to PointCloud2 Conversion | Complete |
| 3 | 3D SLAM - Visual Mode (RTAB-Map RGBD) | Complete |
| 4 | 3D SLAM - ICP Mode (RTAB-Map ICP) | Complete |
| 5 | Localization Performance vs Ground Truth | Complete |
| 6 | 3D Mapping Performance Comparison | Complete |
| 7 | Autonomous Navigation with Nav2 | Complete |

### Key Results

| Metric | Value |
|--------|-------|
| EKF RMSE | 0.011 m |
| Visual SLAM RMSE | 0.099 m |
| ICP SLAM RMSE | 0.095 m |
| Point Cloud | 1.2M+ points |
| Coverage Area | 1,028 m² |

### Quick Start

```bash
# Install dependencies
sudo apt install ros-humble-robot-localization ros-humble-rtabmap-ros \
                 ros-humble-nav2-bringup ros-humble-depthimage-to-laserscan

# Build
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

# Run SLAM with Hybrid Controller
ros2 launch robot_project slam_hybrid.launch.py

# Optional: Nav2 in separate terminal
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
```

### Hybrid Controller

| Key | Action |
|-----|--------|
| W/A/S/D | Movement |
| Space | Toggle AUTO/MANUAL |
| T | Turbo mode (2x) |
| P | Pause (for Nav2) |
| 1-5 | Speed levels |
| Q/E | 90° turns |
| Esc | Emergency stop |

See [project/README.md](project/README.md) for detailed documentation.

## Key Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | Twist | Velocity commands |
| `/odometry/filtered` | Odometry | EKF-fused odometry |
| `/map` | OccupancyGrid | 2D map from RTAB-Map |
| `/rtabmap/cloud_map` | PointCloud2 | 3D point cloud map |
| `/ground_truth/odom` | Odometry | Gazebo ground truth |

## Build Commands

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

# Build specific package
colcon build --symlink-install --packages-select robot_project
```
