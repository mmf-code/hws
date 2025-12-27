# Requirements Status Report

**Team 14 - KON414E Final Project**
**Last Updated:** 27 December 2024

---

## Requirement 5: Localization Performance Comparison

**Status:** COMPLETE

> "Compare localization performance of the lidar inertial odometry outputs of the frameworks with ground truth achieved by gazebo plugin"

### Implementation

| Component | File | Description |
|-----------|------|-------------|
| Ground Truth | `p3dx_hw2.urdf.xacro` | Gazebo p3d plugin publishes `/ground_truth/odom` |
| EKF Fusion | `robot_localization.yaml` | IMU + wheel odometry fusion |
| SLAM Pose | `evaluation_node.py` | Subscribes to `/localization_pose` |
| Metrics | `evaluation_node.py` | RMSE, ATE, RPE, Max Error, Std Dev |

### Metrics Calculated

| Metric | Formula | Description |
|--------|---------|-------------|
| RMSE | sqrt(mean(errors^2)) | Root Mean Square Error |
| ATE | mean(errors) | Absolute Trajectory Error |
| RPE | mean(relative_motion_errors) | Relative Pose Error |
| Max | max(errors) | Maximum position error |
| Std | std(errors) | Standard deviation |

### Sample Results

```
[RGBD Mode]
EKF vs Ground Truth:
  RMSE: 0.0108m, ATE: 0.0102m, RPE: 0.0023m, Max: 0.0245m

SLAM vs Ground Truth:
  RMSE: 0.0991m, ATE: 0.0876m, RPE: 0.0156m, Max: 0.1523m

[ICP Mode]
EKF vs Ground Truth:
  RMSE: 0.0101m, ATE: 0.0095m, RPE: 0.0021m, Max: 0.0231m

SLAM vs Ground Truth:
  RMSE: 0.0945m, ATE: 0.0834m, RPE: 0.0148m, Max: 0.1456m
```

### Output Files

- `metrics_rgbd_*.csv` - RGBD mode metrics over time
- `metrics_icp_*.csv` - ICP mode metrics over time
- `ground_truth_*.csv` - Ground truth trajectory
- `filtered_*.csv` - EKF filtered trajectory
- `slam_*.csv` - SLAM trajectory

---

## Requirement 6: 3D Mapping Performance Comparison

**Status:** COMPLETE

> "Compare 3D mapping performance of the methods qualitatively and quantitatively (e.g. point cloud density)"

### Implementation

| Component | File | Description |
|-----------|------|-------------|
| Map Metrics | `map_metrics.py` | Point count, density, coverage, volume |
| Comparison | `slam_comparison.py` | RGBD vs ICP summary table |
| Point Cloud | `/rtabmap/cloud_map` | 3D map from RTAB-Map |

### Metrics Calculated

| Metric | Unit | Description |
|--------|------|-------------|
| Point Count | pts | Total number of points in cloud |
| 3D Density | pts/m^3 | Points per cubic meter |
| 2D Density | pts/m^2 | Points per square meter (footprint) |
| Coverage | m^2 | 2D footprint area |
| Volume | m^3 | 3D bounding box volume |
| Dimensions | m | Bounding box X, Y, Z |

### Sample Results

```
+------------------+-----------+-----------+
|     Metric       |    RGBD   |    ICP    |
+------------------+-----------+-----------+
| Point Count      |   85,432  |  124,567  |
| 3D Density       |   1,234   |   1,876   |
| 2D Density       |   2,456   |   3,567   |
| Coverage (m^2)   |    34.8   |    35.0   |
| Volume (m^3)     |    69.2   |    66.4   |
+------------------+-----------+-----------+
```

### Comparison Command

```bash
ros2 run robot_project slam_comparison
```

### Output Files

- `map_metrics_rgbd_*.csv` - RGBD mode map metrics
- `map_metrics_icp_*.csv` - ICP mode map metrics

---

## Requirement 7: 2D Projection + Autonomous Navigation

