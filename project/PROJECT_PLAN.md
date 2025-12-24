# Team 14 - Final Projesi Uygulama Planı

## 3D SLAM and Autonomous Navigation with Pioneer 3-DX

**Takım:** Ceylan Tolunay, Atakan Yaman, Eren Yücetürk
**Robot:** Pioneer 3-DX
**Sensörler:** RGBD Camera (90° FOV, 4m, 30Hz) + IMU (±0.1°/s drift)
**World:** Clearpath Robotics Office World
**Teslim:** 10 Ocak 2025 (Sunum), 11 Ocak 2025 (Rapor)

---

## 🚀 UYGULAMA DURUMU

| Faz | Durum | Açıklama |
|-----|-------|----------|
| **Faz 1: Altyapı** | ✅ Tamamlandı | Ground truth plugin, EKF config, proje yapısı |
| **Faz 2: Sensor Fusion** | ✅ Tamamlandı | robot_localization EKF (IMU + wheel odom) |
| **Faz 3: RTAB-Map SLAM** | ✅ Tamamlandı | Visual (RGBD) + ICP configs, launch files |
| **Faz 4: Değerlendirme** | ✅ Tamamlandı | evaluation_node, map_metrics nodes |
| **Faz 5: Navigation** | ⏳ Devam Ediyor | Nav2 entegrasyonu |
| **Faz 6: Dokümantasyon** | ⏳ Bekliyor | Rapor, sunum, video |

**Son Güncelleme:** 25 Aralık 2024

---

## 1. Proje Özeti

### 1.1 Orijinal Gereksinimler (PDF'den)
1. `robot_localization` ile IMU + wheel odometry fusion
2. RGBD depth → PointCloud2 dönüşümü (gerekirse)
3. `faster_lio` **veya benzeri** ile 3D map building
4. `fast_lio` **veya benzeri** ile 3D map building
5. Ground truth ile lokalizasyon karşılaştırması
6. 3D mapping performans karşılaştırması (kalitatif + kantitatif)
7. 3D map'in 2D projeksiyonu ile Nav2 navigation

### 1.2 Sensör Uyumu Analizi

| Paket | Sensör Gereksinimi | Bizim Sensörler | Uyum |
|-------|-------------------|-----------------|------|
| FAST-LIO | 3D LiDAR + IMU | RGBD + IMU | ❌ |
| faster-lio | 3D LiDAR + IMU | RGBD + IMU | ❌ |
| **RTAB-Map** | RGBD + IMU | RGBD + IMU | ✅ |
| **ORB-SLAM3** | Mono/Stereo/RGBD + IMU | RGBD + IMU | ✅ |

