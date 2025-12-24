# KON414E Final Project - Team 14

## 3D SLAM and Autonomous Navigation with Pioneer 3-DX

**Team Members:** Ceylan Tolunay, Atakan Yaman, Eren Yucetürk

---

## Quick Start

### 1. Install Dependencies
```bash
# ROS 2 packages
sudo apt update
sudo apt install -y \
    ros-humble-robot-localization \
    ros-humble-rtabmap-ros \
    ros-humble-nav2-bringup \
    ros-humble-octomap-server
```

### 2. Build Workspace
```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 3. Run SLAM System
```bash
# Option A: Full SLAM pipeline (Gazebo + EKF + RTAB-Map + RViz)
ros2 launch robot_project full_slam.launch.py

# Option B: Step-by-step launch
# Terminal 1: Base simulation (Gazebo + EKF)
ros2 launch robot_project project_bringup.launch.py use_rviz:=false

# Terminal 2: RTAB-Map SLAM (RGB-D visual mode)
ros2 launch robot_project slam_rgbd.launch.py

# OR: RTAB-Map SLAM (ICP mode for comparison)
ros2 launch robot_project slam_icp.launch.py

# Terminal 3: Manual control for mapping
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 4. SLAM Mode Selection
```bash
# RGB-D Visual SLAM (default)
ros2 launch robot_project full_slam.launch.py slam_mode:=rgbd

# ICP-based SLAM (for comparison)
ros2 launch robot_project full_slam.launch.py slam_mode:=icp

# Use RTAB-Map native visualizer instead of RViz
ros2 launch robot_project full_slam.launch.py use_rtabmap_viz:=true use_rviz:=false
```

---

## Repository Structure

```
hws_repo/
├── src/
│   ├── robot_hw1/              # Base package (HW1-3)
│   │   ├── urdf/               # Robot URDF with sensors
│   │   ├── launch/             # HW launch files
│   │   └── robot_hw1/          # Python nodes
│   │
│   └── robot_project/          # FINAL PROJECT PACKAGE
│       ├── config/             # Configuration files
│       │   ├── robot_localization.yaml  # EKF sensor fusion
│       │   ├── rtabmap_rgbd.yaml        # Visual SLAM config
│       │   └── rtabmap_icp.yaml         # ICP SLAM config
│       ├── launch/             # Launch files
│       │   ├── full_slam.launch.py      # Complete SLAM pipeline
│       │   ├── project_bringup.launch.py # Base simulation
│       │   ├── sensor_fusion.launch.py  # EKF only
│       │   ├── slam_rgbd.launch.py      # Visual SLAM
│       │   └── slam_icp.launch.py       # ICP SLAM
│       ├── robot_project/      # Python nodes
│       │   ├── evaluation_node.py       # Ground truth comparison
│       │   ├── waypoint_navigator.py    # Nav2 waypoints
│       │   └── map_metrics.py           # Map quality metrics
│       └── rviz/
│           └── slam_config.rviz         # SLAM visualization
│
├── project/                    # Documentation & Results
│   ├── PROJECT_PLAN.md         # Detailed implementation plan
│   ├── README.md               # This file
│   ├── maps/                   # Saved maps
│   ├── results/                # Evaluation results
│   │   ├── plots/
│   │   └── data/
│   └── report/                 # IEEE format report
│
└── hw3/                        # Office World (already integrated)
    └── src/cpr_office_gazebo/
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GAZEBO SIMULATION                     │
│  Pioneer 3-DX + RGBD Camera + IMU + Office World        │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      /camera/        /imu/data        /odom
      depth/points                    (wheel)
          │               │               │
          │               └───────┬───────┘
          │                       ▼
          │            ┌─────────────────────┐
          │            │ robot_localization  │
          │            │   (EKF Fusion)      │
          │            └──────────┬──────────┘
          │                       │
          │              /odometry/filtered
          │                       │
          ▼                       ▼
    ┌─────────────────────────────────────┐
    │           RTAB-Map SLAM             │
    │  ┌─────────────┐  ┌─────────────┐   │
    │  │  Config A   │  │  Config B   │   │
    │  │  (Visual)   │  │   (ICP)     │   │
    │  └──────┬──────┘  └──────┬──────┘   │
    └─────────┼────────────────┼──────────┘
              │                │
              ▼                ▼
         3D Point Cloud Maps + 2D Grid Map
                          │
                          ▼
              ┌─────────────────────┐
              │    NAV2 Stack       │
              │  (path planning)    │
              └──────────┬──────────┘
                         │
                         ▼
              Autonomous Navigation
```

---

## Key Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/odom` | Odometry | Wheel odometry |
| `/imu/data` | Imu | IMU data (100Hz) |
| `/camera/depth/points` | PointCloud2 | Depth point cloud |
| `/camera/rgb/image_raw` | Image | RGB image |
| `/odometry/filtered` | Odometry | Fused odometry (EKF) |
| `/ground_truth/odom` | Odometry | Gazebo ground truth |
| `/rtabmap/cloud_map` | PointCloud2 | 3D map |
| `/map` | OccupancyGrid | 2D navigation map |

---

## Evaluation Metrics

### Localization
- RMSE (Root Mean Square Error) vs ground truth
- ATE (Absolute Trajectory Error)
- Maximum position error

### Mapping
- Point cloud density (points/m³)
- Coverage area (m²)
- Map completeness

### Navigation
- Goal success rate
- Path efficiency
- Time to goal

---

## Files to Submit

- [ ] IEEE Report (6-10 pages)
- [ ] Presentation (max 10 slides)
- [ ] Demo video
- [ ] GitHub repository link
- [ ] Evaluation paragraph (individual)

---

## Useful Commands

```bash
# View topics
ros2 topic list | grep -E "odom|imu|camera|map"

# Check TF tree
ros2 run tf2_tools view_frames

# Save map
ros2 run nav2_map_server map_saver_cli -f project/maps/office_map

# Record bag
ros2 bag record -o project/results/test_run /odom /imu/data /ground_truth/odom
```
