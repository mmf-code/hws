# KON414E Homework 1 - Pioneer 3-DX Simulation

**Course:** KON414E - Principles of Robot Autonomy
**Student:** mmf
**Term:** 2025-2026 Fall
**Due Date:** 9 November 2025, 23:30

---

## 📁 Project Structure

```
p3dx_homework/
├── README.md              # Complete documentation
├── QUICKSTART.md          # Quick start guide
├── USAGE_COMMANDS.sh      # All terminal commands
├── PROJECT_INFO.md        # This file
├── scripts/
│   ├── cmd_vel_publisher.py      # Robot motion control
│   └── plot_trajectory.py        # Trajectory visualization
├── launch/
│   ├── p3dx.launch.py            # Main simulation launch
│   ├── p3dx_full.launch.py       # Full launch with controllers
│   └── simple_test.launch.py     # Basic test
├── rviz/
│   └── p3dx_view.rviz            # RViz configuration
└── screenshots/          # (Add your screenshots here)
    ├── 01_ros_version.png
    ├── 02_gazebo_rviz.png
    └── 03_trajectory_plot.png
```

---

## 🎯 Homework Requirements

### Completed Tasks:

- [x] **1. ROS 2 Installation**
  - ROS 2 Humble on Ubuntu 22.04
  - Screenshot: Terminal with `ros2 --version` + `whoami`

- [x] **2. Workspace Setup**
  - Created `~/p3dx_ws` with colcon build system
  - Three packages: p3dx_description, p3dx_control, p3dx_gazebo

- [x] **3. Robot Packages**
  - Downloaded from: https://github.com/NKU-MobFly-Robotics/p3dx
  - Ported from ROS 1 Noetic to ROS 2 Humble
  - Modified: package.xml, CMakeLists.txt, launch files, URDF plugins

- [x] **4. Gazebo Simulation**
  - Robot spawns in empty world
  - Differential drive plugin working
  - `/cmd_vel` and `/odom` topics active

- [x] **5. RViz Visualization**
  - Robot model displayed
  - TF tree visible (odom → base_link)
  - Odometry trail visualization

- [x] **6. cmd_vel Publisher Node**
  - Python script: `cmd_vel_publisher.py`
  - Linear velocity: 1.0 m/s
  - Angular velocity: 0.5 rad/s
  - Robot performs circular motion

- [x] **7. Robot Model + Odometry in RViz**
  - Custom RViz config: `p3dx_view.rviz`
  - Displays: RobotModel, TF, Odometry, Grid

- [x] **8. Odometry Tracking**
  - Plotjuggler: X-Y trajectory plot
  - Analysis: Minimal drift in simulation
  - Explanation: Ideal physics vs. real-world errors

- [ ] **9. Video Recording**
  - Record 30-60 seconds showing Gazebo + RViz
  - Upload to Google Drive
  - Add shareable link to report

- [ ] **10. Final Report**
  - Document all steps
  - Include screenshots
  - Add video link
  - Submit by deadline

---

## 🚀 How to Run (From This Directory)

### Prerequisites:
ROS workspace must be at: `~/p3dx_ws/`

If workspace is elsewhere or needs to be set up:
```bash
# See QUICKSTART.md for full installation
```

### Quick Launch:
```bash
# Terminal 1: Gazebo
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 launch p3dx_gazebo p3dx.launch.py

# Terminal 2: Robot Control
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 run p3dx_gazebo cmd_vel_publisher.py

# Terminal 3: RViz
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
rviz2 -d ~/p3dx_ws/src/p3dx/p3dx_description/rviz/p3dx_view.rviz

# Terminal 4: Plotjuggler
source /opt/ros/humble/setup.bash
ros2 run plotjuggler plotjuggler
```

See `QUICKSTART.md` for detailed instructions.

---

## 📸 Screenshots Required

1. **ROS Version + Username**
   ```bash
   ros2 --version && whoami && hostname
   ```

2. **Gazebo + RViz Side-by-Side**
   - Gazebo showing robot in empty world
   - RViz showing robot model + odometry trail

