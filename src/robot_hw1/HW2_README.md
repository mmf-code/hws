# Homework 2 - Sensor Integration & Visualization

**Student:** mmf
**Course:** KON414E - Principles of Robot Autonomy
**Date:** November 2025

---

## 📋 Homework Requirements

✅ **Objective:** Integrate sensors (RGBD Camera, IMU) into Pioneer 3-DX robot, test in Gazebo, and visualize in RViz.

### Assigned Sensor Configuration:
1. **RGBD Camera:** 90° FOV, 4m depth range, 30Hz frame rate
2. **IMU:** ±0.1° drift per second

---

## 📂 Project Structure

```
robot_hw1/
├── urdf/
│   └── p3dx_hw2.urdf.xacro           # Robot model with RGBD camera + IMU
├── launch/
│   ├── hw2.launch.py                 # Main launch file (Gazebo + RViz)
│   └── robot_hw1.launch.py           # HW1 nodes (cmd_vel, noisy_odom)
├── rviz/
│   └── hw2_config.rviz               # RViz configuration for sensors
├── config/
│   └── imu_multiplot.xml             # rqt_multiplot config for IMU
├── robot_hw1/
│   ├── cmd_vel_publisher.py          # Circular motion controller
│   └── noisy_odom_publisher.py       # Odometry noise simulator
└── HW2_README.md                     # This file
```

---

## 🚀 Installation & Build

### Prerequisites

```bash
# Install dependencies
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  ros-humble-rviz2 \
  ros-humble-rqt-multiplot \
  python3-numpy
```

### Build Workspace

```bash
cd ~/hws  # or your workspace path
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

---

## 🎮 Running the Simulation

### Terminal 1: Launch Gazebo + RViz + Robot

```bash
source /opt/ros/humble/setup.bash
source ~/hws/install/setup.bash
ros2 launch robot_hw1 hw2.launch.py
```

**What this does:**
- Starts Gazebo with empty world
- Spawns Pioneer 3-DX robot with RGBD camera and IMU
- Launches RViz with sensor visualization config

**Wait 5-10 seconds for Gazebo to fully load!**

---

### Terminal 2: Robot Motion Control

```bash
source /opt/ros/humble/setup.bash
source ~/hws/install/setup.bash
ros2 run robot_hw1 cmd_vel_publisher
```

**Result:** Robot moves in circular trajectory (linear: 1.0 m/s, angular: 0.5 rad/s)

---

### Terminal 3: IMU Data Visualization (rqt_multiplot)

```bash
source /opt/ros/humble/setup.bash
source ~/hws/install/setup.bash
rqt_multiplot

