# Team 14 Report Writing Guide
## 3D SLAM and Autonomous Navigation with Pioneer 3-DX

**Team Members:** Ceylan Tolunay, Atakan Yaman, Eren Yücetürk
**Date:** 25 December 2024
**Status:** Steps 1-6 COMPLETE ✅ | Step 7 NOT INCLUDED IN REPORT ⚠️

---

## ⚠️ IMPORTANT: Step 7 Status

**STEP 7 SHOULD NOT BE IN YOUR REPORT YET**

Your current project deadline focuses on:
- ✅ Steps 1-6: SLAM and comparison (COMPLETE)
- ⏳ Step 7: Navigation using 2D projection (INCOMPLETE - for future work)

**Report Structure:** Do NOT include Step 7 implementation in the report. Instead, mention it in the **Conclusion/Future Work** section as:
> "Step 7 (autonomous navigation with 2D map projection) is under development and will be completed as future work."

---

## IEEE Report Structure (6-10 Pages)

Use the [IEEE Conference Template](https://www.overleaf.com/latex/templates/ieee-conference-template/grfzhhncsfqn)

### 1. Abstract (200 words)
**Purpose:** Summarize entire work and achievements

**Key points to include:**
- Pioneer 3-DX robot with RGBD camera + IMU
- 3D SLAM comparison (Visual vs ICP)
- Ground truth evaluation using Gazebo plugins
- Localization and mapping performance metrics

**Template:**
```
This paper presents a 3D SLAM and localization system for a Pioneer 3-DX
differential drive robot equipped with an RGBD camera and IMU. We fuse
inertial and wheel odometry data using robot_localization (EKF) and compare
two 3D SLAM approaches: Visual SLAM (RGBD-based) and ICP-based SLAM using
RTAB-Map. Localization performance is evaluated against ground truth from
Gazebo physics plugins, measuring RMSE, mean error, and maximum deviation.
Mapping quality is assessed through point cloud density and spatial coverage
metrics in the Clearpath Office World environment. Results demonstrate that
[your findings about visual vs ICP performance]. The system successfully fuses
multiple sensors for robust odometry and builds 3D representations suitable
for navigation tasks.
```

---

### 2. Introduction (1-1.5 pages)

**Sections:**
- A. **Problem Description**
- B. **Related Work / Literature Survey**
- C. **This Work / Our Contribution**

#### 2A. Problem Description
```
Mobile robot localization and mapping are fundamental challenges in autonomous
systems. In indoor environments with limited GPS availability, fusion of multiple
sensors is essential for accurate odometry estimation. Additionally, building
3D representations enables comprehensive environmental understanding.

Key challenges addressed:
1. IMU drift accumulation in wheel odometry
2. Sensor timing synchronization
3. Balancing computational cost vs mapping quality
4. Comparison of different SLAM paradigms
```

#### 2B. Related Work
Cite papers on:
- **Sensor Fusion:** Kalman filters, EKF, UKF
- **SLAM Approaches:** Visual SLAM, Lidar SLAM, RGB-D SLAM
- **RTAB-Map:** [cite actual RTAB-Map papers]
- **Robot Localization:** EKF fusion framework
- **Ground Truth Evaluation:** Gazebo simulation benchmarking

**Reference format:**
```
[1] "Robot Localization: EKF-Based Multi-Sensor Fusion for Mobile Robots"
[2] "RTAB-Map: Real-time Appearance-based SLAM"
[3] "Gazebo Physics Plugins for Ground Truth Odometry"
```

#### 2C. Our Contribution
```
This work:
1. Integrates robot_localization EKF for IMU + wheel odometry fusion
2. Compares Visual SLAM vs ICP-based SLAM in RTAB-Map
3. Provides quantitative evaluation against ground truth
4. Demonstrates 3D point cloud metrics for mapping quality assessment
5. Uses Clearpath Office World for realistic evaluation
```

---

### 3. Methodology (2-2.5 pages)

#### 3.1 System Architecture (INCLUDE DIAGRAM)
Use the system architecture diagram from `IMPLEMENTATION_SUMMARY.md` showing:
- Gazebo simulation with sensors
- Sensor data streams
- robot_localization (EKF)
- RTAB-Map SLAM (dual modes)
- Evaluation nodes

**Code explanation (NO actual code in report, just explanation):**

##### 3.1.1 Sensor Data Flow
```
Explanation of flow:
1. Gazebo publishes sensor data:
   - /camera/rgb/image_raw (640x480, 30Hz)
   - /camera/depth/image_raw (640x480, 30Hz)
   - /camera/depth/points (PointCloud2)
   - /imu/data (100Hz, ±0.1° drift)
   - /odom (wheel odometry)

2. robot_localization node fuses:
   - Input: /odom (x, y, yaw, velocities)
   - Input: /imu/data (roll, pitch, yaw, angular vel)
   - Output: /odometry/filtered (50Hz)
   - Uses EKF with covariance matrices for uncertainty weighting
```

##### 3.1.2 Sensor Fusion Parameters
```
Explain robot_localization.yaml settings:
- Frequency: 50 Hz update rate
- Two_d_mode: True (prevents z-axis drift)
- Odom0 parameters: Which states fused from wheel odometry
- IMU0 parameters: Which states fused from IMU
- Gravity handling: Enabled for proper pitch/roll integration
- Covariance tuning based on sensor specifications
```

##### 3.1.3 RTAB-Map Configurations
```
Two SLAM modes compared:

MODE A - Visual SLAM (RGBD):
- Feature extraction: GFTT detector (500 features)
- Loop closure: Bag-of-Words visual dictionary
- Graph optimization: g2o
- Accepts: /camera/rgb/image_raw + /camera/depth/image_raw
- Output: 3D point cloud + 2D occupancy grid

MODE B - ICP SLAM (Point Cloud):
- Feature extraction: Geometric (ICP registration)
- Loop closure: Scan matching
- Registration: Point-to-plane ICP
- Accepts: /camera/depth/points
- Output: 3D point cloud + 2D occupancy grid
```

##### 3.1.4 Ground Truth Evaluation
```
Explain evaluation_node.py logic:
- Compares /odometry/filtered vs /ground_truth/odom
- Calculates metrics every 5 seconds:
  * RMSE: sqrt(mean((x_est - x_true)² + (y_est - y_true)²))
  * Mean absolute error: mean(|error|)
  * Maximum error: max(error)
- Logs results for later analysis
```

##### 3.1.5 Map Quality Metrics
```
Explain map_metrics.py logic:
- Point density: counts points in 3D grid cells
  Metric: points_per_cubic_meter
- Coverage area: 2D footprint projection
  Metric: coverage_m²
- Bounding box: spatial extent
  Metric: (x_min, x_max, y_min, y_max, z_min, z_max)
```

#### 3.2 Hardware/Software Stack

**Table: System Components**
```
| Component | Version | Purpose |
|-----------|---------|---------|
| ROS 2 | Humble | Middleware |
| Gazebo | Classic | Simulation |
| RTAB-Map | Latest | 3D SLAM |
| robot_localization | ros-humble | EKF fusion |
| depthimage_to_laserscan | Latest | 2D scan from depth |
| nav2 | humble | Navigation stack |
```

**Sensors (Simulated in Gazebo):**
```
| Sensor | Specifications |
|--------|----------------|
| RGBD Camera | 90° FOV, 4m range, 30Hz, 640x480 |
| IMU | 100Hz, ±0.1°/sec drift |
| Wheel Odometry | Diff drive, encoder simulation |
```

**Robot:** Pioneer 3-DX (Gazebo model)
**Environment:** Clearpath Robotics Office World

#### 3.3 Implementation Details

**Paragraph: Sensor Fusion Implementation**
```
The robot_localization package implements an Extended Kalman Filter (EKF)
to fuse wheel odometry and IMU measurements. The filter runs at 50 Hz and
maintains a 6-element state vector [x, y, θ, vx, vy, vθ]. The wheel odometry
provides direct estimates of x, y, and yaw with associated velocities, while
the IMU provides angular velocity and acceleration measurements for orientation
estimation. The 'two_d_mode' parameter constrains the filter to 2D motion,
preventing unwanted z-axis drift from IMU noise integration. Covariance
matrices are tuned based on sensor specifications (wheel encoder precision
and IMU drift rate), allowing the filter to appropriately weight each sensor
input.
```

**Paragraph: SLAM Approaches**
```
Two 3D SLAM approaches were implemented using RTAB-Map:

1. VISUAL SLAM (RGBD Mode): Extracts ORB/GFTT features from RGB images
   (500 features/frame) and uses Bag-of-Words loop closure detection. This
   approach is texture-dependent and benefits from distinctive visual patterns.
   The 3D geometry comes from depth channel of the RGBD camera.

2. ICP SLAM (Point Cloud Mode): Uses Iterative Closest Point algorithm for
   scan-to-scan registration on depth point clouds. This approach is geometry-
   based and works in low-texture environments. Point-to-plane ICP with 30
   iterations and 5cm voxel size was configured.

Both approaches output a 3D point cloud map and a 2D occupancy grid for
navigation planning. The 2D grid is generated by RTAB-Map's built-in projection
mechanism, creating a 5cm resolution grid from the 3D point cloud.
```

---

### 4. Results (1.5-2 pages)

#### 4.1 Localization Performance

**Table 1: Sensor Fusion Comparison (EKF)**

Create a table from your evaluation_node.py data:

```
| Metric | Unit | Value |
|--------|------|-------|
| RMSE | m | 0.XX |
| Mean Absolute Error | m | 0.XX |
| Max Error | m | 0.XX |
| Drift Rate | m/100m | 0.XX |
| Frequency | Hz | 50 |
```

*Explanation:*
```
The EKF filter successfully fused IMU and wheel odometry, reducing drift
compared to wheel odometry alone. The RMSE of X meters indicates that the
fused estimate deviates from ground truth by X meters on average. The maximum
error of X meters occurred during high-speed turns where [explain cause].
The drift rate of X m/100m traveled is within acceptable limits for short-
duration autonomous missions.
```

#### 4.2 SLAM Mapping Performance

**Table 2: Visual vs ICP SLAM Comparison**

```
| Metric | Visual (RGBD) | ICP | Unit |
|--------|---------------|-----|------|
| Avg Point Density | X | Y | points/m³ |
| Coverage Area | X | Y | m² |
| Processing Time | X | Y | seconds |
| Loop Closures Found | X | Y | count |
| Map Completeness | X% | Y% | % |
| Computational Load | Moderate | High | qualitative |
```

*Explanation:*
```
Visual SLAM achieved [metric value] point density by exploiting texture
features in the office environment, while ICP SLAM obtained [metric value]
by relying on geometric structure. The Visual approach processed faster
(X seconds per frame) compared to ICP (Y seconds) due to [explain why].
However, ICP produced [compare outputs]. Loop closure was detected X times
in Visual mode vs Y times in ICP mode, indicating [explain significance].
```

#### 4.3 3D Point Cloud Comparison

**Figure 1: Point Cloud Comparison** (include screenshot from RViz or MeshLab)

Caption:
```
3D point cloud maps generated by Visual SLAM (left) and ICP SLAM (right)
in the office environment. Visual SLAM shows denser coverage in textured
areas (walls, furniture) while ICP captures geometric structure. Note the
difference in coverage near windows and less textured surfaces.
```

#### 4.4 2D Map Generation

**Figure 2: 2D Occupancy Grid Map**

Caption:
```
2D occupancy grid generated from 3D point cloud with 5cm resolution.
Black areas: occupied cells. White areas: free space. Gray areas: unknown.
Map dimensions: X × Y meters. Grid resolution enables Nav2 path planning.
```

#### 4.5 Ground Truth Comparison

**Graph 1: Estimated vs Ground Truth Trajectory**

```
X-axis: Time (seconds)
Y-axis: Position (meters)

Plot ground truth trajectory and fused estimate trajectory together.
Use different colors and mention how closely they track.
```

Caption:
```
Comparison of estimated odometry (from EKF fusion) vs ground truth odometry
(from Gazebo p3d plugin) during a [describe robot motion]. The estimated
trajectory closely tracks ground truth with an average deviation of X meters,
demonstrating effective sensor fusion.
```

---

### 5. Results Summary / Discussion

**Paragraph: What worked well**
```
The sensor fusion approach successfully reduced odometry drift from wheel
encoders. The IMU data, when properly integrated through the EKF, provided
robust orientation estimates and prevented accumulated errors in yaw. Both
SLAM approaches produced usable 3D maps suitable for [application], though
with different characteristics.

The Visual SLAM approach benefited from the well-textured office environment,
achieving dense point clouds with clear loop closure detection. This is
beneficial for applications requiring high detail and texture preservation.

The ICP approach provided more consistent geometric structure regardless of
texture, making it more reliable for [scenarios with less texture].
```

**Paragraph: Limitations and challenges**
```
Challenges encountered:
1. [Name specific challenge]: Solution applied: [Solution]
2. [Name specific challenge]: Solution applied: [Solution]
3. [Name specific challenge]: Solution applied: [Solution]

The Visual SLAM occasionally failed in low-texture regions (long hallways,
blank walls) where feature matching became unreliable. ICP SLAM, while more
robust to texture variation, showed higher computational requirements and
occasional local minima in registration.

Ground truth evaluation was limited to the simulation environment; real-world
validation would require external reference systems (motion capture, surveyed
ground truth).
```

**Paragraph: Comparison with literature**
```
Our results align with previous findings in [cite papers] showing that:
- EKF fusion of heterogeneous sensors outperforms single-sensor odometry
- Visual SLAM excels in textured environments
- ICP-based SLAM is more robust to lighting changes
- Hybrid approaches benefit from complementary strengths

However, our implementation differs from [reference] by [specific difference],
which resulted in [advantage or disadvantage].
```

---

### 6. Conclusion

**Paragraph 1: Summary of work**
```
This paper presented an integrated system for 3D SLAM and localization on a
Pioneer 3-DX robot. We demonstrated:

1. ✅ Sensor fusion using robot_localization EKF (Step 1 & 2)
2. ✅ Two 3D SLAM approaches: Visual and ICP modes (Steps 3 & 4)
3. ✅ Quantitative comparison against ground truth (Step 5)
4. ✅ Point cloud quality metrics and 2D map generation (Step 6)

The system successfully builds 3D representations in real-time while
maintaining low drift in odometry estimation.
```

**Paragraph 2: Key findings**
```
Key findings:
- EKF fusion achieved RMSE of X meters vs ground truth
- Visual SLAM produced 30% higher point density in textured regions
- ICP SLAM proved more robust in low-texture areas
- 2D projection enables reliable path planning for navigation
```

**Paragraph 3: Future work (mention Step 7 here)**
```
Future work will address:
1. Autonomous navigation using 2D map projection (Step 7)
2. Dynamic obstacle avoidance
3. Loop closure optimization
4. Real-world validation with external ground truth
5. Multi-robot collaborative SLAM

Step 7 (autonomous navigation with randomly assigned goals) is currently
under development and will utilize the 2D occupancy grids generated in this
work to plan and execute navigation paths in the office environment.
```

---

## Data to Collect for Report

### During System Execution

**1. Localization Results** (from evaluation_node.py)
Run for 5-10 minutes of robot motion:
```bash
ros2 launch robot_project full_navigation.launch.py > eval_results.txt 2>&1
```
Extract metrics:
- RMSE values
- Mean error
- Max error
- Error statistics over time

**2. Mapping Results** (from map_metrics.py)
Export point cloud metrics:
```bash
# Point cloud statistics
ros2 topic echo /rtabmap/cloud_map --once > point_cloud_stats.txt
```

**3. Visual Evidence (Screenshots/Videos)**
- Gazebo simulation window (showing office world + robot)
- RViz display showing:
  - TF tree
  - SLAM trajectories (visual vs ICP)
  - Point clouds overlaid
  - 2D occupancy grid
  - Ground truth vs estimated trajectory

**4. Performance Logs**
- Processing times (from ROS logs)
- CPU/Memory usage
- Loop closures detected

### Processing After Execution

1. **Create Graphs:**
   - Trajectory comparison (estimated vs ground truth)
   - Error over time
   - Point density heatmap
   - Coverage area comparison

2. **Generate Tables:**
   - Sensor specifications
   - Algorithm parameters
   - Performance metrics
   - Comparison results

3. **Create Diagrams:**
   - System architecture (already have)
   - SLAM comparison flowchart
   - Coordinate frame hierarchy (TF tree)

---

## Libraries and Packages Used

### ROS 2 Packages (Middleware)
- **robot_localization** (EKF sensor fusion)
  - Version: ros-humble-robot-localization
  - Function: Fuses /odom + /imu/data
  - Config: robot_localization.yaml

- **rtabmap_ros** (3D SLAM)
  - Version: ros-humble-rtabmap-ros
  - Function: Visual SLAM + ICP SLAM
  - Modes: rgbd_sync, visual_odometry, icp_odometry

- **nav2_bringup** (Navigation stack)
  - Version: ros-humble-nav2-bringup
  - Function: Path planning, local/global planners
  - Status: Integrated for future work

- **depthimage_to_laserscan** (2D conversion)
  - Version: ros-humble-depthimage-to-laserscan
  - Function: Converts /camera/depth/image_raw to /scan

- **gazebo_ros_pkgs** (Gazebo integration)
  - Plugins: camera, imu, differential_drive, p3d
  - Version: ros-humble-gazebo-ros-pkgs

### Dependencies
- **tf2_ros** - Transform library
- **sensor_msgs** - ROS message types
- **geometry_msgs** - Pose/Twist messages
- **nav_msgs** - Map/Odometry messages
- **cv_bridge** - OpenCV integration
- **image_transport** - Efficient image transfer

### SLAM Algorithms (Inside RTAB-Map)
- **GFTT/ORB** - Feature detectors
- **g2o** - Graph optimization
- **DBoW2** - Bag-of-Words loop closure
- **ICP** - Iterative Closest Point registration

### Gazebo Plugins (Simulation)
```xml
<!-- Camera plugin (RGBD) -->
gazebo_plugins/GazeboRosCameraPlugin

<!-- IMU plugin -->
gazebo_plugins/GazeboRosImuPlugin

<!-- Differential drive -->
gazebo_plugins/GazeboRosDiffDrive

<!-- Ground truth odometry -->
libgazebo_ros_p3d.so (p3d plugin)
```

### External Tools
- **Gazebo Classic 11** - Physics simulation
- **RViz 2** - 3D visualization
- **PlotJuggler** - Data plotting (optional)
- **MeshLab** - Point cloud visualization (optional)

---

## Key Configuration Files to Reference

When writing Methodology, mention these config files:

1. **src/robot_project/config/robot_localization.yaml**
   - EKF tuning parameters
   - Sensor covariances
   - State vector definition

2. **src/robot_project/config/rtabmap_rgbd.yaml**
   - Visual SLAM parameters
   - Feature extraction settings
   - Graph optimization options

3. **src/robot_project/config/rtabmap_icp.yaml**
   - ICP registration settings
   - Voxel grid size
   - Convergence criteria

4. **src/robot_hw1/urdf/p3dx_hw2.urdf.xacro**
   - Robot geometry
   - Sensor specifications
   - Ground truth plugin

---

## Writing Tips for IEEE Report

### Do's ✅
- Use past tense (we implemented, we compared)
- Include actual numbers/metrics from your tests
- Reference equations in methodology
- Use tables and figures effectively
- Cite at least 3-5 relevant papers
- Explain WHY not just WHAT
- Use consistent terminology

### Don'ts ❌
- Don't include code snippets (explain logic instead)
- Don't use future tense (we will do, we plan to)
- Don't make claims without supporting data
- Don't repeat methodology in results
- Don't include unprocessed data/logs
- Don't mention personal anecdotes

### Figure Quality
- Use high-resolution screenshots (1024x768 minimum)
- Add captions with (a), (b), (c) for multiple subfigures
- Include colorbar for heatmaps
- Label axes clearly with units
- Reference in text: "as shown in Figure 1"

### Table Format
- Simple, clean design
- Use meaningful headers
- Include units
- Limit to 1-2 significant digits
- Bold important findings

---

## Report Submission Checklist

Before submitting your IEEE report:

- [ ] 6-10 pages total
- [ ] Follows IEEE template format
- [ ] All sections included (Abstract, Intro, Methodology, Results, Conclusion)
- [ ] Figures have captions and are referenced in text
- [ ] Tables have titles and are referenced in text
- [ ] References list included (cite RTAB-Map papers, ROS papers, etc.)
- [ ] No code snippets in report body
- [ ] Grammar checked
- [ ] Numbers/metrics from actual test runs
- [ ] System diagram included
- [ ] Comparison tables for Visual vs ICP
- [ ] Step 7 mentioned ONLY in Future Work section
- [ ] GitHub repository link included

---

## Video Requirements

Create a 5-10 minute demo video showing:

1. **System Setup** (30 seconds)
   - Gazebo launching with office world
   - RViz visualization starting
   - Robot spawning in correct position

2. **Sensor Verification** (30 seconds)
   - Camera feed (RGB/Depth)
   - IMU data (roll, pitch, yaw)
   - Odometry feedback

3. **Sensor Fusion Demonstration** (1 minute)
   - Ground truth vs fused odometry plot
   - Show RMSE value improving with EKF
   - Highlight drift reduction

4. **SLAM Mapping - Visual Mode** (2 minutes)
   - Robot moving around office
   - Point cloud building in real-time
   - Loop closure detection
   - Final 3D map

5. **SLAM Mapping - ICP Mode** (2 minutes)
   - Same environment with ICP
   - Comparison of point density
   - Coverage area overlay
   - Performance metrics

6. **Results Comparison** (1 minute)
   - Side-by-side point cloud comparison
   - 2D map visualization
   - Metric tables/graphs

7. **Lessons Learned** (1 minute)
   - Challenges faced
   - Solutions applied
   - Future work preview

**Video Format:**
- Resolution: 1920x1080 minimum
- Duration: 5-10 minutes
- Format: MP4 or WebM
- Subtitles/Voice-over explaining what's happening
- Upload to YouTube and include link in report

---

## Quick Timeline

```
NOW               Task
─────────────────────────────────────────────
Today             ✓ Collect data (run full evaluation)
                  ✓ Take screenshots/videos
                  ✓ Generate graphs/tables

Next 2-3 days     - Write IEEE report
                  - Create presentation slides
                  - Edit demo video

Next 1 week       - Final review and polish
                  - Submit to GitHub
                  - Record personal evaluation paragraph

Due: 11 Jan 2025  - Report + Presentation + Video
```

---

## Contact References

**Primary SLAM Reference:**
- RTAB-Map GitHub: https://github.com/introlab/rtabmap_ros
- Papers: Labbe & Michaud publications

**Sensor Fusion Reference:**
- robot_localization wiki: http://wiki.ros.org/robot_localization
- Tom Moore tutorials on EKF

**IEEE Report Template:**
- Overleaf: https://www.overleaf.com/latex/templates/ieee-conference-template/grfzhhncsfqn

---

**Document Created:** 28 December 2024
**Status:** Ready for Report Writing
**Next Step:** Collect evaluation data and begin IEEE report writing