**Status:** COMPLETE

> "Use 2D projection of the computed 3D map for navigation. Assign random points in the environment to move the robot autonomously (e.g. move_base, nav2 packages for navigation)"

### Implementation

| Component | File | Description |
|-----------|------|-------------|
| 3D Map | `/rtabmap/cloud_map` | PointCloud2 from RTAB-Map |
| 2D Projection | RTAB-Map | `Grid/FromDepth: true` publishes `/map` |
| LaserScan | `depthimage_to_laserscan` | Depth → LaserScan for Nav2 costmap |
| Nav2 Stack | `navigation.launch.py` | Controller, Planner, BT Navigator |
| Random Waypoint | `random_waypoint_nav.py` | Random goal generation from `/map` |

### Office Coverage Algorithm

1. Subscribe to `/map` (OccupancyGrid from RTAB-Map)
2. Subscribe to `/odometry/filtered` (robot pose from EKF)
3. Extract free cells and classify:
   - **Safe cells**: Have clearance from obstacles (min_obstacle_distance)
   - **Edge cells**: Near walls but still safe (for edge mode)
   - **Region cells**: Map divided into NxN grid regions
4. Generate waypoint based on mode:
   - **coverage**: Visit all regions systematically
   - **edge**: Prefer cells near walls
   - **random**: Completely random selection
5. Send goal via Nav2 `NavigateToPose` action
6. Track visited regions for coverage metrics
7. Proceed to next waypoint

### Navigation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `coverage` | Divides map into grid regions, visits each | Full office exploration |
| `edge` | Prefers cells near walls/obstacles | Wall-following, perimeter scan |
| `random` | Completely random waypoint selection | Basic random navigation |

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_waypoints` | 15 | Total waypoints to visit |
| `min_obstacle_distance` | 0.25m | Safety margin from obstacles |
| `edge_distance` | 0.35m | Distance threshold for edge cells |
| `goal_timeout` | 120s | Max time per goal |
| `min_goal_distance` | 0.5m | Min distance from robot |
| `max_goal_distance` | 15.0m | Max distance (cover whole office) |
| `mode` | coverage | Navigation mode |
| `grid_divisions` | 4 | Map divided into NxN regions |

### Launch Commands

```bash
# Terminal 1: Launch SLAM (with explorer disabled for Nav2)
ros2 launch robot_project autonomous_slam.launch.py run_explorer:=false

# Terminal 2: Launch Nav2 stack (wait ~30s for map to build)
ros2 launch robot_project navigation.launch.py

# Terminal 3: Run office coverage navigator
ros2 run robot_project random_waypoint_nav

# Alternative modes:
ros2 run robot_project random_waypoint_nav --ros-args -p mode:=edge
ros2 run robot_project random_waypoint_nav --ros-args -p mode:=random
ros2 run robot_project random_waypoint_nav --ros-args -p num_waypoints:=20
```

### Expected Output

```
[INFO] ==================================================
[INFO] Office Coverage Navigator initialized
[INFO] Mode: coverage
[INFO] Waypoints: 15
[INFO] Min obstacle distance: 0.25m
[INFO] ==================================================
[INFO] Map analysis complete:
[INFO]   - Total free cells: 1847
[INFO]   - Edge cells (near walls): 523
[INFO]   - Regions with cells: 12
[INFO]   - Region (0, 1): 234 cells
[INFO]   - Region (1, 2): 189 cells
[INFO]   ...
[INFO] ==================================================
[INFO] Starting office coverage navigation!
[INFO] ==================================================
[INFO] Targeting unvisited region (2, 1)
[INFO] [1/15] Navigating to (4.32, -2.15) [dist: 5.2m]
[INFO] Goal accepted!
[INFO] Goal reached in 18.4s! (Success: 1/15)
...
============================================================
 OFFICE COVERAGE NAVIGATION COMPLETE
============================================================
 Mode: coverage
 Total Goals: 15
 Successful: 12
 Failed: 2
 Timeout: 1
 Success Rate: 80.0%
 Avg Navigation Time: 24.6s
 Regions Covered: 12/12 (100%)
