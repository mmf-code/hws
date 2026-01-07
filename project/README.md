# 3D SLAM and Autonomous Navigation

**KON414E Final Project - Team 14**
**Team:** Ceylan Tolunay, Atakan Yaman, Eren Yucetürk

Pioneer 3-DX robot with EKF sensor fusion, RTAB-Map SLAM (Visual + ICP), and Nav2 navigation in Clearpath Office World simulation.

## Project Status

| Step | Requirement | Status | Implementation |
|------|-------------|--------|----------------|
| 1 | EKF Sensor Fusion (IMU + Wheel Odometry) | Complete | robot_localization package |
| 2 | Depth to PointCloud2 Conversion | Complete | Gazebo RGBD plugin |
| 3 | 3D SLAM - Visual Mode | Complete | RTAB-Map Visual SLAM |
| 4 | 3D SLAM - ICP Mode | Complete | RTAB-Map ICP SLAM |
| 5 | Localization Comparison vs Ground Truth | Complete | evaluation_node.py |
| 6 | 3D Mapping Performance Comparison | Complete | map_metrics.py |
| 7 | Autonomous Navigation with Nav2 | Complete | Hybrid Controller + Nav2 |

## Quick Start

```bash
# Install dependencies
sudo apt install ros-humble-robot-localization ros-humble-rtabmap-ros \
                 ros-humble-nav2-bringup ros-humble-depthimage-to-laserscan

# Build and source
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

# Run SLAM with Hybrid Controller
ros2 launch robot_project slam_hybrid.launch.py

# Optional: Start in AUTO mode
ros2 launch robot_project slam_hybrid.launch.py start_mode:=auto

# Optional: Nav2 (separate terminal, after SLAM starts)
ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GAZEBO SIMULATION                                │
│          Pioneer 3-DX + RGBD Camera + IMU + Office World                │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      /camera/            /imu/data            /odom
      depth/points                           (wheel)
          │                   │                   │
          │                   └─────────┬─────────┘
          │                             ▼
          │                  ┌─────────────────────┐
          │                  │  robot_localization │
          │                  │     (EKF Fusion)    │
          │                  └──────────┬──────────┘
          │                             │
          │                    /odometry/filtered
          │                             │
          ▼                             ▼
    ┌─────────────────────────────────────────────┐
    │              RTAB-Map SLAM                   │
    │    ┌──────────────┐    ┌──────────────┐     │
    │    │    Visual    │    │     ICP      │     │
    │    │    (RGBD)    │    │  (Geometric) │     │
    │    └──────┬───────┘    └──────┬───────┘     │
    └───────────┼──────────────────┼──────────────┘
                │                  │
                ▼                  ▼
          3D Point Cloud + 2D Occupancy Grid
                              │
                              ▼
                   ┌─────────────────────┐
                   │     Nav2 Stack      │
                   │   (Path Planning)   │
                   └─────────────────────┘
```

## Hybrid SLAM Controller

PyGame-based control system with manual and autonomous exploration modes.

### Control Modes

| Mode | Description |
|------|-------------|
| MANUAL | Direct WASD control, no obstacle avoidance |
| AUTO | Depth-based autonomous exploration |
| TURBO | AUTO mode with 2x speed multiplier |

### Keyboard Controls

| Key | Action |
|-----|--------|
| W/A/S/D | Movement control |
| 1-5 | Speed levels (0.2x to 2.0x) |
| Q/E | 90° turns |
| R | 180° U-turn |
| Space | Toggle AUTO/MANUAL |
| T | Turbo mode toggle |
| P | Pause (for Nav2 goals) |
| Esc | Emergency stop |

### Nav2 Integration

1. Press **P** to pause controller
2. Set 2D Goal Pose in RViz
3. Nav2 controls robot to goal
4. Press **P** to resume manual control

## Results

### EKF Sensor Fusion Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| RMSE | 0.011 m | ~1 cm average error |
| ATE | 0.009 m | Excellent trajectory tracking |
| RPE | 0.002 m | Minimal drift |
| Max Error | 0.030 m | Peak deviation ~3 cm |

### SLAM Localization Comparison

| Method | RMSE | ATE | RPE | Max Error |
|--------|------|-----|-----|-----------|
| EKF Only | 0.009 m | 0.007 m | 0.002 m | 0.030 m |
| Visual SLAM | 0.099 m | 0.088 m | 0.016 m | 0.152 m |
| ICP SLAM | 0.095 m | 0.083 m | 0.015 m | 0.146 m |

ICP SLAM achieved 4.6% better localization accuracy than Visual SLAM.

### 3D Mapping Performance

| Metric | Visual SLAM | ICP SLAM |
|--------|-------------|----------|
| Total Points | 1,265,586 | 82,314 |
| 3D Density | 204.2 pts/m³ | 223.4 pts/m³ |
| 2D Density | 1,230 pts/m² | 492 pts/m² |
| Coverage Area | 1,028.72 m² | 167.26 m² |
| Mapping Duration | 13.3 min | 1.0 min |

## Key ROS Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/odom` | Odometry | Wheel odometry |
| `/imu/data` | Imu | IMU data (100Hz) |
| `/camera/depth/points` | PointCloud2 | Depth point cloud |
| `/odometry/filtered` | Odometry | EKF fused odometry |
| `/ground_truth/odom` | Odometry | Gazebo ground truth |
| `/rtabmap/cloud_map` | PointCloud2 | 3D map |
| `/map` | OccupancyGrid | 2D navigation map |
| `/scan` | LaserScan | Converted from depth |

## Repository Structure

```
src/robot_project/
├── config/
│   ├── robot_localization.yaml    # EKF sensor fusion
│   ├── rtabmap_rgbd.yaml          # Visual SLAM config
│   └── rtabmap_icp.yaml           # ICP SLAM config
├── launch/
│   ├── slam_hybrid.launch.py      # Main SLAM launch
│   ├── view_map.launch.py         # View existing map
│   └── full_navigation.launch.py  # SLAM + Nav2
├── robot_project/
│   ├── hybrid_slam_controller.py  # PyGame controller
│   ├── evaluation_node.py         # Ground truth comparison
│   └── map_metrics.py             # 3D map quality metrics
└── rviz/
    └── slam_config.rviz           # SLAM visualization
```

## Configuration Files

| Resource | Path |
|----------|------|
| EKF Config | `src/robot_project/config/robot_localization.yaml` |
| Visual SLAM | `src/robot_project/config/rtabmap_rgbd.yaml` |
| ICP SLAM | `src/robot_project/config/rtabmap_icp.yaml` |
| Controller | `src/robot_project/robot_project/hybrid_slam_controller.py` |
| Robot URDF | `src/robot_hw1/urdf/p3dx_hw2.urdf.xacro` |
| World File | `src/robot_hw1/worlds/empty_office.world` |

## Debugging Commands

```bash
# Check SLAM status
ros2 node list | grep rtabmap
ros2 topic hz /map

# Verify TF tree
ros2 run tf2_tools view_frames

# Check camera
ros2 topic hz /camera/rgbd_camera/depth/image_raw

# Monitor metrics
ros2 topic echo /map_metrics

# Save 2D map
ros2 run nav2_map_server map_saver_cli -f project/maps/office_map
```

## Documentation

- [FINAL_REPORT.md](FINAL_REPORT.md) - Complete technical report with all implementation details
- [FINAL_REPORT_DATA.md](FINAL_REPORT_DATA.md) - IEEE report data reference and LaTeX tables
