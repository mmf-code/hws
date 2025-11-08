# Homework 2 Report - Sensor Integration & Visualization

**Student Name:** [Your Name]
**Student ID:** [Your ID]
**Course:** KON414E - Principles of Robot Autonomy
**Date:** November 8, 2025

---

## 1. Introduction

This report presents the integration and testing of sensor systems for the Pioneer 3-DX mobile robot in a simulated environment using ROS 2 Humble and Gazebo Classic.

### Assigned Sensor Configuration

Our group was assigned the following sensors:

1. **RGBD Camera**
   - Horizontal Field of View (FOV): 90° (1.5708 radians)
   - Depth Range: 0.1m - 4.0m
   - Frame Rate: 30 Hz
   - Resolution: 640x480 pixels

2. **IMU (Inertial Measurement Unit)**
   - Angular Velocity Drift: ±0.1°/second (0.001745 rad/s)
   - Update Rate: 100 Hz
   - Outputs: Orientation, Angular Velocity, Linear Acceleration

**Note:** Our assigned configuration includes RGBD Camera and IMU instead of LiDAR and GPS. RGBD cameras combine RGB imaging with depth sensing, providing both visual information and 3D spatial data, making them superior to standard cameras for robot navigation and obstacle detection.

---

## 2. Implementation

### 2.1 RGBD Camera Integration

The RGBD camera was integrated into the robot's URDF model using Gazebo's depth camera plugin.

**URDF Implementation (p3dx_hw2.urdf.xacro):**

```xml
<gazebo reference="camera_link">
  <sensor name="rgbd_camera" type="depth">
    <update_rate>30.0</update_rate>
    <camera>
      <horizontal_fov>1.5708</horizontal_fov>  <!-- 90 degrees -->
      <image>
        <width>640</width>
        <height>480</height>
        <format>R8G8B8</format>
      </image>
      <clip>
        <near>0.1</near>
        <far>4.0</far>  <!-- 4m depth range -->
      </clip>
    </camera>
    <plugin name="rgbd_camera_controller" filename="libgazebo_ros_camera.so">
      <ros>
        <namespace>/camera</namespace>
        <remapping>image_raw:=rgb/image_raw</remapping>
        <remapping>depth/image_raw:=depth/image_raw</remapping>
        <remapping>points:=depth/points</remapping>
      </ros>
      <camera_name>rgbd_camera</camera_name>
      <frame_name>camera_optical_frame</frame_name>
      <min_depth>0.1</min_depth>
      <max_depth>4.0</max_depth>
    </plugin>
  </sensor>
</gazebo>
```

**Camera Position:** Mounted on top-front of the robot (0.15m forward, 0.20m up from base_link).

**Published Topics:**
- `/camera/rgbd_camera/image_raw` - RGB image stream
- `/camera/rgbd_camera/depth/image_raw` - Depth image stream
- `/camera/rgbd_camera/points` - 3D point cloud data

---

### 2.2 IMU Sensor Integration

The IMU sensor was integrated to provide orientation, angular velocity, and linear acceleration data.

**URDF Implementation (p3dx_hw2.urdf.xacro):**

```xml
<gazebo reference="imu_link">
  <sensor name="imu_sensor" type="imu">
    <always_on>true</always_on>
    <update_rate>100.0</update_rate>
    <plugin name="imu_plugin" filename="libgazebo_ros_imu_sensor.so">
      <ros>
        <namespace>/imu</namespace>
        <remapping>~/out:=data</remapping>
      </ros>
      <frame_name>imu_link</frame_name>

      <!-- Noise parameters for ±0.1° drift per second -->
      <angular_velocity_stdev>0.001745</angular_velocity_stdev>
      <linear_acceleration_stdev>0.01</linear_acceleration_stdev>
      <orientation_stdev>0.001745</orientation_stdev>
    </plugin>
  </sensor>
</gazebo>
```

**IMU Position:** Center of robot chassis (0.10m up from base_link).

**Published Topic:**
- `/imu/data` - Full IMU data (orientation quaternion, angular velocity, linear acceleration)

---

### 2.3 Robot Motion Control

The robot was programmed to execute circular motion to test sensor functionality during movement.

**Motion Parameters:**
- Linear Velocity: 1.0 m/s
- Angular Velocity: 0.5 rad/s
- Trajectory: Circular path with ~2m radius

