# HW2 Manual Startup Guide

**Due to snap/pthread conflicts with gnome-terminal, follow these manual steps:**

---

## 🚀 Step-by-Step Startup (5 Terminals)

### Terminal 1: Launch Gazebo with Objects

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_hw1 hw2.launch.py use_rviz:=false world:=$(pwd)/worlds/hw2_world.world
```

**Wait 10 seconds for Gazebo to fully load!**

---

### Terminal 2: Launch RViz

**Open NEW terminal (Ctrl+Shift+T or right-click → New Terminal)**

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:$//')
rviz2 -d install/robot_hw1/share/robot_hw1/rviz/hw2_config.rviz
```

---

### Terminal 3: Start Robot Motion

**Open NEW terminal**

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run robot_hw1 cmd_vel_publisher
```

**Robot should now move in circles!**

---

### Terminal 4: Camera Viewer

**Open NEW terminal**

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v snap | tr '\n' ':' | sed 's/:$//')
/opt/ros/humble/lib/rqt_image_view/rqt_image_view /camera/rgb/image_raw
```

---

### Terminal 5: IMU Plotter

**Open NEW terminal**

```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
/opt/ros/humble/lib/rqt_plot/rqt_plot /imu/data/angular_velocity/x /imu/data/angular_velocity/y /imu/data/angular_velocity/z /imu/data/linear_acceleration/x /imu/data/linear_acceleration/y /imu/data/linear_acceleration/z
```

---

## ✅ Expected Result

You should now have:

1. **Gazebo:** Robot moving among colored objects (red box, green cylinder, blue box, yellow sphere)
2. **RViz:** Circular odometry path
3. **Camera:** View of colored objects as robot turns
4. **IMU Plot:** 6 graphs updating in real-time

---

## 🎥 Record Video

Once all windows are open and working:

1. Arrange windows on screen
2. Press `Ctrl + Alt + Shift + R` to start recording
3. Wait 30-60 seconds
4. Press `Ctrl + Alt + Shift + R` to stop
5. Video saved to `~/Videos/`

---

## 🛑 Stop Everything

Press `Ctrl+C` in each terminal, or:

```bash
pkill -9 gzserver gzclient
pkill -f cmd_vel_publisher
pkill -f rviz2
pkill -f rqt
```

---

**Good luck!** 🚀
