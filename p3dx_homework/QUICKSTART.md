# Pioneer 3-DX Quick Start Guide

## 🚀 Quick Launch (4 Terminals)

### Terminal 1: Gazebo
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 launch p3dx_gazebo p3dx.launch.py
```
**Wait for Gazebo to fully load (5-10 seconds)**

---

### Terminal 2: Robot Movement
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 run p3dx_gazebo cmd_vel_publisher.py
```
Robot will start moving in circles

---

### Terminal 3: RViz Visualization
```bash
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
rviz2 -d ~/p3dx_ws/src/p3dx/p3dx_description/rviz/p3dx_view.rviz
```

**RViz Manual Setup (if config doesn't work):**
1. **Fixed Frame:** `odom`
2. **Add** → **RobotModel**
3. **Add** → **TF**
4. **Add** → **Odometry** (Topic: `/odom`)
5. Disable Odometry → Covariance → Position (to remove yellow noise)

---

### Terminal 4: Trajectory Plot
```bash
source /opt/ros/humble/setup.bash
ros2 run plotjuggler plotjuggler
```

**In Plotjuggler:**
1. **Streaming** → **Start** → **ROS 2 Topics**
2. Find `/odom/pose/pose/position/x` and `/odom/pose/pose/position/y`
3. Select both → Right-click → **Create XY Plot**
4. **Buffer:** 30 seconds
5. You'll see a circular trajectory

---

## 📸 Taking Screenshots

### System Info (Required for Report)
```bash
ros2 --version
whoami
hostname
```
**Screenshot this terminal output** (`PrtScn` key)

### Gazebo + RViz (Figure 2)
- Arrange windows side-by-side
- `Shift + PrtScn` → Select area

### Plotjuggler (Figure 3)
- Screenshot the X-Y plot showing circular trajectory

---

## 🎥 Recording Video

### Option 1: Built-in (Gnome)
```bash
# Start/Stop recording
Ctrl + Alt + Shift + R
```
Videos saved to `~/Videos/`

### Option 2: SimpleScreenRecorder
```bash
sudo apt install simplescreenrecorder
simplescreenrecorder
```

**What to show in video (30-60 seconds):**
- Gazebo with robot moving
- RViz with odometry trail
- Plotjuggler showing trajectory
- All running simultaneously

---

## 🛑 Stopping Everything

```bash
# Kill Gazebo
pkill -9 gzserver gzclient

# Kill all ROS nodes
pkill -9 -f ros2

# Or press Ctrl+C in each terminal
```

---

## ✅ Checklist for Homework

- [ ] Screenshot: Terminal (ros2 --version + whoami)
- [ ] Screenshot: Gazebo + RViz side-by-side
- [ ] Screenshot: Plotjuggler X-Y trajectory
- [ ] Video: 30-60 seconds showing all components
- [ ] Upload video to Google Drive
- [ ] Get shareable link
- [ ] Write report with analysis

---

## 🐛 Troubleshooting

### Gazebo doesn't open
```bash
pkill -9 gzserver gzclient
ros2 launch p3dx_gazebo p3dx.launch.py
```

### No /cmd_vel or /odom topics
```bash
# Check topics
ros2 topic list

# Restart Gazebo if missing
```

### RViz shows nothing
- Check **Fixed Frame** is `odom`
- Re-add displays
- Check `/robot_description` exists:
  ```bash
  ros2 topic echo /robot_description --once
  ```

### Robot doesn't move
```bash
# Check cmd_vel is publishing
ros2 topic echo /cmd_vel

# Check odometry is updating
ros2 topic echo /odom
```

---

## 📦 File Locations

- **Workspace:** `~/p3dx_ws/`
- **Launch files:** `~/p3dx_ws/src/p3dx/p3dx_gazebo/launch/`
- **Scripts:** `~/p3dx_ws/src/p3dx/p3dx_gazebo/scripts/`
- **URDF:** `~/p3dx_ws/src/p3dx/p3dx_description/urdf/p3dx/`
- **RViz config:** `~/p3dx_ws/src/p3dx/p3dx_description/rviz/`
- **Screenshots:** `~/Pictures/Screenshots/`
- **Videos:** `~/Videos/`

---

## 🎯 Expected Results

### Gazebo
- Pioneer 3-DX robot in empty world
- Robot moves in circular path
- Smooth motion

### RViz
- Robot model visible (frames and links)
- TF tree showing odom → base_link
- Red arrows (odometry trail) forming a circle
- Grid for reference

### Plotjuggler
- X-Y plot showing circular trajectory
- Nearly overlapping circles (minimal drift in simulation)

### Analysis
**Question:** Did robot follow same trajectory?
**Answer:** Yes, in simulation. Nearly perfect overlap.

**Why no drift?**
- Ideal Gazebo physics
- No wheel slip
- Perfect encoders
- No sensor noise

**Real world would have:**
- Wheel slippage
- Encoder errors
- Odometry drift
- Gaussian noise
- Dynamic effects

---

## 📞 Need Help?

Check full documentation: `~/p3dx_ws/README.md`

Command reference: `~/p3dx_ws/USAGE_COMMANDS.sh`