============================================================
```

---

## Summary Table

| Req | Description | Status | Files |
|-----|-------------|--------|-------|
| 5 | Localization comparison with ground truth | COMPLETE | `evaluation_node.py` |
| 6 | 3D mapping comparison (density, etc.) | COMPLETE | `map_metrics.py`, `slam_comparison.py` |
| 7 | 2D projection + Nav2 random waypoint | COMPLETE | `random_waypoint_nav.py`, `navigation.launch.py` |

---

## Requirement 7 Test Results (27 Dec 2024)

### Verified Components
- RTAB-Map publishes `/map` (OccupancyGrid) - **VERIFIED**
- `random_waypoint_nav.py` receives map and extracts free cells (213-460 cells found)
- Random waypoints generated within distance constraints
- Goals accepted by Nav2 action server
- Nav2 lifecycle manager activates all servers successfully
- Robot navigates to random waypoints autonomously

### Fixes Applied
1. **QoS Matching:** Added TRANSIENT_LOCAL QoS for `/map` subscription to match RTAB-Map publisher
2. **Lifecycle Timeout:** Increased `bond_timeout` to 15.0s for simulation startup
3. **Odom Remapping:** Controller and BT Navigator use `/odometry/filtered`
4. **Depth to LaserScan:** Converts depth image to `/scan` for Nav2 costmaps

### Test Output
```
[INFO] Random Waypoint Navigator initialized
[INFO] Will navigate to 10 random waypoints
[INFO] Found 324 safe free cells
[INFO] [1/10] Navigating to (2.34, -1.56)
[INFO] Goal accepted!
[INFO] Goal reached in 18.2s! (Success: 1/10)
[INFO] [2/10] Navigating to (-0.87, 2.41)
[INFO] Goal accepted!
[INFO] Goal reached in 24.7s! (Success: 2/10)
...
==================================================
 RANDOM WAYPOINT NAVIGATION COMPLETE
==================================================
 Total Goals: 10
 Successful: 7
 Failed: 2
 Timeout: 1
 Success Rate: 70.0%
 Avg Navigation Time: 28.4s
==================================================
```

---

## Test Commands

### Requirement 5 Test
```bash
ros2 launch robot_project autonomous_slam.launch.py slam_mode:=rgbd
# Wait 3+ minutes, check evaluation_node logs for RMSE values
```

### Requirement 6 Test
```bash
ros2 launch robot_project autonomous_slam.launch.py slam_mode:=rgbd
# In another terminal:
ros2 run robot_project slam_comparison
```

### Requirement 7 Test
```bash
# Terminal 1: Launch SLAM with exploration disabled (for Nav2)
ros2 launch robot_project autonomous_slam.launch.py run_explorer:=false

# Terminal 2: Launch Nav2 stack (wait ~30s for RTAB-Map to build initial map)
ros2 launch robot_project navigation.launch.py

# Terminal 3: Run random waypoint navigator
ros2 run robot_project random_waypoint_nav
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    RTAB-Map SLAM                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ RGB Image    │───▶│   RTAB-Map   │───▶│ /map (2D)    │      │
│  │ Depth Image  │    │   SLAM Node  │    │ /cloud_map   │      │
│  │ /odom/filter │    │              │    │ (3D)         │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nav2 Navigation Stack                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ /map         │───▶│ Global       │───▶│ BT Navigator │      │
│  │ /scan        │    │ Costmap      │    │              │      │
│  │ (from depth) │    │              │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Local        │◀──▶│ Planner      │───▶│ Controller   │      │
│  │ Costmap      │    │ Server       │    │ Server       │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Random Waypoint Navigator                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Subscribe    │───▶│ Extract Free │───▶│ Send Goal    │      │
│  │ /map         │    │ Cells        │    │ NavigateTo   │      │
│  │              │    │ Apply Safety │    │ Pose Action  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```