**Sonuç:** "or similar" ifadesine dayanarak **RTAB-Map** ve **ORB-SLAM3** (veya RTAB-Map'in farklı modları) kullanılacak.

---

## 2. Mevcut Durum (HW3'ten Devralınan)

### 2.1 Çalışan Bileşenler
```
✅ Pioneer 3-DX URDF modeli (src/robot_hw1/urdf/p3dx_hw2.urdf.xacro)
✅ RGBD Camera plugin - /camera/depth/points (PointCloud2)
✅ IMU plugin - /imu/data (100Hz)
✅ Differential drive - /odom, /cmd_vel
✅ Office World entegrasyonu (hw3/src/cpr_office_gazebo/)
✅ RViz konfigürasyonları
✅ Temel obstacle avoidance (corridor_navigator.py)
```

### 2.2 Topic Yapısı (HW3)
```
/odom                          → nav_msgs/Odometry (wheel odometry)
/imu/data                      → sensor_msgs/Imu
/camera/depth/points           → sensor_msgs/PointCloud2
/camera/rgb/image_raw          → sensor_msgs/Image
/camera/depth/image_raw        → sensor_msgs/Image
/cmd_vel                       → geometry_msgs/Twist
/tf, /tf_static                → TF tree
```

### 2.3 Bileşen Durumu (Güncel)
```
✅ Ground truth odometry (Gazebo p3d plugin) - TAMAMLANDI
✅ robot_localization (EKF sensor fusion) - TAMAMLANDI
✅ RTAB-Map SLAM (Visual + ICP configs) - TAMAMLANDI
⏳ Nav2 navigation stack - DEVAM EDİYOR
⏳ 3D → 2D map projection - DEVAM EDİYOR
✅ Evaluation node - TAMAMLANDI
✅ Map metrics node - TAMAMLANDI
✅ Waypoint navigator (temel) - TAMAMLANDI
```

---

## 3. Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            GAZEBO SIMULATION                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ RGBD Camera │  │     IMU     │  │ Diff Drive  │  │ Ground Truth  │  │
│  │  (depth)    │  │  (100Hz)    │  │  (odom)     │  │   (p3d)       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘  │
└─────────┼────────────────┼────────────────┼─────────────────┼──────────┘
          │                │                │                 │
          ▼                ▼                ▼                 ▼
    /camera/depth    /imu/data          /odom           /ground_truth
    /points                                              /odom
          │                │                │                 │
          │                └───────┬────────┘                 │
          │                        ▼                          │
          │            ┌───────────────────────┐              │
          │            │  robot_localization   │              │
          │            │    (EKF Fusion)       │              │
          │            │  IMU + Wheel Odom     │              │
          │            └───────────┬───────────┘              │
          │                        │                          │
          │                 /odometry/filtered                │
          │                        │                          │
          ▼                        ▼                          │
┌─────────────────────────────────────────────┐               │
│              SLAM METHODS                    │               │
│  ┌─────────────────┐  ┌─────────────────┐   │               │
│  │   RTAB-Map      │  │   RTAB-Map      │   │               │
│  │  (Config A)     │  │  (Config B)     │   │               │
│  │  Visual Odom    │  │  ICP Odom       │   │               │
│  └────────┬────────┘  └────────┬────────┘   │               │
│           │                    │            │               │
│           ▼                    ▼            │               │
│     /rtabmap/               /rtabmap_icp/   │               │
│     cloud_map               cloud_map       │               │
└─────────────┬─────────────────┬─────────────┘               │
              │                 │                             │
              ▼                 ▼                             ▼
      ┌───────────────────────────────────────────────────────────┐
      │                  EVALUATION NODE                          │
      │  - Localization error (RMSE vs ground truth)              │
      │  - Point cloud density comparison                         │
      │  - Map coverage analysis                                  │
      └───────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   2D Map Projection     │
                    │   (octomap_server or    │
                    │    rtabmap's grid_map)  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                           /map (OccupancyGrid)
                                 │
                    ┌────────────┴────────────┐
                    │      NAV2 STACK         │
                    │  - AMCL localization    │
                    │  - Planner server       │
                    │  - Controller server    │
                    │  - BT Navigator         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Waypoint Navigator    │
                    │   (Random goal points)  │
                    └─────────────────────────┘
```

---

## 4. Kurulum Gereksinimleri

### 4.1 Apt Paketleri
```bash
# Temel paketler
sudo apt update
sudo apt install -y \
    ros-humble-robot-localization \
    ros-humble-rtabmap-ros \
    ros-humble-rtabmap-slam \
    ros-humble-rtabmap-odom \
    ros-humble-rtabmap-viz \
    ros-humble-octomap-server \
    ros-humble-octomap-rviz-plugins \
    ros-humble-depthimage-to-laserscan \
    ros-humble-nav2-bringup \
    ros-humble-nav2-bt-navigator \
    ros-humble-nav2-map-server \
    ros-humble-nav2-amcl \
    ros-humble-nav2-planner \
    ros-humble-nav2-controller \
    ros-humble-nav2-behaviors \
    ros-humble-nav2-lifecycle-manager
```

### 4.2 Tahmini Disk Alanı
```
robot-localization:  ~5 MB
rtabmap-ros:         ~200 MB
nav2-bringup:        ~150 MB
octomap:             ~20 MB
─────────────────────────────
TOPLAM:              ~400 MB
```

---

## 5. Uygulama Adımları

### FAZA 1: Altyapı Hazırlığı (1-2 gün)

#### Adım 1.1: Paket Kurulumu
```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash

# Paketleri kur
sudo apt install -y ros-humble-robot-localization ros-humble-rtabmap-ros \
    ros-humble-nav2-bringup ros-humble-octomap-server

# Workspace'i rebuild et
colcon build --symlink-install
source install/setup.bash
```

#### Adım 1.2: URDF'e Ground Truth Plugin Ekleme
`src/robot_hw1/urdf/p3dx_hw2.urdf.xacro` dosyasına eklenecek:

```xml
<!-- Ground Truth Odometry Plugin (for evaluation) -->
<gazebo>
  <plugin name="p3d_base_controller" filename="libgazebo_ros_p3d.so">
    <ros>
      <namespace>/ground_truth</namespace>
      <remapping>odom:=odom</remapping>
    </ros>
    <body_name>base_link</body_name>
    <frame_name>world</frame_name>
    <update_rate>50.0</update_rate>
    <xyz_offset>0 0 0</xyz_offset>
    <rpy_offset>0 0 0</rpy_offset>
    <gaussian_noise>0</gaussian_noise>
  </plugin>
</gazebo>
```

#### Adım 1.3: Proje Klasör Yapısı
```
project/
├── PROJECT_PLAN.md              # Bu dosya
├── config/
│   ├── robot_localization.yaml  # EKF parametreleri
│   ├── rtabmap_config_a.yaml    # RTAB-Map Visual Odom config
│   ├── rtabmap_config_b.yaml    # RTAB-Map ICP Odom config
│   ├── nav2_params.yaml         # Nav2 parametreleri
│   └── mapper_params.yaml       # Octomap parametreleri
├── launch/
│   ├── project_bringup.launch.py      # Ana launch
│   ├── sensor_fusion.launch.py        # robot_localization
│   ├── slam_rtabmap_a.launch.py       # RTAB-Map Config A
│   ├── slam_rtabmap_b.launch.py       # RTAB-Map Config B
│   ├── navigation.launch.py           # Nav2 stack
│   └── evaluation.launch.py           # Ground truth comparison
├── src/
│   ├── evaluation_node.py       # Lokalizasyon karşılaştırma
│   ├── waypoint_navigator.py    # Random waypoint gönderici
│   └── map_metrics.py           # Point cloud density hesaplama
├── rviz/
│   └── project_config.rviz      # Proje RViz ayarları
├── maps/                        # Kaydedilen haritalar
│   ├── rtabmap_a/
│   └── rtabmap_b/
└── results/                     # Sonuçlar
    ├── plots/
    ├── metrics/
    └── videos/
```

---

### FAZA 2: Sensor Fusion (1 gün)

#### Adım 2.1: robot_localization EKF Konfigürasyonu

`project/config/robot_localization.yaml`:
```yaml
ekf_filter_node:
  ros__parameters:
    frequency: 50.0
    sensor_timeout: 0.1
    two_d_mode: false  # 3D mode for SLAM

    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom

    # Wheel odometry
    odom0: /odom
    odom0_config: [true,  true,  false,  # x, y, z
                   false, false, true,   # roll, pitch, yaw
                   true,  true,  false,  # vx, vy, vz
                   false, false, true,   # vroll, vpitch, vyaw
                   false, false, false]  # ax, ay, az
    odom0_differential: false
    odom0_relative: false

    # IMU
    imu0: /imu/data
    imu0_config: [false, false, false,  # x, y, z
                  true,  true,  true,   # roll, pitch, yaw
                  false, false, false,  # vx, vy, vz
                  true,  true,  true,   # vroll, vpitch, vyaw
                  true,  true,  true]   # ax, ay, az
    imu0_differential: false
    imu0_relative: false
    imu0_remove_gravitational_acceleration: true

    # Process noise (tune these)
    process_noise_covariance: [0.05, 0.0,  0.0,  ...]  # 15x15 matrix
```

#### Adım 2.2: Sensor Fusion Launch File

`project/launch/sensor_fusion.launch.py`:
```python
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('robot_hw1'),
        'config', 'robot_localization.yaml'
    )

    return LaunchDescription([
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[config],
            remappings=[
                ('odometry/filtered', '/odometry/filtered')
            ]
        )
    ])
