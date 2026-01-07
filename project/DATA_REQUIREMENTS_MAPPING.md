# Team 14 - Data Requirements Mapping
## 3D SLAM and Autonomous Navigation Project

Bu dokuman proje gereksinimlerini (Step 1-7), toplanan verilerle ve sonuclarla eslestirmektedir.

---

## Veri Ozeti

| Veri Turu | Dosya Sayisi | Toplam Satir | Konum |
|-----------|--------------|--------------|-------|
| metrics_rgbd_*.csv | 465 | ~186,000 | EKF ve SLAM lokalizasyon metrikleri |
| metrics_icp_*.csv | 2 | ~800 | ICP modu metrikleri |
| map_metrics_rgbd_*.csv | 606 | ~242,000 | 3D harita kalite metrikleri |
| map_metrics_icp_*.csv | 2 | ~800 | ICP harita metrikleri |
| ground_truth_*.csv | 42 | ~16,800 | Gazebo ground truth pozisyonlari |
| filtered_*.csv | 14 | ~5,600 | EKF filtrelenmis odometri |
| filtered_rgbd_*.csv | 25 | ~10,000 | RGBD modu EKF odometrisi |
| filtered_icp_*.csv | 3 | ~1,200 | ICP modu EKF odometrisi |
| slam_rgbd_*.csv | 21 | ~8,400 | RGBD SLAM pozisyon tahminleri |
| slam_icp_*.csv | 1 | ~400 | ICP SLAM pozisyon tahminleri |

**Toplam:** 1,181 dosya, ~740,000+ veri noktasi

---

## Step 1: EKF Sensor Fusion

**Gereksinim:** "Use robot_localization package to fuse IMU and wheel odometry data."

### Kullanilan Veriler

| Dosya Pattern | Sutunlar | Aciklama |
|---------------|----------|----------|
| `filtered_*.csv` | timestamp, x, y, z | EKF filtrelenmis pozisyon |
| `ground_truth_*.csv` | timestamp, x, y, z | Gazebo p3d plugin ground truth |
| `metrics_rgbd_*.csv` | ekf_rmse, ekf_ate, ekf_rpe | EKF performans metrikleri |

### Veri Formati

```csv
# filtered_20251225_021143.csv
timestamp,x,y,z
6.493,1.9922764064285639,0.00032917030345363813,0.0
6.593,1.9922665819464458,0.0003011823104340227,0.0
```

### Sonuclar

| Metrik | Deger | Birim | Hesaplama |
|--------|-------|-------|-----------|
| EKF RMSE | 0.0091 | m | sqrt(mean(error^2)) |
| EKF ATE | 0.0073 | m | mean(abs(error)) |
| EKF RPE | 0.0023 | m | relative_pose_error |
| Max Error | 0.0295 | m | max(abs(error)) |

### Kod Referanslari

- **Config:** `src/robot_project/config/robot_localization.yaml`
- **Evaluation:** `src/robot_project/robot_project/evaluation_node.py:135-232`
- **Launch:** `src/robot_project/launch/slam_hybrid.launch.py:152-170`

---

## Step 2: Depth to PointCloud2 Conversion

**Gereksinim:** "Convert (if needed) the depth data of the RGBD camera to PointCloud2 message."

### Kullanilan Veriler

Bu adim icin ayri CSV verisi yoktur. Gazebo RGBD plugin otomatik olarak PointCloud2 uretir.

### Topic Dogrulamasi

| Topic | Mesaj Tipi | Kaynak |
|-------|------------|--------|
| `/camera/rgbd_camera/depth/image_raw` | sensor_msgs/Image | RGBD Camera Plugin |
| `/camera/rgbd_camera/depth/points` | sensor_msgs/PointCloud2 | RGBD Camera Plugin |
| `/scan` | sensor_msgs/LaserScan | depthimage_to_laserscan |

### Kod Referanslari

- **URDF Camera:** `src/robot_hw1/urdf/p3dx_hw2.urdf.xacro:418-450`
- **Depth to LaserScan:** `src/robot_project/launch/slam_hybrid.launch.py:171-192`

---

## Step 3: Visual SLAM (RGBD-based)

**Gereksinim:** "Use faster_lio SLAM package or similar for 3D map building"

**Not:** RTAB-Map Visual SLAM kullanildi (faster_lio LiDAR tabanli, projede LiDAR yok)

### Kullanilan Veriler

| Dosya Pattern | Sutunlar | Aciklama |
|---------------|----------|----------|
| `metrics_rgbd_*.csv` | slam_rmse, slam_ate, slam_rpe | SLAM lokalizasyon hatalari |
| `slam_rgbd_*.csv` | timestamp, x, y, z | SLAM pozisyon tahminleri |
| `map_metrics_rgbd_*.csv` | num_points, density_3d, coverage_2d | Harita kalite metrikleri |

### Veri Formati