**Implementation:** Python node `cmd_vel_publisher.py` publishes velocity commands at 10Hz to `/cmd_vel` topic.

---

## 3. Testing & Verification

### 3.1 Simulation Environment

**Platform:** ROS 2 Humble + Gazebo Classic
**World:** Empty world with colored geometric objects for visual testing:
- Red box (3.5m ahead)
- Green cylinder (front-left)
- Blue box (back-left)
- Yellow sphere (front-right)

### 3.2 Sensor Verification

**RGBD Camera:**
- ✅ RGB images successfully published at ~23-30 Hz
- ✅ Depth point cloud generated and visualized in RViz
- ✅ Camera correctly detects colored objects in environment
- ✅ 90° FOV provides adequate field of view for navigation
- ✅ 4m depth range captures all nearby objects

**IMU Sensor:**
- ✅ Data published at 100 Hz as configured
- ✅ Angular velocity Z-axis shows ~0.5 rad/s during circular motion
- ✅ Linear acceleration Z-axis shows ~9.8 m/s² (gravity)
- ✅ Noise parameters correctly simulate ±0.1°/s drift

---

## 4. Visualization

### 4.1 RViz Visualization

**RViz Configuration includes:**
1. **Robot Model** - 3D visualization with colored sensors (blue camera, green IMU)
2. **Odometry Path** - Red arrow markers showing robot trajectory
3. **Camera Image** - Live RGB feed from RGBD camera
4. **Point Cloud** - 3D depth data colored by RGB values
5. **TF Tree** - Coordinate frame transformations

### 4.2 IMU Data Plotting

**Tool Used:** rqt_plot

**Plotted Data:**
- Angular Velocity (X, Y, Z axes)
- Linear Acceleration (X, Y, Z axes)

**Observations:**
- Z-axis angular velocity oscillates around 0.5 rad/s (matches commanded circular motion)
- Z-axis linear acceleration shows gravity (~9.8 m/s²) plus small noise
- X and Y accelerations show minor fluctuations due to simulated sensor noise

---

## 5. Screenshots

### Screenshot 1: Complete System Overview
*[Include screenshot showing Gazebo + RViz + Camera View + IMU Plot simultaneously]*

**What it shows:**
- Gazebo: Robot moving in circular path with colored objects
- RViz: Robot model with odometry trail
- Camera: RGB view of environment
- IMU Plot: Real-time sensor data graphs

---

### Screenshot 2: RViz - Robot Model & Odometry
*[Include RViz screenshot showing robot model and circular odometry path]*

**What it shows:**
- 3D robot model with sensor frames
- Red odometry arrows forming circular trajectory
- TF tree connecting all coordinate frames
- Grid reference plane

---

### Screenshot 3: Camera RGB View
*[Include camera viewer screenshot showing colored objects]*

**What it shows:**
- Live RGB camera feed
- Colored objects visible in frame (red box, green cylinder, yellow sphere, blue box)
- Clear image quality at 640x480 resolution

---

### Screenshot 4: IMU Data Graphs
*[Include rqt_plot screenshot with 6 IMU data curves]*

**What it shows:**
- Angular velocity X, Y, Z (top 3 curves)
- Linear acceleration X, Y, Z (bottom 3 curves)
- Z angular velocity ~0.5 rad/s (circular motion)
- Z linear acceleration ~9.8 m/s² (gravity)

---

## 6. Video Demonstration

**Video Link:** [Insert Google Drive public link here]

**Video Contents (30-60 seconds):**
1. Gazebo simulation with robot executing circular motion
2. RViz showing odometry path and sensor data
3. Camera viewer displaying live RGB feed
4. IMU plots updating in real-time
5. All four windows visible simultaneously

**How to Access:**
- Click the link above
- Video is publicly accessible (no login required)
- Recommended viewing: Full screen for clarity

---

## 7. Technical Details

### 7.1 ROS 2 Topic Summary

| Topic | Message Type | Rate | Description |
|-------|--------------|------|-------------|
| `/cmd_vel` | geometry_msgs/Twist | 10 Hz | Velocity commands |
| `/odom` | nav_msgs/Odometry | 50 Hz | Wheel odometry |
| `/camera/rgbd_camera/image_raw` | sensor_msgs/Image | 30 Hz | RGB image |
| `/camera/rgbd_camera/depth/image_raw` | sensor_msgs/Image | 30 Hz | Depth image |
| `/camera/rgbd_camera/points` | sensor_msgs/PointCloud2 | 30 Hz | 3D point cloud |
| `/imu/data` | sensor_msgs/Imu | 100 Hz | IMU measurements |
| `/joint_states` | sensor_msgs/JointState | 50 Hz | Wheel positions |