```

---

### FAZA 3: RTAB-Map SLAM (2-3 gün)

#### Adım 3.1: RTAB-Map Config A (Visual Odometry)

`project/config/rtabmap_config_a.yaml`:
```yaml
# Config A: Feature-based Visual Odometry
rtabmap:
  ros__parameters:
    frame_id: base_link
    odom_frame_id: odom
    map_frame_id: map
    subscribe_depth: true
    subscribe_rgb: true
    subscribe_odom_info: true
    approx_sync: true
    queue_size: 10

    # Visual odometry parameters
    Odom/Strategy: "0"           # 0=Frame-to-Map, 1=Frame-to-Frame
    Odom/GuessMotion: "true"
    Vis/FeatureType: "6"         # 6=ORB features
    Vis/MaxFeatures: "1000"
    Vis/MinInliers: "15"

    # RTAB-Map parameters
    Rtabmap/DetectionRate: "1"
    Rtabmap/CreateIntermediateNodes: "false"
    RGBD/NeighborLinkRefining: "true"
    RGBD/ProximityBySpace: "true"
    RGBD/OptimizeFromGraphEnd: "false"
    Reg/Strategy: "0"            # 0=Visual
    Reg/Force3DoF: "false"       # 3D SLAM

    # Memory management
    Mem/IncrementalMemory: "true"
    Mem/STMSize: "30"
