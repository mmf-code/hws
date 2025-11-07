# Pioneer 3-DX ROS 2 Simulation - KON414E Homework 1

**Student:** mmf
**Robot:** Pioneer 3-DX
**ROS Version:** ROS 2 Humble
**Platform:** Ubuntu 22.04
**Original Package:** https://github.com/NKU-MobFly-Robotics/p3dx
**Original Author:** CHAN JIAN LE (brucechanjianle)

---

## Project Summary

This project implements a Pioneer 3-DX differential drive robot simulation in ROS 2 Humble with Gazebo Classic. The original ROS 1 Noetic package was ported to ROS 2 and extended with realistic odometry noise to demonstrate sensor drift effects.

---

## Package Structure

```
~/p3dx_ws/src/p3dx/
├── p3dx_description/        # Robot URDF models (from original repo)
│   ├── urdf/
│   │   └── p3dx/
│   │       ├── pioneer3dx.xacro
│   │       ├── pioneer3dx_wheel.xacro (modified: added friction params)
│   │       └── pioneer3dx_plugins_simple.xacro (modified: odom_clean topic)
│   ├── meshes/             # 3D models (from original repo)
│   └── rviz/
│       └── p3dx_view.rviz  # Custom RViz config
├── p3dx_control/           # Controller configs (from original repo)
└── p3dx_gazebo/            # Simulation launch files
    ├── launch/
    │   └── p3dx.launch.py  # Main launch file (ported to ROS 2)
    └── scripts/
        ├── cmd_vel_publisher.py      # NEW: Circular motion controller
        └── noisy_odom_publisher.py   # NEW: Adds drift to odometry
```

---

## Installation

### Prerequisites
```bash
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher \
  ros-humble-xacro \
  ros-humble-plotjuggler-ros \
  python3-numpy
```

### Build
```bash
cd ~/p3dx_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

---

## Running the Simulation

### Terminal 1: Gazebo Simulation
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 launch p3dx_gazebo p3dx.launch.py
```

### Terminal 2: Odometry Noise (for drift effect)
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
python3 ~/p3dx_ws/src/p3dx/p3dx_gazebo/scripts/noisy_odom_publisher.py
```

### Terminal 3: Robot Motion Control
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 run p3dx_gazebo cmd_vel_publisher.py
```

### Terminal 4: Visualization
```bash
# RViz
env -i HOME=$HOME DISPLAY=$DISPLAY USER=$USER PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
bash -c 'source /opt/ros/humble/setup.bash && source ~/p3dx_ws/install/setup.bash && \
export QT_QPA_PLATFORM=xcb && rviz2 -d ~/p3dx_ws/src/p3dx/p3dx_description/rviz/p3dx_view.rviz'

# Plotjuggler (for trajectory plot)
source /opt/ros/humble/setup.bash
ros2 run plotjuggler plotjuggler
# Subscribe to /odom/pose/pose/position/{x,y} and create XY plot
```

---

## Implementation Details

### 1. ROS 1 to ROS 2 Port

**Changes made to original package:**

**package.xml:**
- Format 2 → Format 3
- `<run_depend>` → `<exec_depend>`
- `catkin` → `ament_cmake`

**Launch files:**
- Converted from XML to Python
- Updated node names and parameters for ROS 2 API

**URDF plugins:**
- Updated Gazebo plugin names for ROS 2 compatibility

### 2. Robot Motion Control (Homework Requirement 6)

**File:** `scripts/cmd_vel_publisher.py`

**Purpose:** Publishes velocity commands to `/cmd_vel` topic

**Parameters:**
- Linear velocity: 1.0 m/s (forward)
- Angular velocity: 0.5 rad/s (rotation)
- Publish rate: 10 Hz

**Result:** Robot moves in circular trajectory

**Code origin:** Written from scratch for this homework

### 3. Odometry Drift Simulation

**Initial Problem:**
The original Gazebo simulation had **perfect odometry** with no drift. The robot returned to exactly the same position after each loop, which is unrealistic.

