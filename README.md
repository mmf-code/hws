# ROS 2 Mobile Robot Autonomy

A ROS 2 autonomy stack for a simulated Pioneer 3-DX mobile robot, combining sensor fusion, RGB-D perception, SLAM, autonomous exploration, navigation, and quantitative evaluation against Gazebo ground truth.

The system runs in Gazebo Classic and uses `robot_localization` for EKF-based state estimation, RTAB-Map for 3D mapping, a custom depth-based exploration controller, and Nav2 for goal-directed navigation.

`ROS 2 Humble` · `Gazebo` · `RTAB-Map` · `Nav2` · `robot_localization` · `Python`

---

## Overview

The project follows the complete mobile-robot autonomy pipeline:

```text
Gazebo simulation
       │
       ├── wheel odometry
       ├── IMU
       ├── RGB camera
       └── depth camera
              │
              ▼
      state estimation
              │
       EKF sensor fusion
              │
              ▼
      /odometry/filtered
              │
       ┌──────┴─────────────┐
       │                    │
       ▼                    ▼
   RTAB-Map            robot control
   3D SLAM             manual / auto
       │                    │
       ▼                    ▼
  point cloud           /cmd_vel
  occupancy map              │
       │                     │
       └─────────┬───────────┘
                 ▼
                Nav2
                 │
                 ▼
          autonomous navigation
```

A separate evaluation pipeline compares estimated poses with Gazebo ground truth and records localization and mapping metrics to CSV.

---

## Main Components

### Sensor Fusion

Wheel odometry and IMU measurements are fused with `robot_localization`.

The EKF publishes:

```text
/odometry/filtered
```

and runs at:

```text
50 Hz
```

The filter is configured in 2D mode for a ground mobile robot and uses separate state contributions from wheel odometry and IMU data.

```text
/odom ───────────┐
                 │
                 ▼
              EKF
                 │
                 ▼
       /odometry/filtered
                 ▲
                 │
/imu/data ───────┘
```

Configuration:

```text
src/robot_project/config/robot_localization.yaml
```

---

## SLAM

The project uses RTAB-Map for 3D mapping and localization.

Two mapping approaches were explored:

### RGB-D Visual SLAM

Visual SLAM uses synchronized RGB and depth data from the simulated RGB-D camera.

The system performs:

- RGB-D registration
- visual feature extraction
- loop-closure detection
- pose-graph optimization
- 3D point-cloud generation
- 2D occupancy-grid generation

Main outputs:

```text
/rtabmap/cloud_map
/map
```

### ICP-Based Mapping

A geometric mapping configuration was also tested using ICP-based registration.

This provides an alternative to visual feature matching and allows comparison between appearance-based and geometry-based mapping behavior.

The repository includes recorded ICP map-metric runs for quantitative analysis.

---

## Autonomous Exploration

The project contains a custom ROS 2 exploration controller designed for SLAM data collection.

The controller processes the depth image by splitting it into five horizontal regions:

```text
far left
left
center
right
far right
```

For each region, the nearest valid obstacle distance is estimated.

```text
depth image
     │
     ▼
five-region distance extraction
     │
     ▼
obstacle state
     │
     ▼
control policy
     │
     ▼
/cmd_vel
```

The autonomous behavior handles several conditions:

- clear path
- obstacle approaching
- critical front obstacle
- wall on left or right
- narrow corridors
- corners
- stuck detection
- reverse-and-turn recovery

The controller runs at 10 Hz.

---

## Control Modes

The exploration controller supports three modes.

### Manual

Direct keyboard control through a PyGame interface.

```text
W / S    forward / reverse
A / D    turn left / right
Q / E    ±90° rotation
R        180° rotation
1-5      speed level
Esc      emergency stop
```

### Auto

Depth-based autonomous exploration with obstacle avoidance.

The controller attempts to move through the environment while keeping enough clearance for useful SLAM observations.

### Turbo

Runs the autonomous controller with a higher velocity multiplier.

The mode can be toggled interactively from the PyGame interface.

---

## Special Motion Control

The controller includes odometry-based fixed-angle rotations.

For example:

```text
Q → +90°
E → -90°
R → 180°
```

The target heading is calculated from the current fused odometry orientation and normalized to the `[-π, π]` range.

The rotation terminates once the heading error reaches a small angular tolerance.

---

## Navigation with Nav2

The repository also integrates the ROS 2 Navigation Stack.