```

#### Adım 3.2: RTAB-Map Config B (ICP Odometry)

`project/config/rtabmap_config_b.yaml`:
```yaml
# Config B: ICP-based Odometry (Point Cloud Registration)
rtabmap:
  ros__parameters:
    frame_id: base_link
    odom_frame_id: odom
    map_frame_id: map
    subscribe_depth: true
    subscribe_rgb: true
    approx_sync: true

    # ICP odometry
    Odom/Strategy: "1"           # ICP
    OdomF2M/ScanSubtractRadius: "0.05"
    OdomF2M/ScanMaxSize: "10000"

    # ICP parameters
    Icp/PointToPlane: "true"
    Icp/VoxelSize: "0.05"
    Icp/MaxCorrespondenceDistance: "0.1"
    Icp/Iterations: "30"

    # Registration
    Reg/Strategy: "1"            # 1=ICP
    Reg/Force3DoF: "false"

    # Grid map (for 2D projection)
    Grid/FromDepth: "true"
    Grid/MaxGroundHeight: "0.1"
    Grid/MaxObstacleHeight: "2.0"
```

#### Adım 3.3: RTAB-Map Launch Files

`project/launch/slam_rtabmap_a.launch.py`:
```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        # RTAB-Map SLAM node (Config A - Visual)
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'subscribe_depth': True,
                'subscribe_rgb': True,
                'approx_sync': True,
                'Odom/Strategy': '0',
                'Vis/FeatureType': '6',
                'RGBD/NeighborLinkRefining': 'true',
                'Reg/Strategy': '0',
                'Reg/Force3DoF': 'false',
                'Grid/FromDepth': 'true',
            }],
            remappings=[
                ('rgb/image', '/camera/rgb/image_raw'),
                ('rgb/camera_info', '/camera/rgb/camera_info'),
                ('depth/image', '/camera/depth/image_raw'),
                ('odom', '/odometry/filtered'),  # From robot_localization
            ]
        ),

        # Visual Odometry node
        Node(
            package='rtabmap_odom',
            executable='rgbd_odometry',
            name='rgbd_odometry',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'publish_tf': False,  # Let robot_localization handle TF
                'Odom/Strategy': '0',
                'Vis/FeatureType': '6',
            }],
            remappings=[
                ('rgb/image', '/camera/rgb/image_raw'),
                ('rgb/camera_info', '/camera/rgb/camera_info'),
                ('depth/image', '/camera/depth/image_raw'),
            ]
        ),
    ])