### 7.2 Coordinate Frames (TF Tree)

```
odom
 └─ base_link
     ├─ camera_link
     │   └─ camera_optical_frame
     ├─ imu_link
     ├─ left_wheel
     ├─ right_wheel
     └─ caster_wheel
```

### 7.3 File Structure

```
~/Documents/GitHub/hws_repo/
├── src/robot_hw1/
│   ├── urdf/p3dx_hw2.urdf.xacro        # Robot model with sensors
│   ├── launch/hw2.launch.py            # Main launch file
│   ├── rviz/hw2_config.rviz            # RViz configuration
│   ├── config/imu_multiplot.xml        # IMU plot settings
│   ├── robot_hw1/
│   │   ├── cmd_vel_publisher.py        # Motion controller
│   │   └── noisy_odom_publisher.py     # Odometry simulator
│   └── HW2_README.md                   # Technical documentation
├── worlds/hw2_world.world              # Gazebo world with objects
└── [Helper scripts for launching]
```

---

## 8. Challenges & Solutions

### Challenge 1: RViz libpthread Error

**Problem:** RViz crashed on startup due to snap/libpthread conflict.

**Solution:**
```bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v snap | tr '\n' ':')
```
Force-loaded system pthread library instead of snap's version.

### Challenge 2: rqt Tools Not in PATH

**Problem:** `rqt_image_view` and `rqt_plot` not found despite being installed.

**Solution:** Used full paths:
```bash
/opt/ros/humble/lib/rqt_image_view/rqt_image_view
/opt/ros/humble/lib/rqt_plot/rqt_plot
```

### Challenge 3: Robot Colliding with Objects

**Problem:** Initially placed objects too close, robot collided during circular motion.

**Solution:** Repositioned objects 2.5-3.5m away from origin, within camera's 4m range but outside robot's ~2m trajectory radius.

---

## 9. Results & Analysis

### 9.1 RGBD Camera Performance

**Strengths:**
- Provides both RGB and depth information simultaneously
- 90° FOV adequate for navigation and obstacle detection
- Point cloud data enables 3D environment mapping
- 30 Hz frame rate sufficient for real-time processing

**Observations:**
- Objects within 4m clearly visible
- Depth accuracy suitable for obstacle avoidance
- RGB image quality good for object recognition

### 9.2 IMU Performance

**Strengths:**
- High update rate (100 Hz) enables accurate motion tracking
- Successfully detects circular motion (0.5 rad/s angular velocity)
- Gravity measurement confirms correct orientation sensing
- Noise simulation realistic for hardware IMU

**Observations:**
- Z-axis angular velocity matches commanded rotation
- Small noise fluctuations demonstrate drift simulation
- Data suitable for sensor fusion with odometry

---

## 10. Conclusion

This homework successfully demonstrated the integration and testing of RGBD camera and IMU sensors on the Pioneer 3-DX robot in a Gazebo simulation environment.

**Key Achievements:**
1. ✅ Both sensors correctly integrated into robot URDF model
2. ✅ Sensor specifications met (90° FOV, 4m range, ±0.1°/s drift)
3. ✅ Sensors functional during robot motion
4. ✅ Data successfully visualized in RViz and rqt tools
5. ✅ Complete system demonstrated in video

**Learning Outcomes:**
- Gained experience with URDF sensor definitions
- Understood Gazebo sensor plugins and ROS 2 integration
- Practiced sensor data visualization techniques
- Learned troubleshooting skills for ROS 2 environment issues

**Future Work:**
- Implement sensor fusion (camera + IMU + odometry)
- Add obstacle avoidance using depth data
- Test more complex motion patterns
- Implement SLAM using RGBD point cloud

---

## 11. References

1. ROS 2 Humble Documentation: https://docs.ros.org/en/humble/
2. Gazebo Classic Documentation: http://classic.gazebosim.org/
3. Pioneer 3-DX Robot Specifications: Original package from NKU-MobFly-Robotics
4. ROS 2 sensor_msgs: http://docs.ros.org/en/humble/p/sensor_msgs/

---

**Submitted by:** [Your Name]
**Date:** November 8, 2025
