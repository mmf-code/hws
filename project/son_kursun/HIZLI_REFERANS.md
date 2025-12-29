# HIZLI REFERANS KARTI

**Son Güncelleme:** 2024-12-29

## En Sık Kullanılan Komutlar

```bash
# 1. Build
cd /home/mmf/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select robot_project robot_hw1
source install/setup.bash

# 2. Fresh SLAM (PyGame kontrollü) - ÖNERİLEN
ros2 launch robot_project slam_hybrid.launch.py

# 3. Full Navigation (mevcut map ile)
ros2 launch robot_project full_navigation.launch.py

# 4. Requirement 7 Complete
ros2 launch robot_project requirement7_complete.launch.py
```

---

## PyGame Kontrolleri

```
┌────────────────────────────────────┐
│  WASD   = Hareket                  │
│  1-5    = Hız (0.2x → 2.0x)        │
│  Q/E    = 90° Sol/Sağ              │
│  R      = 180° U-Turn              │
│  SPACE  = AUTO ↔ MANUAL            │
│  T      = TURBO toggle             │
│  P      = Pause                    │
│  ESC    = Emergency Stop           │
└────────────────────────────────────┘
```

---

## Hızlı Problemler

| Problem | Çözüm |
|---------|-------|
| Keyboard çalışmıyor | PyGame penceresine tıkla |
| Robot çok yavaş | **5** tuşu veya **T** (turbo) |
| Robot sıkıştı | **SPACE** → MANUAL → **S** → geri git |
| Ters döndü | **R** tuşu (180° dönüş) |
| Map oluşmuyor | `ros2 topic list \| grep map` kontrol |
| Robot düşüyor | Ground plane eklendi, rebuild gerekli |
| RViz zoom yok | `hybrid_slam.rviz` kullanılmalı |

---

## Dosya Konumları

```
Controller:     src/robot_project/robot_project/hybrid_slam_controller.py
Launch:         src/robot_project/launch/slam_hybrid.launch.py
RViz Config:    src/robot_project/rviz/hybrid_slam.rviz
World File:     src/robot_hw1/worlds/empty_office.world
Database:       ~/.ros/rtabmap.db
Sonuçlar:       project/results/data/
Dökümanlar:     project/son_kursun/
```

---

## Debug Komutları

```bash
# Node'lar çalışıyor mu?
ros2 node list

# Map publish ediliyor mu?
ros2 topic hz /map

# TF tree
ros2 run tf2_tools view_frames

# Camera aktif mi?
ros2 topic hz /camera/rgbd_camera/depth/image_raw

# Mevcut topics
ros2 topic list | grep -E "map|cmd_vel|odom"
```

---

## Launch Parametreleri

```bash
# MANUAL mode başlat
ros2 launch robot_project slam_hybrid.launch.py start_mode:=manual

# Hızlı base speed
ros2 launch robot_project slam_hybrid.launch.py base_speed:=1.2

# RViz kapalı
ros2 launch robot_project slam_hybrid.launch.py use_rviz:=false

# Farklı spawn
ros2 launch robot_project slam_hybrid.launch.py robot_x:=3.0 robot_y:=1.0
```