```

---

### FAZA 4: Değerlendirme Sistemi (1-2 gün)

#### Adım 4.1: Ground Truth Karşılaştırma Node

`project/src/evaluation_node.py`:
```python
#!/usr/bin/env python3
"""
Lokalizasyon performans değerlendirme node'u.
Ground truth ile SLAM çıktısını karşılaştırır.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
import numpy as np
import csv
from datetime import datetime

class EvaluationNode(Node):
    def __init__(self):
        super().__init__('evaluation_node')

        # Subscribers
        self.gt_sub = self.create_subscription(
            Odometry, '/ground_truth/odom', self.gt_callback, 10)
        self.slam_sub = self.create_subscription(
            Odometry, '/rtabmap/odom', self.slam_callback, 10)
        self.filtered_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.filtered_callback, 10)

        # Data storage
        self.gt_poses = []
        self.slam_poses = []
        self.filtered_poses = []
        self.timestamps = []

        # Timer for periodic metrics calculation
        self.timer = self.create_timer(5.0, self.calculate_metrics)

        self.get_logger().info('Evaluation node started')

    def gt_callback(self, msg):
        pose = self.extract_pose(msg)
        self.gt_poses.append(pose)
        self.timestamps.append(msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9)

    def slam_callback(self, msg):
        pose = self.extract_pose(msg)
        self.slam_poses.append(pose)

    def filtered_callback(self, msg):
        pose = self.extract_pose(msg)
        self.filtered_poses.append(pose)

    def extract_pose(self, msg):
        return {
            'x': msg.pose.pose.position.x,
            'y': msg.pose.pose.position.y,
            'z': msg.pose.pose.position.z,
            'qx': msg.pose.pose.orientation.x,
            'qy': msg.pose.pose.orientation.y,
            'qz': msg.pose.pose.orientation.z,
            'qw': msg.pose.pose.orientation.w
        }

    def calculate_metrics(self):
        if len(self.gt_poses) < 10 or len(self.slam_poses) < 10:
            return

        # Calculate RMSE
        n = min(len(self.gt_poses), len(self.slam_poses))
        errors = []
        for i in range(n):
            gt = self.gt_poses[i]
            slam = self.slam_poses[i]
            error = np.sqrt(
                (gt['x'] - slam['x'])**2 +
                (gt['y'] - slam['y'])**2 +
                (gt['z'] - slam['z'])**2
            )
            errors.append(error)

        rmse = np.sqrt(np.mean(np.array(errors)**2))
        max_error = np.max(errors)
        mean_error = np.mean(errors)

        self.get_logger().info(f'RMSE: {rmse:.4f}m, Mean: {mean_error:.4f}m, Max: {max_error:.4f}m')

    def save_results(self, filename):
        """Save results to CSV for plotting"""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'gt_x', 'gt_y', 'gt_z', 'slam_x', 'slam_y', 'slam_z', 'error'])
            # Write data...

def main():
    rclpy.init()
    node = EvaluationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

#### Adım 4.2: Point Cloud Density Hesaplama

`project/src/map_metrics.py`:
```python
#!/usr/bin/env python3
"""
3D Map kalite metrikleri hesaplama.
- Point cloud density
- Coverage area
- Map completeness
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import numpy as np

class MapMetricsNode(Node):
    def __init__(self):
        super().__init__('map_metrics_node')

        self.sub_a = self.create_subscription(
            PointCloud2, '/rtabmap/cloud_map', self.map_a_callback, 10)

        self.map_a_points = None
        self.map_b_points = None

    def map_a_callback(self, msg):
        points = list(pc2.read_points(msg, field_names=['x', 'y', 'z']))
        self.map_a_points = np.array(points)

        if len(self.map_a_points) > 0:
            # Calculate metrics
            density = self.calculate_density(self.map_a_points)
            coverage = self.calculate_coverage(self.map_a_points)

            self.get_logger().info(
                f'Map A - Points: {len(self.map_a_points)}, '
                f'Density: {density:.2f} pts/m³, '
                f'Coverage: {coverage:.2f} m²'
            )

    def calculate_density(self, points, voxel_size=0.1):
        """Points per cubic meter"""
        if len(points) == 0:
            return 0.0

        # Bounding box volume
        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        volume = np.prod(max_coords - min_coords)

        return len(points) / volume if volume > 0 else 0.0

    def calculate_coverage(self, points):
        """2D footprint area"""
        if len(points) == 0:
            return 0.0

        min_xy = np.min(points[:, :2], axis=0)
        max_xy = np.max(points[:, :2], axis=0)

        return np.prod(max_xy - min_xy)

def main():
    rclpy.init()
    node = MapMetricsNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

### FAZA 5: Navigation (1-2 gün)

#### Adım 5.1: 2D Map Projection

RTAB-Map otomatik olarak `grid_map` publish edebilir, ya da manuel olarak:

```bash
# octomap_server kullanarak
ros2 run octomap_server octomap_server_node --ros-args \
    -p frame_id:=map \
    -p resolution:=0.05 \
    -r cloud_in:=/rtabmap/cloud_map
```

#### Adım 5.2: Nav2 Konfigürasyonu

`project/config/nav2_params.yaml`:
```yaml
bt_navigator:
  ros__parameters:
    use_sim_time: true
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odometry/filtered

controller_server:
  ros__parameters:
    use_sim_time: true
    controller_frequency: 10.0
    controller_plugins: ["FollowPath"]
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      min_vel_x: 0.0
      max_vel_x: 0.3
      max_vel_theta: 0.5

planner_server:
  ros__parameters:
    use_sim_time: true
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: true
```

#### Adım 5.3: Waypoint Navigator Node