3. **Plotjuggler X-Y Trajectory**
   - Circular trajectory plot
   - X vs Y position from `/odom`

---

## 📊 Analysis Results

### Question: Did the robot consistently pass through the same points?

**Answer:** No, the robot shows realistic drift over multiple cycles (after adding noise parameters).

### Explanation: Why drift occurs even in simulation?

**Enhanced Simulation (Current Implementation):**
- ⚠️ **Odometry Noise**: Added Gaussian noise (0.05 m) to measurements
- ⚠️ **Wheel Slip**: Slip compliance parameters (0.02-0.03) simulate real friction
- ⚠️ **Surface Friction**: Non-uniform mu1/mu2 (0.8/0.7) causes directional slip
- ⚠️ **Covariance Model**: Position/orientation uncertainty accumulates over time
- ⚠️ **Encoder Source**: Using encoder-based odometry (not ground truth)

**Parameters Added to Simulation:**
```xml
<noise>0.05</noise>
<covariance_x>0.0001</covariance_x>
<covariance_y>0.0001</covariance_y>
<covariance_yaw>0.01</covariance_yaw>
<wheel_slip_compliance>0.02</wheel_slip_compliance>
<slip1>0.02</slip1>
<slip2>0.03</slip2>
<mu1>0.8</mu1>
<mu2>0.7</mu2>
```

**Real-World Comparison:**
- ❌ **Wheel Slippage**: Simulated via slip parameters
- ❌ **Encoder Errors**: Modeled with measurement noise
- ❌ **Odometry Drift**: Covariance accumulation over time
- ❌ **Surface Variations**: Different friction coefficients (mu1 ≠ mu2)
- ❌ **Sensor Noise**: Gaussian noise in odometry

**Conclusion:** With realistic parameters, simulation now shows observable drift similar to real robots. The trajectory no longer perfectly overlaps after multiple loops.

---

## 🛠️ Technical Details

### ROS 1 → ROS 2 Port Changes:

**package.xml:**
- Format 2 → Format 3
- `<run_depend>` → `<exec_depend>`
- `catkin` → `ament_cmake`

**CMakeLists.txt:**
- `find_package(catkin ...)` → `find_package(ament_cmake ...)`
- `catkin_package()` → `ament_package()`

**Launch Files:**
- XML (`.launch`) → Python (`.launch.py`)
- Different node/parameter syntax

**Gazebo Plugins:**
- Used `libgazebo_ros_diff_drive.so` (ROS 2 compatible)
- Replaced ROS 2 Control approach with simpler diff_drive plugin
- **Added Realistic Parameters**:
  - Odometry noise and covariance for sensor uncertainty
  - Wheel slip parameters for realistic friction
  - Contact dynamics (mu1, mu2, kp, kd) for surface interaction

---

## 📚 Documentation Files

- **README.md** - Complete project documentation (setup, usage, troubleshooting)
- **QUICKSTART.md** - Quick start guide for running simulation
- **USAGE_COMMANDS.sh** - Shell script with all commands
- **PROJECT_INFO.md** - This file (homework-specific info)

---

## 🔗 References

- Original Package: https://github.com/NKU-MobFly-Robotics/p3dx
- ROS 2 Docs: https://docs.ros.org/en/humble/
- Gazebo Classic: https://classic.gazebosim.org/

---

## 📝 Notes

- ROS workspace location: `~/p3dx_ws/`
- This directory contains exported files for Git/homework submission
- Full workspace required for running simulation
- Screenshots should be added to `screenshots/` folder
- Video link should be added to final report

---

## ✅ Submission Checklist

- [ ] Screenshots collected (ROS version, Gazebo+RViz, Plotjuggler)
- [ ] Video recorded (30-60 seconds)
- [ ] Video uploaded to Google Drive with public link
- [ ] Report written with all steps documented
- [ ] Analysis of odometry drift included
- [ ] Video link added to report
- [ ] Submit before: 9 November 2025, 23:30

---

**Author:** mmf
**Date:** October 2025
