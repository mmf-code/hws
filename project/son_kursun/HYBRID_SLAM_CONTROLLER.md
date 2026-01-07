# HYBRID SLAM CONTROLLER - Detaylı Kullanım Kılavuzu

**Son Güncelleme:** 2024-12-29

## Genel Bakış

Bu sistem, SLAM mapping sırasında **otomatik** ve **manuel** kontrol arasında geçiş yapmanızı sağlar. PyGame penceresi ile görsel feedback ve keyboard kontrolü sunar.

---

## Hızlı Başlangıç

```bash
# Terminal'de çalıştır
cd /home/mmf/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash

# Fresh SLAM başlat
ros2 launch robot_project slam_hybrid.launch.py
```

**Not:** PyGame penceresi açılınca, o pencereye tıklayarak focus yapın!

---

## Dosya Yapısı

```
src/robot_project/
├── robot_project/
│   └── hybrid_slam_controller.py   # Ana controller node
├── launch/
│   └── slam_hybrid.launch.py       # All-in-one launch file
├── rviz/
│   └── hybrid_slam.rviz            # Özel RViz config (TopDownOrtho)

src/robot_hw1/
└── worlds/
    └── empty_office.world          # Ground plane eklendi

project/son_kursun/                  # Bu klasör
├── HYBRID_SLAM_CONTROLLER.md
├── PROJE_WORKFLOW.md
└── HIZLI_REFERANS.md
```

---

## Kontroller

### Hareket (WASD)

| Tuş | Aksiyon |
|-----|---------|
| **W** | İleri git |
| **S** | Geri git (yarı hızda) |
| **A** | Sola dön |
| **D** | Sağa dön |

### Hız Seviyeleri (1-5)

| Tuş | Çarpan | Linear (m/s) | Angular (rad/s) |
|-----|--------|--------------|-----------------|
| **1** | 0.2x | 0.18 | 0.36 |
| **2** | 0.5x | 0.45 | 0.90 |
| **3** | 1.0x | 0.90 | 1.80 |
| **4** | 1.5x | 1.35 | 2.70 |
| **5** | 2.0x | 1.80 | 3.60 |

### Özel Dönüşler

| Tuş | Aksiyon |
|-----|---------|
| **Q** | 90° sola dön |
| **E** | 90° sağa dön |
| **R** | 180° geri dön (U-turn) |

### Mod Değiştirme

| Tuş | Aksiyon |
|-----|---------|
| **SPACE** | AUTO ↔ MANUAL geçiş |
| **T** | TURBO mode toggle |
| **P** | Pause / Resume |
| **ESC** | Emergency Stop (toggle) |

---

## Modlar

### AUTO Mode (Varsayılan)
- Depth kamerası ile otomatik engel algılama
- 5 bölgeli derinlik taraması
- Otomatik duvar takibi + sıkışma kurtarma

**Kullanım:** Normal SLAM mapping

### MANUAL Mode
- Tam WASD kontrolü
- **Engel algılama YOK** - dikkatli olun!

**Kullanım:** Robot ters döndü, dar alan, spesifik hedef

### TURBO Mode
- AUTO mode + 2x hız çarpanı
- Engel algılama aktif

**Kullanım:** Geniş açık alanlar

---

## Launch Parametreleri

```bash
# Varsayılan
ros2 launch robot_project slam_hybrid.launch.py

# MANUAL mode
ros2 launch robot_project slam_hybrid.launch.py start_mode:=manual

# Hızlı
ros2 launch robot_project slam_hybrid.launch.py base_speed:=1.2

# RViz kapalı
ros2 launch robot_project slam_hybrid.launch.py use_rviz:=false

# Farklı spawn
ros2 launch robot_project slam_hybrid.launch.py robot_x:=3.0 robot_y:=1.0
```

---

## RViz Görünümü

**Config:** `hybrid_slam.rviz` - TopDownOrtho (2D harita)

| Kontrol | Aksiyon |
|---------|---------|
| Scroll | Zoom in/out |
| Sağ tık + drag | Pan |
| Views panel | TopDown ↔ 3D View |

### Görüntülenenler
- Grid, Robot Model, 2D Map, 3D Point Cloud
- Odometry trail, LaserScan, Camera image

---

## Tipik Senaryolar

### Robot Sıkıştı / Ters Döndü
1. **SPACE** → MANUAL
2. **S** → Geri git
3. **A/D** → Dön
4. **SPACE** → AUTO

### Hızlı Tarama
1. **T** → TURBO
2. Geniş alanda hızlı hareket
3. Dar alanda **T** → AUTO

### 180° Dönüş
1. **R** tuşu
2. Robot otomatik döner

---

## Troubleshooting

| Problem | Çözüm |
|---------|-------|
| PyGame yok | `pip install pygame` |
| Keyboard çalışmıyor | PyGame penceresine tıkla |
| Robot yavaş | **5** veya **T** tuşu |
| Robot düşüyor | World file ground plane kontrol |
| RViz zoom yok | hybrid_slam.rviz kullan |
| Map yok | `ros2 topic list \| grep map` |

---

## Değişiklik Geçmişi

### 2024-12-29
- **Eklendi:** `hybrid_slam_controller.py` (PyGame GUI)
- **Eklendi:** `slam_hybrid.launch.py`
- **Eklendi:** `hybrid_slam.rviz` (TopDownOrtho, proper tools)
- **Düzeltildi:** `empty_office.world` - ground plane eklendi
- **Düzeltildi:** Robot spawn (z=0.1)