`project/src/waypoint_navigator.py`:
```python
#!/usr/bin/env python3
"""
Random waypoint gönderici.
Haritada rastgele erişilebilir noktalara robot gönderir.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid
import random
import numpy as np

class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('waypoint_navigator')

        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, 10)

        self.map_data = None
        self.free_cells = []

        # Predefined waypoints (Office World'e özgü)
        self.waypoints = [
            {'x': 2.0, 'y': 0.0},    # Koridor başı
            {'x': 5.0, 'y': 0.0},    # Koridor ortası
            {'x': 8.0, 'y': 2.0},    # Oda 1
            {'x': 8.0, 'y': -2.0},   # Oda 2
            {'x': 3.0, 'y': 3.0},    # Açık alan
        ]
        self.current_waypoint = 0

    def map_callback(self, msg):
        self.map_data = msg
        self.extract_free_cells()

    def extract_free_cells(self):
        """Haritadan boş hücreleri çıkar"""
        if self.map_data is None:
            return

        width = self.map_data.info.width
        height = self.map_data.info.height
        resolution = self.map_data.info.resolution
        origin = self.map_data.info.origin

        self.free_cells = []
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if self.map_data.data[idx] == 0:  # Free
                    world_x = origin.position.x + x * resolution
                    world_y = origin.position.y + y * resolution
                    self.free_cells.append((world_x, world_y))

    def send_goal(self, x, y, yaw=0.0):
        """Nav2'ye hedef gönder"""
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0

        self.nav_client.wait_for_server()
        self.get_logger().info(f'Navigating to ({x:.2f}, {y:.2f})')

        future = self.nav_client.send_goal_async(goal_msg)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if goal_handle.accepted:
            self.get_logger().info('Goal accepted')
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Navigation completed')
        # Sonraki waypoint'e git
        self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
        wp = self.waypoints[self.current_waypoint]
        self.send_goal(wp['x'], wp['y'])

def main():
    rclpy.init()
    node = WaypointNavigator()
    # İlk waypoint'i gönder
    wp = node.waypoints[0]
    node.send_goal(wp['x'], wp['y'])
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 6. Test Senaryoları

### 6.1 Mapping Testi
```bash
# Terminal 1: Gazebo + Robot
ros2 launch robot_hw1 hw3.launch.py run_controller:=false

# Terminal 2: Sensor Fusion
ros2 launch robot_hw1 sensor_fusion.launch.py

# Terminal 3: RTAB-Map (Config A)
ros2 launch robot_hw1 slam_rtabmap_a.launch.py

# Terminal 4: Teleop (manuel hareket)
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Terminal 5: RViz
rviz2 -d project/rviz/project_config.rviz
```

### 6.2 Karşılaştırma Testi
```
1. Config A ile tam tur at, haritayı kaydet
2. Gazebo'yu resetle
3. Config B ile aynı rotayı takip et
4. Her iki haritayı karşılaştır
```

### 6.3 Navigation Testi
```bash
# Harita kaydedildikten sonra
ros2 launch robot_hw1 navigation.launch.py map:=maps/rtabmap_a.yaml