The navigation launch includes:

- `controller_server`
- `planner_server`
- `behavior_server`
- `bt_navigator`
- lifecycle management

RTAB-Map provides the occupancy map while the EKF provides filtered odometry.

Depth images are also converted into a synthetic `LaserScan` for navigation.

```text
depth image
     │
     ▼
depthimage_to_laserscan
     │
     ▼
   /scan
     │
     ▼
    Nav2
```

The full stack can be launched with:

```bash
ros2 launch robot_project full_navigation.launch.py
```

Navigation is implemented and integrated, but the quantitative evaluation in this repository focuses primarily on localization and mapping rather than navigation success rate or path efficiency.

---

## Ground-Truth Evaluation

Gazebo publishes a reference pose through:

```text
/ground_truth/odom
```

A custom evaluation node compares this trajectory against:

```text
/odometry/filtered
/localization_pose
```

The evaluator performs timestamp matching and calculates:

- RMSE
- Absolute Trajectory Error
- Relative Pose Error
- maximum position error
- standard deviation

The node also records trajectory and metric history to CSV.

```text
ground truth ─────────┐
                     │
EKF estimate ─────────┼──► evaluation node
                     │
SLAM estimate ────────┘
                     │
                     ▼
           RMSE / ATE / RPE
                     │
                     ▼
                    CSV
```

Implementation:

```text
src/robot_project/robot_project/evaluation_node.py
```

---

## Map Evaluation

A second evaluation node analyzes the RTAB-Map point cloud.

It subscribes to:

```text
/rtabmap/cloud_map
```

and calculates:

- point count
- 3D point density
- 2D projected density
- 2D bounding-box coverage
- 3D bounding-box volume
- map dimensions
- vertical range
- map growth over time

Implementation:

```text
src/robot_project/robot_project/map_metrics.py
```

---

## Example ICP Mapping Run

One recorded ICP run progresses from:

```text
4,327 points
```

to:

```text
82,314 points
```

over approximately one minute of recorded mapping metrics.

The final sample from that run reports approximately:

```text
Point count      82,314
3D density       223.39 pts/m³
2D density       492.14 pts/m²
2D coverage      167.26 m²
```

The repository contains raw CSV results so mapping behavior can be inspected directly rather than only through summary figures.

---

## EKF Evaluation

The project also evaluates fused odometry against the Gazebo reference trajectory.

Recorded project results include localization errors on the centimeter scale for the EKF estimate in the simulated environment.

The evaluation code itself is kept in the repository, allowing the metrics to be recomputed from new test runs rather than relying only on static reported numbers.

---

## Launching the SLAM Stack

Build the workspace:

```bash
source /opt/ros/humble/setup.bash

colcon build --symlink-install

source install/setup.bash
```

Launch the main SLAM environment:

```bash
ros2 launch robot_project slam_hybrid.launch.py
```

The launch file starts:

```text
Gazebo
Pioneer 3-DX
office environment
robot_state_publisher
EKF sensor fusion
depth-to-LaserScan conversion
RTAB-Map
hybrid exploration controller
map evaluation
RViz
```

---

## Start Mode

The controller can start in different modes.

Manual:

```bash
ros2 launch robot_project slam_hybrid.launch.py \
  start_mode:=manual
```

Automatic:

```bash
ros2 launch robot_project slam_hybrid.launch.py \
  start_mode:=auto
```

Set a different base velocity:

```bash
ros2 launch robot_project slam_hybrid.launch.py \
  base_speed:=1.2
```

Disable RViz:

```bash
ros2 launch robot_project slam_hybrid.launch.py \
  use_rviz:=false
```

---

## Full Navigation Stack

Launch RTAB-Map and Nav2 together:

```bash
ros2 launch robot_project full_navigation.launch.py
```

The launch sequence initializes the main components in stages so that Gazebo, robot state, sensors, localization, mapping, and navigation become available in a predictable order.

---

## Useful ROS Topics

