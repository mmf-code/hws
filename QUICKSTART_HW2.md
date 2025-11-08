# HW2 Quick Start Guide

**Repository:** ~/Documents/GitHub/hws_repo
**Date:** November 8, 2025

---

## ⚡ Quick Start (3 Terminals)

### Terminal 1: Launch Gazebo + Robot (NO RViz due to libpthread bug)

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_hw1 hw2.launch.py use_rviz:=false
```

**Wait 10 seconds for Gazebo to fully load!**

---

### Terminal 2: Start Robot Motion

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run robot_hw1 cmd_vel_publisher
```

**Robot should now move in circles! (linear: 1.0 m/s, angular: 0.5 rad/s)**

---

### Terminal 3: Launch RViz (Manually)

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
rviz2 -d install/robot_hw1/share/robot_hw1/rviz/hw2_config.rviz
```

**If RViz crashes with libpthread error:**

```bash
# Fix: Remove snap version, install apt version
sudo snap remove rviz2
sudo apt install ros-humble-rviz2
```

---

### Terminal 4 (OPTIONAL): IMU Visualization

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
rqt_multiplot
```

**In rqt_multiplot GUI:**
- File → Open → `install/robot_hw1/share/robot_hw1/config/imu_multiplot.xml`

---

## ✅ Verify Everything Works

### Check Sensors are Publishing:

```bash
ros2 topic list | grep -E 'camera|imu'
```

Expected output:
```
/camera/rgbd_camera/camera_info
/camera/rgbd_camera/depth/image_raw
/camera/rgbd_camera/image_raw
/camera/rgbd_camera/points
/imu/data
```

### Check Camera Data:

```bash
ros2 topic echo /camera/rgbd_camera/image_raw --once
```

### Check IMU Data:

```bash
ros2 topic echo /imu/data --once
```

### Check Robot Motion:

```bash
ros2 topic echo /cmd_vel
```

Expected output (repeating):
```
linear:
  x: 1.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.5
```

---

## 📊 What to See in RViz

1. **Robot Model**: Red chassis, blue camera, green IMU
2. **Camera View**: Live RGB feed from robot's perspective
3. **Depth Point Cloud**: 3D colored point cloud (max 4m range)
4. **Odometry Path**: Red arrows showing robot trajectory
5. **TF Tree**: All coordinate frames connected

---

## 📊 What to See in rqt_multiplot

1. **Left Plot**: IMU Angular Velocity (X, Y, Z)
   - Z-axis should show ~0.5 rad/s when robot turns
2. **Right Plot**: IMU Linear Acceleration (X, Y, Z)
   - Shows noise (±0.1° drift simulation)
   - Z-axis shows gravity (~9.8 m/s²)

---

## 🎥 Recording Your Video

**Required Shots:**

1. **Gazebo Window**: Show robot moving in empty world
2. **RViz Window**: Show all of:
   - Camera RGB feed
   - Depth point cloud
   - Robot trajectory (red path)
   - Robot model with sensors
3. **rqt_multiplot**: Show IMU graphs updating in real-time
4. **All 3 windows visible simultaneously** (use screen recording)

**Recording Options:**

**Option 1: Ubuntu Built-in (Ctrl+Alt+Shift+R)**
- Press `Ctrl+Alt+Shift+R` to start/stop
- Videos saved to `~/Videos/`

**Option 2: OBS Studio**
```bash
sudo apt install obs-studio
obs
```

**Video Requirements:**
- Duration: 30-60 seconds
- Show sensor data updating
- Show robot moving
- Upload to Google Drive with public link

---

## 🐛 Troubleshooting

### RViz libpthread error
```
/opt/ros/humble/lib/rviz2/rviz2: symbol lookup error:
/snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0:
undefined symbol: __libc_pthread_init
```

**Solution:**
```bash
sudo snap remove rviz2
sudo apt install ros-humble-rviz2
```

### Robot doesn't move
- Make sure Terminal 2 (`cmd_vel_publisher`) is running
- Check: `ros2 topic echo /cmd_vel` should show data

### Camera shows no image in RViz
- Wait 10-15 seconds after launch
- Check topic: `ros2 topic list | grep camera`
- Verify in Gazebo: camera should be visible (blue box on robot)

### IMU not working
```bash
ros2 topic echo /imu/data --once
```
- Should show orientation, angular_velocity, linear_acceleration

### Gazebo crashes
```bash
pkill -9 gzserver gzclient
ros2 launch robot_hw1 hw2.launch.py use_rviz:=false
```

---

## 📝 Report Checklist

**Include in your report:**

- [ ] Screenshot: Gazebo + RViz side-by-side
- [ ] Screenshot: Camera RGB view in RViz
- [ ] Screenshot: Depth point cloud in RViz
- [ ] Screenshot: rqt_multiplot showing IMU data
- [ ] Video link (Google Drive, public access)
- [ ] Explanation of sensor integration (URDF modifications)
- [ ] Explanation of sensor specifications (90° FOV, 4m depth, ±0.1° drift)

---

## 📚 File Structure

```
~/Documents/GitHub/hws_repo/
├── src/robot_hw1/
│   ├── urdf/p3dx_hw2.urdf.xacro       # Robot model + sensors
│   ├── launch/hw2.launch.py           # Main launch file
│   ├── rviz/hw2_config.rviz           # RViz configuration
│   ├── config/imu_multiplot.xml       # IMU plot config
│   ├── robot_hw1/
│   │   ├── cmd_vel_publisher.py       # Motion controller
│   │   └── noisy_odom_publisher.py    # Odometry noise
│   └── HW2_README.md                  # Full documentation
├── build/                             # Build artifacts (ignored)
├── install/                           # Install artifacts (ignored)
└── log/                               # Log files (ignored)
```

---

**Good luck!** 🚀

For detailed technical documentation, see [HW2_README.md](src/robot_hw1/HW2_README.md)