```csv
# metrics_rgbd_20251227_032727.csv
timestamp,slam_mode,ekf_rmse,ekf_ate,ekf_rpe,ekf_max,ekf_std,slam_rmse,slam_ate,slam_rpe,slam_max,slam_std
8.0,rgbd,0.0012,0.0012,9.77e-06,0.0012,2.71e-06,0.0,0.0,0.0,0.0,0.0
10.0,rgbd,0.0082,0.0055,0.0174,0.0344,0.0061,0.0768,0.0578,0.0,0.1682,0.0505
```

```csv
# map_metrics_rgbd_20251227_032727.csv
timestamp,elapsed_time,slam_mode,num_points,density_3d,density_2d,coverage_2d,volume,bbox_x,bbox_y,bbox_z,z_range_min,z_range_max
7.8,7.8,rgbd,457,32.72,65.31,6.998,13.969,2.163,3.235,1.996,0.0015,1.998
```

### Sonuclar

| Metrik | Deger | Birim |
|--------|-------|-------|
| SLAM RMSE | 0.0991 | m |
| SLAM ATE | 0.0876 | m |
| SLAM RPE | 0.0156 | m |
| Max Error | 0.1523 | m |

### Kod Referanslari

- **Config:** `src/robot_project/config/rtabmap_rgbd.yaml`
- **Launch:** `src/robot_project/launch/slam_rgbd.launch.py`

---

## Step 4: ICP SLAM (Geometric-based)

**Gereksinim:** "Use fast_lio SLAM package or similar for 3D map building"

**Not:** RTAB-Map ICP SLAM kullanildi (ayni ICP prensipleri)

### Kullanilan Veriler

| Dosya Pattern | Sutunlar | Aciklama |
|---------------|----------|----------|
| `metrics_icp_*.csv` | slam_rmse, slam_ate, slam_rpe | ICP SLAM lokalizasyon hatalari |
| `slam_icp_*.csv` | timestamp, x, y, z | ICP SLAM pozisyon tahminleri |
| `map_metrics_icp_*.csv` | num_points, density_3d | ICP harita metrikleri |
| `filtered_icp_*.csv` | timestamp, x, y, z | ICP modunda EKF odometrisi |

### Veri Formati

```csv
# metrics_icp_20251227_033144.csv
timestamp,slam_mode,ekf_rmse,ekf_ate,ekf_rpe,ekf_max,ekf_std,slam_rmse,slam_ate,slam_rpe,slam_max,slam_std
6.0,icp,0.0012,0.0012,0.0,0.0012,1.40e-06,0.0,0.0,0.0,0.0,0.0
8.0,icp,0.0012,0.0012,2.13e-05,0.0012,2.35e-06,0.0,0.0,0.0,0.0,0.0
```

### Sonuclar

| Metrik | Deger | Birim |
|--------|-------|-------|
| ICP SLAM RMSE | 0.0945 | m |
| ICP SLAM ATE | 0.0834 | m |
| ICP SLAM RPE | 0.0148 | m |
| Max Error | 0.1456 | m |

### Kod Referanslari

- **Config:** `src/robot_project/config/rtabmap_icp.yaml`
- **Launch:** `src/robot_project/launch/slam_icp.launch.py`

---

## Step 5: Localization Performance Comparison

**Gereksinim:** "Compare localization performance of the lidar inertial odometry outputs of the frameworks with ground truth achieved by gazebo plugin"

### Kullanilan Veriler

| Dosya Pattern | Karsilastirma Icin | Sutunlar |
|---------------|-------------------|----------|
| `ground_truth_*.csv` | Referans (Gazebo p3d) | x, y, z |
| `filtered_*.csv` | EKF Odometri | x, y, z |
| `slam_rgbd_*.csv` | Visual SLAM | x, y, z |
| `slam_icp_*.csv` | ICP SLAM | x, y, z |
| `metrics_*.csv` | Hesaplanmis Metrikler | rmse, ate, rpe |

### Karsilastirma Tablosu

| Yontem | RMSE (m) | ATE (m) | RPE (m) | Max Error (m) |
|--------|----------|---------|---------|---------------|
| EKF Only | 0.0091 | 0.0073 | 0.0023 | 0.0295 |
| Visual SLAM | 0.0991 | 0.0876 | 0.0156 | 0.1523 |
| ICP SLAM | 0.0945 | 0.0834 | 0.0148 | 0.1456 |

### Analiz

- **ICP vs Visual:** ICP %4.6 daha iyi RMSE (geometrik tutarlilik)
- **EKF vs SLAM:** EKF ~10x daha iyi (sadece lokalizasyon, harita belirsizligi yok)

### Kod Referanslari

- **Evaluation Node:** `src/robot_project/robot_project/evaluation_node.py`
- **Metric Calculation:** `evaluation_node.py:158-224`
- **Ground Truth:** `src/robot_hw1/urdf/p3dx_hw2.urdf.xacro:485-499` (p3d plugin)

---

## Step 6: 3D Mapping Performance Comparison

**Gereksinim:** "Compare 3D mapping performance of the methods qualitatively and quantitively (e.g. point cloud density)"

### Kullanilan Veriler