| Topic | Type | Purpose |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/Twist` | Robot velocity commands |
| `/odom` | `nav_msgs/Odometry` | Wheel odometry |
| `/imu/data` | `sensor_msgs/Imu` | IMU measurements |
| `/odometry/filtered` | `nav_msgs/Odometry` | EKF fused state |
| `/ground_truth/odom` | `nav_msgs/Odometry` | Gazebo reference trajectory |
| `/camera/rgbd_camera/image_raw` | `sensor_msgs/Image` | RGB image |
| `/camera/rgbd_camera/depth/image_raw` | `sensor_msgs/Image` | Depth image |
| `/camera/depth/points` | `sensor_msgs/PointCloud2` | Depth point cloud |
| `/scan` | `sensor_msgs/LaserScan` | Depth-derived laser scan |
| `/rtabmap/cloud_map` | `sensor_msgs/PointCloud2` | Global 3D point cloud |
| `/map` | `nav_msgs/OccupancyGrid` | 2D occupancy map |
| `/localization_pose` | `geometry_msgs/PoseWithCovarianceStamped` | SLAM pose estimate |

---

## System Architecture

```text
                         Gazebo Classic
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
         wheel odom           IMU              RGB-D
            │                  │                  │
            └──────────┬───────┘                  │
                       ▼                          │
               robot_localization                │
                     EKF                          │
                       │                          │
                       ▼                          │
             /odometry/filtered                  │
                       │                          │
             ┌─────────┴─────────┐                │
             │                   │                │
             ▼                   ▼                ▼
        RTAB-Map            controller       depth processing
             │                   │                │
      ┌──────┴──────┐            │                │
      ▼             ▼            │                ▼
 point cloud   occupancy grid     │             /scan
      │             │            │                │
      └──────┬──────┘            │                │
             │                   │                │
             ▼                   ▼                ▼
          evaluation          /cmd_vel           Nav2
             │                                    │
             ▼                                    ▼
          CSV metrics                         navigation
```

---

## Repository Structure

```text
.
├── README.md
│
├── src/
│   ├── robot_hw1/
│   │   ├── launch/
│   │   ├── urdf/
│   │   ├── worlds/
│   │   └── ...
│   │
│   └── robot_project/
│       ├── config/
│       │   ├── robot_localization.yaml
│       │   ├── rtabmap_rgbd.yaml
│       │   ├── rtabmap_icp.yaml
│       │   └── nav2_params.yaml
│       │
│       ├── launch/
│       │   ├── slam_hybrid.launch.py
│       │   ├── full_navigation.launch.py
│       │   └── view_map.launch.py
│       │
│       ├── robot_project/
│       │   ├── hybrid_slam_controller.py
│       │   ├── evaluation_node.py
│       │   ├── map_metrics.py
│       │   └── ...
│       │
│       └── rviz/
│
├── project/
│   ├── results/
│   │   └── data/
│   ├── FINAL_REPORT.md
│   ├── FINAL_REPORT_DATA.md
│   └── README.md
│
├── p3dx_homework/
├── hw3/
├── worlds/
└── scripts/
```

---

## Earlier Work in the Repository

The repository grew through several robotics exercises before the final autonomy stack.

### Pioneer 3-DX ROS 2 Port

An earlier stage migrated Pioneer 3-DX packages from ROS 1 concepts into a ROS 2 workflow.

It includes:

- URDF/Xacro robot description
- differential-drive simulation
- Gazebo integration
- RViz visualization

### Sensor Integration

The robot model was extended with:

- RGB-D camera
- IMU
- noisy odometry
- simulated sensor behavior

### Autonomous Corridor Navigation

An intermediate stage explored simple autonomous navigation and obstacle handling in an office-style environment before the larger SLAM project was built.

These components remain in the repository as part of the development history.

---

## Design Notes

This is a simulation-focused robotics project, not a production mobile-robot stack.

Several design choices reflect that scope:

- Gazebo provides deterministic ground truth for evaluation
- obstacle avoidance is heuristic and depth-based
- the exploration controller is separate from Nav2
- launch sequencing uses timed startup actions
- mapping metrics use axis-aligned bounding-box approximations
- evaluation focuses primarily on translational trajectory error
- navigation is integrated but not evaluated with a full benchmark suite

The goal of the project is to study how sensing, state estimation, mapping, control, navigation, and evaluation fit together as one ROS 2 system.

---

## Project Context

The project originated in the KON414E Principles of Robot Autonomy course at Istanbul Technical University.

The final project was developed by:

```text
Ceylan Tolunay
Atakan Yaman
Eren Yucetürk
```

The repository is kept public as a record of the complete autonomy pipeline and the experimental evaluation data produced during development.

---

## Author

Atakan Yaman

[GitHub](https://github.com/mmf-code) · [LinkedIn](https://linkedin.com/in/atakanyaman)