**Why was it perfect?**
- Gazebo's `libgazebo_ros_diff_drive.so` plugin provides ideal encoder readings
- No sensor noise
- No wheel slip simulation
- Perfect friction model

**Solution Implemented:**
Created `noisy_odom_publisher.py` to add realistic noise

**How it works:**
1. Gazebo plugin publishes clean odometry to `/odom_clean`
2. `noisy_odom_publisher.py` subscribes to `/odom_clean`
3. Adds Gaussian noise and accumulated drift
4. Publishes noisy odometry to `/odom`
5. RViz and other nodes use `/odom` (with drift)

**Noise parameters:**
```python
position_noise = 0.15        # 15 cm position uncertainty
orientation_noise = 0.05     # ~3 degrees heading error
drift_rate = 0.005          # Accumulated error per update
```

**Modified files for noise:**
- `pioneer3dx_plugins_simple.xacro`: Changed odometry topic from `/odom` to `/odom_clean`
- `pioneer3dx_wheel.xacro`: Added surface friction parameters (mu1, mu2, slip)

**Code origin:** Written from scratch for this homework

---

## Odometry Drift Analysis (Homework Requirement 8)

### Question: Did the robot consistently pass through the same points?

**Answer:** No. The trajectory shows visible drift over multiple loops.

### Explanation

**Without noise (initial state):**
- Robot trajectory was perfectly circular
- Each loop overlapped exactly
- Unrealistic for real robots

**With noise (current implementation):**
- Trajectory forms a spiral pattern
- Inner and outer circles visible in Plotjuggler
- Drift accumulates over time

**Why drift occurs:**

**In simulation:**
- Added Gaussian noise to position measurements (15 cm std dev)
- Systematic drift accumulation (0.5 cm per update)
- Orientation errors compound over time

**In real robots (what we're simulating):**
- Wheel encoder quantization errors
- Tire deformation and slip
- Uneven floor surfaces
- IMU drift
- Mechanical backlash

**Result:** The odometry topic `/odom` now behaves like a real wheel encoder system with accumulated errors, which is why the robot does not return to the same position after each loop.

---

## ROS Topics

| Topic | Publisher | Description |
|-------|-----------|-------------|
| `/cmd_vel` | cmd_vel_publisher.py | Velocity commands |
| `/odom_clean` | Gazebo diff_drive plugin | Ideal odometry (no drift) |
| `/odom` | noisy_odom_publisher.py | Realistic odometry (with drift) |
| `/ground_truth/pose` | Gazebo p3d plugin | True robot pose |
| `/joint_states` | Gazebo joint publisher | Wheel joint states |
| `/tf` | robot_state_publisher | Transform tree |

---

## Files Overview

### From Original Repository
- `p3dx_description/urdf/` - Robot URDF models
- `p3dx_description/meshes/` - 3D mesh files
- `p3dx_gazebo/launch/` - Launch files (ported to ROS 2)

### Modified from Original
- `pioneer3dx_plugins_simple.xacro` - Changed odom topic name
- `pioneer3dx_wheel.xacro` - Added friction parameters

### Created for Homework
- `cmd_vel_publisher.py` - Circular motion controller
- `noisy_odom_publisher.py` - Drift simulation
- `p3dx_view.rviz` - RViz configuration
- All documentation files

---

## Screenshots Required for Report

1. Terminal showing ROS 2 version and username
2. Gazebo (left) and RViz (right) side-by-side
3. Plotjuggler showing X-Y trajectory with drift

---

## References

- Original package: https://github.com/NKU-MobFly-Robotics/p3dx
- Author: CHAN JIAN LE (brucechanjianle@gmail.com)
- ROS 2 Humble documentation: https://docs.ros.org/en/humble/
- Pioneer 3-DX specifications: Adept MobileRobots

---

**Date:** October 2025
**Course:** KON414E - Principles of Robot Autonomy