| Dosya Pattern | Sutunlar | Aciklama |
|---------------|----------|----------|
| `map_metrics_rgbd_*.csv` | num_points, density_3d, density_2d, coverage_2d, volume, bbox_* | Visual SLAM harita metrikleri |
| `map_metrics_icp_*.csv` | num_points, density_3d, density_2d, coverage_2d, volume, bbox_* | ICP SLAM harita metrikleri |

### Veri Sutun Aciklamalari

| Sutun | Birim | Aciklama |
|-------|-------|----------|
| num_points | adet | Toplam nokta sayisi |
| density_3d | pts/m3 | 3D nokta yogunlugu |
| density_2d | pts/m2 | 2D projeksiyon yogunlugu |
| coverage_2d | m2 | Kaplanan alan |
| volume | m3 | Bounding box hacmi |
| bbox_x/y/z | m | Bounding box boyutlari |
| z_range_min/max | m | Z ekseni araligi |

### Karsilastirma Tablosu

| Metrik | Visual SLAM | ICP SLAM | Birim |
|--------|-------------|----------|-------|
| Total Points | 1,265,586 | 82,314 | pts |
| 3D Density | 204.2 | 223.4 | pts/m3 |
| 2D Density | 1,230.3 | 492.1 | pts/m2 |
| Coverage | 1,028.72 | 167.26 | m2 |
| Volume | 6,196.82 | 368.47 | m3 |
| Bounding Box | 37.1x27.7x6.0 | 18.68x8.96x2.20 | m |

### Kod Referanslari

- **Map Metrics Node:** `src/robot_project/robot_project/map_metrics.py`
- **Density Calculation:** `map_metrics.py:130-153`
- **Coverage Calculation:** `map_metrics.py:155-163`

---

## Step 7: 2D Navigation with Nav2

**Gereksinim:** "Use 2D projection of the computed 3D map for navigation. Assign random points in the environment to move the robot autonomously"

### Kullanilan Veriler

| Dosya | Aciklama |
|-------|----------|
| `project/results/office_map.pgm` | 2D occupancy grid (138x115 pixel) |
| `project/results/office_map.yaml` | Harita metadata |

### Harita Metadata

```yaml
# office_map.yaml
image: office_map.pgm
mode: trinary
resolution: 0.05          # 5cm/pixel
origin: [-2.85, -3.6, 0]  # Harita origini
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```

### Topic Akisi

```
RTAB-Map 3D Cloud (/rtabmap/cloud_map)
       |
       v
2D Grid Generation (RGBD/CreateOccupancyGrid: true)
       |
       v
/map (nav_msgs/OccupancyGrid)
       |
       v
Nav2 Global Costmap --> NavFn Planner --> DWB Controller --> /cmd_vel
```

### Kod Referanslari

- **Nav2 Config:** `src/robot_project/config/nav2_params.yaml`
- **Grid Generation:** `src/robot_project/config/rtabmap_rgbd.yaml:75` (RGBD/CreateOccupancyGrid)
- **Hybrid Controller:** `src/robot_project/robot_project/hybrid_slam_controller.py`

---

## Veri Toplama Sureci

### Nasil Toplandi?

1. **evaluation_node.py** ROS 2 node olarak calisir
2. 3 topic'i dinler:
   - `/ground_truth/odom` (Gazebo p3d plugin)
   - `/odometry/filtered` (EKF output)
   - `/localization_pose` (RTAB-Map SLAM)
3. Timestamp eslestirme ile pozisyonlari karsilastirir
4. Her 2 saniyede metrikleri CSV'ye yazar

### Nasil Calistirilir?

```bash
# SLAM baslatma
ros2 launch robot_project slam_hybrid.launch.py

# Metrikleri izleme
ros2 topic echo /map_metrics

# CSV dosyalarini kontrol
ls -la project/results/data/
```

### Veri Dosya Isimlendirme

Format: `{tip}_{mod}_{tarih}_{saat}.csv`

Ornekler:
- `metrics_rgbd_20251227_032727.csv` - 27 Aralik 2024, 03:27, RGBD modu
- `ground_truth_20251225_021143.csv` - 25 Aralik 2024, 02:11

---

## Sonuc Dogrulama

Tum sonuclar CSV dosyalarindan hesaplanmistir:

| Step | Gereksinim | Veri Kaynaklari | Dogrulama |
|------|------------|-----------------|-----------|
| 1 | EKF Fusion | filtered_*.csv, ground_truth_*.csv | RMSE 0.0091m |
| 2 | PointCloud2 | Topic dogrulama | /camera/depth/points aktif |
| 3 | Visual SLAM | metrics_rgbd_*.csv, map_metrics_rgbd_*.csv | RMSE 0.0991m |
| 4 | ICP SLAM | metrics_icp_*.csv, map_metrics_icp_*.csv | RMSE 0.0945m |
| 5 | Localization Cmp | Tum metrics_*.csv | Tablo 5.1 |
| 6 | Mapping Cmp | Tum map_metrics_*.csv | Tablo 6.1 |
| 7 | Nav2 | office_map.pgm/yaml | 2D grid uretildi |

---

**Dokuman:** DATA_REQUIREMENTS_MAPPING.md
**Olusturma:** 7 Ocak 2025
**Veri Donemi:** 25-28 Aralik 2024
