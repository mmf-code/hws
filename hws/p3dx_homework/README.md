# Pioneer 3-DX ROS 2 Simulation

**Student:** mmf
**Robot:** Pioneer 3-DX
**ROS Version:** ROS 2 Humble
**OS:** Ubuntu 22.04

---

## Overview

Pioneer 3-DX mobile robot simulation in ROS 2 Humble with Gazebo Classic. Ported from ROS 1 Noetic to ROS 2 Humble.

**Packages:**
- `p3dx_description` - Robot URDF and meshes
- `p3dx_control` - Controllers
- `p3dx_gazebo` - Simulation and scripts

---

## Installation

### System Requirements
- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic

### Install Dependencies

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher \
  ros-humble-xacro \
  ros-humble-plotjuggler-ros \
  python3-numpy
```

### Build Workspace

```bash
cd ~/p3dx_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## Usage

### Launch Simulation

**Terminal 1 - Gazebo:**
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 launch p3dx_gazebo p3dx.launch.py
```

**Terminal 2 - Add Odometry Noise:**
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
python3 ~/p3dx_ws/src/p3dx/p3dx_gazebo/scripts/noisy_odom_publisher.py
```

**Terminal 3 - Robot Control:**
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 run p3dx_gazebo cmd_vel_publisher.py
```

**Terminal 4 - RViz:**
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
rviz2 -d ~/p3dx_ws/src/p3dx/p3dx_description/rviz/p3dx_view.rviz
```

**Terminal 5 - Plotjuggler:**
```bash
source /opt/ros/humble/setup.bash
ros2 run plotjuggler plotjuggler
```

In Plotjuggler:
- Streaming → ROS2 Topics → Start
- Subscribe to `/odom/pose/pose/position/x` and `y`
- Create XY Plot: x vs y

---

## Scripts

### cmd_vel_publisher.py
Publishes velocity commands to make robot move in circles.
- Linear velocity: 1.0 m/s
- Angular velocity: 0.5 rad/s

### noisy_odom_publisher.py
Adds realistic noise and drift to odometry data:
- Position noise: 15 cm
- Orientation noise: ~3 degrees
- Accumulated drift over time

Subscribes to `/odom_clean` (ideal from Gazebo) and publishes to `/odom` (with noise).

---

## ROS Topics

- `/cmd_vel` - Velocity commands
- `/odom` - Noisy odometry (with drift)
- `/odom_clean` - Clean odometry from Gazebo
- `/ground_truth/pose` - Ground truth position
- `/joint_states` - Robot joint states
- `/tf` - Transform tree

---

## Odometry Drift Analysis

### Question: Does the robot pass through the same points every loop?

**Answer:** No, the trajectory shows drift over time.

### Why?

**In this simulation:**
- Added Gaussian noise to position measurements (15 cm std dev)
- Accumulated drift from systematic errors
- Orientation errors compound over time
- Similar to real wheel encoders with quantization errors

**In real robots:**
- Wheel slippage on uneven surfaces
- Encoder quantization errors
- IMU drift
- Tire deformation
- Surface variations

The noisy odometry node simulates these real-world effects, causing the robot to not return to exactly the same position after each loop.

---

## ROS 1 to ROS 2 Port Changes

**package.xml:**
- Format 2 → 3
- `<run_depend>` → `<exec_depend>`

**CMakeLists.txt:**
- `catkin` → `ament_cmake`

**Launch files:**
- XML → Python

**URDF:**
- Gazebo plugin paths updated for ROS 2
- Topic remapping syntax changed

---

## Files

**Core Files:**
- `README.md` - This file
- `QUICKSTART.md` - Quick reference
- `PROJECT_INFO.md` - Homework details
- `REALISTIC_SIMULATION.md` - Noise parameters explanation

**Scripts:**
- `scripts/cmd_vel_publisher.py` - Motion control
- `scripts/noisy_odom_publisher.py` - Odometry noise

**Config:**
- `rviz/p3dx_view.rviz` - RViz configuration
- `launch/p3dx.launch.py` - Main launch file

---

## Troubleshooting

**Gazebo not spawning robot:**
```bash
killall gzserver gzclient
```

**RViz not showing robot:**
- Check Fixed Frame is set to `odom`
- Verify `/robot_description` topic exists

**No odometry drift visible:**
- Ensure `noisy_odom_publisher.py` is running
- Check RViz Odometry display subscribes to `/odom` (not `/odom_clean`)

---

## References

- Original package: https://github.com/NKU-MobFly-Robotics/p3dx
- ROS 2 Humble docs: https://docs.ros.org/en/humble/
- Gazebo Classic: https://classic.gazebosim.org/

---

**Date:** October 2025