# In rqt_multiplot GUI:
# File → Open → ~/hws/src/robot_hw1/config/imu_multiplot.xml
```

**What you'll see:**
- Left plot: IMU Angular Velocity (X, Y, Z axes)
- Right plot: IMU Linear Acceleration (X, Y, Z axes)

---

## 📊 What to Verify

### In Gazebo:
- ✅ Pioneer 3-DX robot spawned
- ✅ Blue RGBD camera visible on top
- ✅ Green IMU sensor visible
- ✅ Robot moves in circles

### In RViz:
- ✅ **Robot Model:** Red chassis, black wheels, blue camera, green IMU
- ✅ **TF Tree:** Shows all frames (odom → base_link → camera_link, imu_link)
- ✅ **Camera View:** Live RGB feed from RGBD camera
- ✅ **Depth Cloud:** 3D point cloud from depth sensor (colorized)
- ✅ **Depth Image:** Grayscale depth image panel
- ✅ **Odometry:** Red arrows showing robot trajectory

### In rqt_multiplot:
- ✅ **Angular Velocity:** Z-axis shows ~0.5 rad/s when turning
- ✅ **Linear Acceleration:** Shows noise (±0.1° drift simulation)

---

## 📡 ROS 2 Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | Velocity commands to robot |
| `/odom` | `nav_msgs/Odometry` | Wheel odometry (with drift) |
| `/camera/rgb/image_raw` | `sensor_msgs/Image` | RGB camera feed |
| `/camera/depth/image_raw` | `sensor_msgs/Image` | Depth image |
| `/camera/depth/points` | `sensor_msgs/PointCloud2` | 3D point cloud |
| `/imu/data` | `sensor_msgs/Imu` | IMU sensor data |
| `/joint_states` | `sensor_msgs/JointState` | Wheel joint states |
| `/robot_description` | `std_msgs/String` | URDF model |

---

## 🎥 Video Recording

### Record your demonstration showing:
1. Gazebo window with robot moving
2. RViz showing:
   - Camera feed
   - Depth cloud visualization
   - Robot trajectory
3. rqt_multiplot with IMU graphs
4. All running simultaneously

### Recording Options:

**Option 1: Built-in (Ubuntu)**
```bash
Ctrl + Alt + Shift + R  # Start/Stop recording
```
Videos saved to `~/Videos/`

**Option 2: OBS Studio**
```bash
sudo apt install obs-studio
obs
```

**Video Requirements:**
- Duration: 30-60 seconds
- Show all sensor outputs
- Upload to Google Drive
- Share link in report

---

## 📝 Report Requirements

### Include in your report:

1. **Introduction:** Brief description of sensor configuration

2. **Implementation:**
   - How RGBD camera was integrated (plugin, parameters)
   - How IMU was integrated (plugin, noise parameters)
   - URDF modifications

3. **Screenshots:**
   - Screenshot 1: Gazebo + RViz side-by-side
   - Screenshot 2: Camera view in RViz
   - Screenshot 3: Depth cloud in RViz
   - Screenshot 4: rqt_multiplot showing IMU data

4. **Video Link:** Google Drive link (make sure it's accessible)

5. **Verification:**
   - Confirm sensors work correctly
   - Explain what each visualization shows
   - Mention any issues encountered

6. **Conclusion:** Summary of learning outcomes

---

## 🔍 Sensor Specifications (As Implemented)

### RGBD Camera
- **Plugin:** `gazebo_ros_camera` (depth mode)
- **Horizontal FOV:** 90° (1.5708 radians)
- **Resolution:** 640x480
- **Depth Range:** 0.1m - 4.0m
- **Frame Rate:** 30Hz
- **Position:** Front-top of robot (0.15m forward, 0.20m up)

### IMU Sensor
- **Plugin:** `gazebo_ros_imu_sensor`
- **Update Rate:** 100Hz
- **Angular Velocity Noise:** 0.001745 rad/s (±0.1°/s)
- **Linear Acceleration Noise:** 0.01 m/s²
- **Orientation Noise:** 0.001745 rad
- **Position:** Center of robot (0.10m up)

---

## 🛠️ Troubleshooting

### Gazebo doesn't start
```bash
pkill -9 gzserver gzclient
ros2 launch robot_hw1 hw2.launch.py
```

### RViz shows no camera image
- Check topic: `ros2 topic echo /camera/rgb/image_raw --once`
- Verify camera plugin in Gazebo (should publish)
- Wait 5-10 seconds after launch

### IMU data not showing
```bash
# Check IMU topic
ros2 topic echo /imu/data --once

# Check if Gazebo loaded IMU plugin
ros2 topic list | grep imu
```

### Robot doesn't move
```bash
# Verify cmd_vel publisher is running
ros2 topic echo /cmd_vel

# Check odometry updates
ros2 topic echo /odom
```

### rqt_multiplot shows nothing
- Make sure robot is launched and moving first
- Verify IMU topic exists: `ros2 topic list | grep imu`
- Check config file path is correct

---

## 📚 Technical Details

### URDF Structure
```
base_link (chassis)
├── left_wheel
├── right_wheel
├── caster_wheel
├── camera_link
│   └── camera_optical_frame (for image orientation)
└── imu_link
```

### Gazebo Plugins Used
1. **Differential Drive:** Controls robot motion
2. **Joint State Publisher:** Publishes wheel states
3. **RGBD Camera:** RGB + Depth sensor
4. **IMU Sensor:** Orientation + Angular Velocity + Linear Acceleration

---

## 🎯 Expected Results

### Camera Visualization:
- RGB image shows environment from robot's perspective
- Depth cloud shows 3D structure with color mapping
- Max range: 4 meters (objects beyond fade out)

### IMU Visualization:
- Angular velocity Z shows ~0.5 rad/s during circular motion
- Linear acceleration shows gravity (9.8 m/s² on Z-axis)
- Small noise visible due to ±0.1°/s drift parameter

### Robot Motion:
- Circular trajectory with ~2m radius
- Smooth motion (no jerky movements)
- Odometry drift accumulates over time (realistic simulation)

---

## 📞 Support

**Repository:** https://github.com/mmf/hws (or your repo)
**Issues:** Contact course TA or check ROS 2 documentation

---

**Good luck with your demonstration!** 🚀
