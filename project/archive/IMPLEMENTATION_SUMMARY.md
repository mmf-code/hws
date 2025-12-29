# KON414E Final Project - Implementation Summary

## Team 14: Ceylan Tolunay, Atakan Yaman, Eren Yucetürk

**Project:** 3D SLAM and Autonomous Navigation with Pioneer 3-DX
**Date:** 25 December 2024
**Status:** Technical Implementation Complete

---

## 1. Project Requirements vs Implementation

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| robot_localization (IMU + wheel odom fusion) | EKF with `robot_localization.yaml` | ✅ |
| RGBD depth → PointCloud2 | Native from Gazebo camera plugin | ✅ |
| 3D SLAM (faster_lio or similar) | RTAB-Map Visual SLAM | ✅ |
| 3D SLAM comparison | RTAB-Map ICP mode | ✅ |
| Ground truth comparison | Gazebo p3d plugin + evaluation_node | ✅ |
| 3D mapping metrics | map_metrics.py (density, coverage) | ✅ |
| 2D map projection | RTAB-Map grid_map + depthimage_to_laserscan | ✅ |
| Nav2 navigation | Full Nav2 stack integration | ✅ |

---

## 2. Package Structure

```
src/robot_project/                    # Main project package
├── package.xml
├── setup.py
├── setup.cfg
├── resource/robot_project
│
├── config/
│   ├── robot_localization.yaml      # EKF sensor fusion (IMU + wheel)
│   ├── rtabmap_rgbd.yaml            # Visual SLAM configuration
│   ├── rtabmap_icp.yaml             # ICP SLAM configuration
│   └── nav2_params.yaml             # Navigation stack parameters
│
├── launch/
│   ├── project_bringup.launch.py    # Base simulation (Gazebo + EKF)
│   ├── sensor_fusion.launch.py      # EKF only
│   ├── slam_rgbd.launch.py          # Visual SLAM standalone
│   ├── slam_icp.launch.py           # ICP SLAM standalone
│   ├── full_slam.launch.py          # Gazebo + EKF + SLAM + RViz
│   ├── navigation.launch.py         # Nav2 standalone
│   └── full_navigation.launch.py    # Complete pipeline with Nav2
│
├── robot_project/
│   ├── __init__.py
│   ├── evaluation_node.py           # Ground truth comparison, RMSE
│   ├── waypoint_navigator.py        # Nav2 goal sender
│   └── map_metrics.py               # Point cloud quality metrics
│
└── rviz/
    └── slam_config.rviz             # Visualization configuration
```

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GAZEBO SIMULATION                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐   │
│  │ RGBD Camera │  │     IMU     │  │ Diff Drive  │  │ Ground Truth  │   │
│  │  (30Hz)     │  │  (100Hz)    │  │  (odom)     │  │   (p3d)       │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘   │
└─────────┼────────────────┼────────────────┼─────────────────┼───────────┘
          │                │                │                 │
          ▼                ▼                ▼                 ▼
    /camera/*         /imu/data          /odom         /ground_truth/odom
          │                │                │                 │
          │                └───────┬────────┘                 │
          │                        ▼                          │
          │              ┌──────────────────┐                 │
          │              │ robot_localization│                 │
          │              │   (EKF Fusion)    │                 │
          │              └────────┬─────────┘                 │
          │                       │                           │
          │               /odometry/filtered                  │
          │                       │                           │
          ▼                       ▼                           │
┌─────────────────────────────────────────────┐               │
│              RTAB-Map SLAM                  │               │
│  ┌──────────────┐    ┌──────────────┐       │               │
│  │ Visual Mode  │    │  ICP Mode    │       │               │
│  │  (RGBD)      │    │ (PointCloud) │       │               │
│  └──────┬───────┘    └──────┬───────┘       │               │
└─────────┼───────────────────┼───────────────┘               │
          │                   │                               │
          ▼                   ▼                               ▼
    /rtabmap/cloud_map    /map (2D)              ┌────────────────────┐
          │                   │                  │  evaluation_node   │
          │                   │                  │  (RMSE, ATE)       │
          ▼                   ▼                  └────────────────────┘
    ┌─────────────────────────────────┐
    │        map_metrics.py           │
    │  (density, coverage, bbox)      │
    └─────────────────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  depthimage_to  │
          │   laserscan     │──────► /scan
          └─────────────────┘
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │      NAV2 Stack       │
                            │  - Controller Server  │
                            │  - Planner Server     │
                            │  - BT Navigator       │
                            │  - Behavior Server    │
                            └───────────┬───────────┘
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │  waypoint_navigator   │
                            │  (autonomous goals)   │
                            └───────────────────────┘
```

---

## 4. Key Topics

| Topic | Type | Source | Description |
|-------|------|--------|-------------|
| `/odom` | Odometry | Gazebo diff_drive | Wheel odometry |
| `/imu/data` | Imu | Gazebo IMU plugin | 100Hz IMU data |
| `/camera/rgb/image_raw` | Image | Gazebo camera | RGB image 640x480 |
| `/camera/depth/image_raw` | Image | Gazebo camera | Depth image |
| `/camera/depth/points` | PointCloud2 | Gazebo camera | 3D point cloud |
| `/ground_truth/odom` | Odometry | Gazebo p3d | Perfect odometry |
| `/odometry/filtered` | Odometry | robot_localization | Fused odometry |
| `/rtabmap/cloud_map` | PointCloud2 | RTAB-Map | 3D map |
| `/map` | OccupancyGrid | RTAB-Map | 2D navigation map |
| `/scan` | LaserScan | depthimage_to_laserscan | Virtual laser scan |

---

## 5. Configuration Details

### 5.1 EKF Sensor Fusion (`robot_localization.yaml`)
```yaml
Key Parameters:
- frequency: 50 Hz
- two_d_mode: true (prevents z-drift)
- odom0: /odom (wheel odometry)
  - Uses: x, y, yaw, vx, vy, vyaw
- imu0: /imu/data
  - Uses: roll, pitch, yaw, angular velocities, accelerations
  - Gravity removal: enabled
```

### 5.2 RTAB-Map Visual SLAM (`rtabmap_rgbd.yaml`)
```yaml
Key Parameters:
- Feature detector: GFTT (500 features)
- Loop closure: Bag-of-Words
- Graph optimization: g2o
- 2D mode: enabled (Optimizer/Slam2D: true)
- Grid resolution: 5cm
- Depth range: 0.1m - 4.0m
```

### 5.3 RTAB-Map ICP SLAM (`rtabmap_icp.yaml`)
```yaml
Key Parameters:
- Registration: ICP (point-to-plane)
- Voxel size: 5cm
- Max correspondence: 10cm
- ICP iterations: 30
- 3DoF constraint: enabled
```

### 5.4 Nav2 Navigation (`nav2_params.yaml`)
```yaml
Key Parameters:
- Local planner: DWB
  - max_vel_x: 0.3 m/s
  - max_vel_theta: 0.5 rad/s
- Global planner: NavFn (A*)
- Costmap resolution: 5cm
- Robot radius: 22cm
- Inflation radius: 55cm
```

---

## 6. Evaluation Metrics

### 6.1 Localization (evaluation_node.py)
- **RMSE**: Root Mean Square Error vs ground truth
- **Mean Error**: Average position error
- **Max Error**: Maximum position deviation
- Publishes every 5 seconds to console

### 6.2 Mapping (map_metrics.py)
- **Point Density**: points per cubic meter
- **Coverage Area**: 2D footprint in m²
- **Bounding Box**: X, Y, Z dimensions
- Publishes every 10 seconds to console

### 6.3 Navigation (waypoint_navigator.py)
- **Goal Success**: Tracks reached waypoints
- **Predefined Waypoints**: 5 locations in office
- **Loop Mode**: Continuous waypoint cycling

---

## 7. Launch Commands

### Quick Start (Recommended)
```bash
# Source workspace
source /opt/ros/humble/setup.bash
source ~/Documents/GitHub/hws_repo/install/setup.bash

# Full system with navigation
ros2 launch robot_project full_navigation.launch.py

# Teleop for manual control
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Alternative Launches
```bash
# SLAM only (no Nav2)
ros2 launch robot_project full_slam.launch.py

# ICP mode comparison
ros2 launch robot_project full_slam.launch.py slam_mode:=icp

# Base simulation only
ros2 launch robot_project project_bringup.launch.py

# Add SLAM separately
ros2 launch robot_project slam_rgbd.launch.py

# Add Nav2 separately
ros2 launch robot_project navigation.launch.py
```

---

## 8. SLAM Comparison: Visual vs ICP

| Aspect | Visual (RGBD) | ICP |
|--------|---------------|-----|
| Input | RGB + Depth images | Point cloud only |
| Features | ORB/GFTT visual features | Geometric structure |
| Loop Closure | Bag-of-Words | Scan matching |
| Best For | Textured environments | Geometric environments |
| CPU Usage | Moderate | Higher |
| Drift | Lower (visual constraints) | Higher (geometric only) |

---

## 9. Known Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Robot falls (z=-1000m) | EKF integrating z noise | `two_d_mode: true` |
| RViz crash | snap/apt library conflict | `QT_QPA_PLATFORM=xcb` |
| Office not spawning | xacro not processed | Use ExecuteProcess with pipe |
| RTAB-Map no features | Low texture area | Move to textured region |
| Nav2 not responding | Lifecycle not started | Wait for autostart |

---

## 10. Files Modified from HW3

### URDF Changes (`p3dx_hw2.urdf.xacro`)
```xml
<!-- Added Ground Truth Plugin -->
<gazebo>
  <plugin name="ground_truth_odom" filename="libgazebo_ros_p3d.so">
    <ros>
      <namespace>/ground_truth</namespace>
      <remapping>odom:=odom</remapping>
    </ros>
    <body_name>base_link</body_name>
    <frame_name>world</frame_name>
    <gaussian_noise>0</gaussian_noise>
  </plugin>
</gazebo>
```

---

## 11. Git Commits (This Session)

1. `83bb1bd` - Add Final Project (Phase 1): robot_project package + sensor fusion
2. `8552d74` - Add Phase 2: RTAB-Map SLAM integration
3. `9693899` - Update PROJECT_PLAN.md with implementation progress
4. `e420116` - Add Phase 5: Nav2 navigation integration
5. `24218ea` - Update PROJECT_PLAN.md: Phase 5 (Nav2) completed

---

## 12. Remaining Tasks (Phase 6: Documentation)

- [ ] Record demo video
  - [ ] Gazebo + Office World
  - [ ] SLAM mapping process
  - [ ] Ground truth vs SLAM comparison
  - [ ] Autonomous navigation

- [ ] IEEE Report (6-10 pages)
  - [ ] Abstract
  - [ ] Introduction + Literature
  - [ ] Methodology
  - [ ] Results (tables, graphs)
  - [ ] Conclusion

- [ ] Presentation (max 10 slides)
  - [ ] System architecture
  - [ ] Demo clips
  - [ ] Comparison tables

---

## 13. Test Checklist

```bash
# 1. Build verification
colcon build --packages-select robot_project --symlink-install
# Expected: Success

# 2. Launch verification
ros2 launch robot_project full_navigation.launch.py --show-args
# Expected: Shows all arguments

# 3. Topic verification (after launch)
ros2 topic list | grep -E "odom|imu|camera|map|scan"
# Expected: All topics present

# 4. TF verification
ros2 run tf2_tools view_frames
# Expected: Complete TF tree (map→odom→base_link→sensors)

# 5. Navigation test
ros2 run robot_project waypoint_navigator
# Expected: Robot navigates to predefined waypoints
```

---

**Document Generated:** 25 December 2024
**Implementation Status:** Phase 1-5 Complete, Phase 6 Pending