# Waypoint navigator başlat
ros2 run robot_hw1 waypoint_navigator
```

---

## 7. Karşılaştırma Metrikleri

### 7.1 Lokalizasyon Performansı
| Metrik | Açıklama | Formül |
|--------|----------|--------|
| RMSE | Root Mean Square Error | √(Σ(error²)/n) |
| ATE | Absolute Trajectory Error | Mean of position errors |
| RPE | Relative Pose Error | Error between consecutive poses |
| Max Error | Maximum position error | max(errors) |

### 7.2 Mapping Performansı
| Metrik | Açıklama |
|--------|----------|
| Point Density | Points per cubic meter |
| Coverage | 2D footprint area |
| Completeness | % of expected area mapped |
| Noise Level | Variance in flat surfaces |

### 7.3 Navigation Performansı
| Metrik | Açıklama |
|--------|----------|
| Success Rate | % of reached goals |
| Path Length | Total distance traveled |
| Time to Goal | Average navigation time |
| Replanning Count | Number of path recalculations |

---

## 8. Zaman Çizelgesi

```
┌────────────────────────────────────────────────────────────────┐
│ Gün 1-2: Altyapı                                               │
│ ├─ Paket kurulumu                                              │
│ ├─ URDF ground truth plugin                                    │
│ └─ Klasör yapısı oluşturma                                     │
├────────────────────────────────────────────────────────────────┤
│ Gün 3: Sensor Fusion                                           │
│ ├─ robot_localization config                                   │
│ ├─ Launch file                                                 │
│ └─ Test ve tuning                                              │
├────────────────────────────────────────────────────────────────┤
│ Gün 4-6: RTAB-Map SLAM                                         │
│ ├─ Config A (Visual Odometry)                                  │
│ ├─ Config B (ICP Odometry)                                     │
│ ├─ Mapping testleri                                            │
│ └─ Harita kaydetme                                             │
├────────────────────────────────────────────────────────────────┤
│ Gün 7-8: Değerlendirme                                         │
│ ├─ Ground truth karşılaştırma                                  │
│ ├─ Metrik hesaplama                                            │
│ └─ Grafik/tablo oluşturma                                      │
├────────────────────────────────────────────────────────────────┤
│ Gün 9-10: Navigation                                           │
│ ├─ 2D map projection                                           │
│ ├─ Nav2 kurulum                                                │
│ └─ Waypoint navigation test                                    │
├────────────────────────────────────────────────────────────────┤
│ Gün 11-12: Dokümantasyon                                       │
│ ├─ Video kayıt ve düzenleme                                    │
│ ├─ Rapor yazımı (IEEE format)                                  │
│ └─ Sunum hazırlama                                             │
├────────────────────────────────────────────────────────────────┤
│ 10 Ocak: SUNUM                                                 │
│ 11 Ocak: RAPOR TESLİM                                          │
└────────────────────────────────────────────────────────────────┘
```

---

## 9. Olası Sorunlar ve Çözümler

| Sorun | Olası Sebep | Çözüm |
|-------|-------------|-------|
| RTAB-Map loop closure çalışmıyor | Yetersiz feature | Vis/MaxFeatures artır |
| Drift fazla | IMU calibration | robot_localization covariance tune |
| Nav2 hedef bulamıyor | Costmap sorunu | inflation_radius ayarla |
| Point cloud seyrek | Kamera limitli | voxel_size küçült |
| TF timeout | Senkronizasyon | approx_sync: true |

---

## 10. Deliverables Checklist

### Rapor (6-10 sayfa, IEEE format)
- [ ] Abstract
- [ ] Introduction + Literature Survey
- [ ] Methodology (flow chart, block diagram)
- [ ] Results (tablolar, grafikler)
- [ ] Video/repo linkleri
- [ ] References

### Sunum (max 10 slide, 10 dakika)
- [ ] Problem tanımı
- [ ] Sistem mimarisi
- [ ] Demo videoları
- [ ] Sonuç karşılaştırma tabloları
- [ ] Q&A hazırlığı

### Video
- [ ] Gazebo + Office World görüntüsü
- [ ] RTAB-Map mapping process
- [ ] Ground truth vs SLAM karşılaştırma
- [ ] Nav2 autonomous navigation
- [ ] Metrik sonuçları

### Kod
- [x] GitHub repo linki
- [x] README.md (project/README.md)
- [x] Launch files (full_slam, slam_rgbd, slam_icp, project_bringup, sensor_fusion)
- [x] Config files (robot_localization.yaml, rtabmap_rgbd.yaml, rtabmap_icp.yaml)
- [x] Evaluation scripts (evaluation_node.py, map_metrics.py, waypoint_navigator.py)

---

## 11. Hızlı Başlangıç Komutları

```bash
# 1. Paketleri kur (zaten kurulu olmalı)
sudo apt install -y ros-humble-robot-localization ros-humble-rtabmap-ros \
    ros-humble-nav2-bringup ros-humble-octomap-server

# 2. Workspace build
cd ~/Documents/GitHub/hws_repo
colcon build --symlink-install
source install/setup.bash

# 3. Tam SLAM sistemi (Gazebo + EKF + RTAB-Map + RViz)
ros2 launch robot_project full_slam.launch.py

# 4. ICP modunda SLAM (karşılaştırma için)
ros2 launch robot_project full_slam.launch.py slam_mode:=icp

# 5. Sadece base simulation (EKF, SLAM'sız)
ros2 launch robot_project project_bringup.launch.py

# 6. Manuel hareket için teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 7. Ayrı terminalde SLAM başlat
ros2 launch robot_project slam_rgbd.launch.py  # Visual SLAM
ros2 launch robot_project slam_icp.launch.py   # ICP SLAM
```

---

**Not:** Bu plan, hocadan "or similar" için onay alındığı varsayımıyla hazırlanmıştır. RTAB-Map yerine farklı bir paket istenirse plan güncellenecektir.
