# PROJE WORKFLOW - Tüm Adımlar

**Son Güncelleme:** 2024-12-29

## Proje Gereksinimleri Özeti

```
1. ✅ EKF Sensor Fusion (IMU + wheel odometry)
2. ✅ Depth → PointCloud2 conversion
3. ⚠️ SLAM (RTAB-Map kullanıyoruz - Faster-LIO/FAST_LIO değil)
4. ⚠️ Comparison metrics (skip)
5. ⚠️ Localization vs GT (evaluation_node yapıyor)
6. ⚠️ 3D Map Quality (map_metrics yapıyor)
7. ✅ 2D Projection + Nav2 + Autonomous Navigation
```

---

## Ana Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                       PROJE AKIŞI                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1: SLAM MAPPING (ÖNERİLEN)                               │
│  ─────────────────────────────────                              │
│  ros2 launch robot_project slam_hybrid.launch.py                │
│                                                                 │
│  • PyGame ile AUTO/MANUAL/TURBO kontrol                         │
│  • RTAB-Map 3D map oluşturur                                    │
│  • 2D occupancy grid publish eder                               │
│  • Keyboard ile müdahale mümkün                                 │
│                                                                 │
│  Çıktı: ~/.ros/rtabmap.db (3D database)                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 2: NAV2 NAVIGATION                                       │
│  ─────────────────────────                                      │
│  (Mapping bittikten sonra veya paralel)                         │
│                                                                 │
│  • Nav2 stack başlar                                            │
│  • Costmap 2D grid'den oluşur                                   │
│  • Global + local planner aktif                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 3: AUTONOMOUS WAYPOINT NAVIGATION                        │
│  ────────────────────────────────────────                       │
│  ros2 launch robot_project requirement7_complete.launch.py      │
│                                                                 │
│  • Random waypoint generator                                    │
│  • Nav2 ile otonom navigasyon                                   │
│  • Coverage-based exploration                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Launch Files Özet

| Launch File | Açıklama | Database | Kontrol |
|-------------|----------|----------|---------|
| `slam_hybrid.launch.py` | Fresh SLAM + PyGame | Siler | Manual/Auto |
| `full_slam.launch.py` | Fresh SLAM (auto) | Siler | Auto only |
| `full_navigation.launch.py` | Existing map + Nav2 | Mevcut | - |
| `requirement7_complete.launch.py` | Full system | Mevcut | Random Nav |

---

## Timing (slam_hybrid.launch.py)

```
T=0s    Gazebo başlatılır
T=2s    Office geometry spawn
T=4s    Robot spawn (x=2.0, y=0.0, z=0.1)
T=6s    EKF sensor fusion başlar
T=7s    Depth → LaserScan converter
T=9s    RTAB-Map SLAM başlar
T=12s   Hybrid Controller başlar (PyGame)
T=15s   Map Metrics başlar
T=16s   RViz açılır (hybrid_slam.rviz)
```

---

## Düzeltilen Sorunlar

### 1. Robot Düşme Sorunu
**Sorun:** World file'da ground plane yoktu
**Çözüm:** `empty_office.world`'e ground_plane modeli eklendi

### 2. RViz Zoom/Pan Çalışmıyor
**Sorun:** slam_config.rviz eksik tools
**Çözüm:** `hybrid_slam.rviz` oluşturuldu - TopDownOrtho view + proper tools

### 3. Office Görsel Sorunu
**Sorun:** Mesh single-sided (backface culling)
**Not:** Bu Collada dosyasının özelliği, düzeltilmedi

---

## RViz Görüntülenecekler

1. **Robot Model** - TF: base_link
2. **/map** - 2D Occupancy Grid
3. **/rtabmap/cloud_map** - 3D Point Cloud
4. **/camera/rgbd_camera/image_raw** - RGB Camera
5. **/scan** - LaserScan (depth'den)
6. **Odometry** - Hareket izi

---

## Monitoring Komutları

```bash
# Topic listesi
ros2 topic list

# Node listesi
ros2 node list

# Map publish rate
ros2 topic hz /map

# RTAB-Map durumu
ros2 node info /rtabmap

# TF tree
ros2 run tf2_tools view_frames
```

---

## Database Yönetimi

```bash
# Mevcut database boyutu
ls -lh ~/.ros/rtabmap.db

# Database silme (fresh start için)
rm ~/.ros/rtabmap.db

# Database yedekleme
cp ~/.ros/rtabmap.db ~/maps/backup_$(date +%Y%m%d_%H%M%S).db
```

---

## Sonuçlar Nerede?

```
~/.ros/rtabmap.db              # 3D SLAM database

project/results/data/
├── map_metrics_*.csv          # 3D map quality
├── metrics_*.csv              # Position accuracy
├── ground_truth_*.csv         # GT trajectory
├── filtered_*.csv             # EKF odometry
└── slam_*.csv                 # SLAM odometry
```

---

## Değişiklik Geçmişi

### 2024-12-29
- `slam_hybrid.launch.py` eklendi (PyGame kontrol)
- `hybrid_slam.rviz` eklendi (TopDownOrtho + tools)
- `empty_office.world` güncellendi (ground plane)
- `hybrid_slam_controller.py` eklendi
