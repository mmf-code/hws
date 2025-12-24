# HW3: World Integration and Robot Operation

## Proje Özeti

Bu ödevde Pioneer 3-DX robotunu Clearpath Office World ortamında çalıştırdık. Robot, RGBD kamera kullanarak koridorlarda otonom olarak hareket ediyor ve engellere çarpmadan ilerliyor.

## Sistem Mimarisi

### Kullanılan Teknolojiler
- **ROS 2 Humble** - Robot işletim sistemi
- **Gazebo Classic** - Fizik simülasyonu
- **RViz2** - Görselleştirme
- **PlotJuggler/rqt_plot** - Sensör verisi grafikleri

### Paket Yapısı
```
src/robot_hw1/
├── launch/hw3.launch.py       # Ana launch dosyası
├── robot_hw1/
│   └── corridor_navigator.py  # Hareket kontrol node'u
├── urdf/p3dx_hw2.urdf.xacro   # Robot modeli + sensörler
├── rviz/hw3_config.rviz       # RViz ayarları
└── worlds/empty_office.world  # Boş world (ground plane yok)

hw3/src/cpr_office_gazebo/     # Office world paketi (ROS 2'ye port edildi)
├── CMakeLists.txt
├── package.xml
├── urdf/office_geometry.urdf.xacro
└── meshes/
    ├── office.dae             # Ana mesh dosyası
    └── *.jpg                  # Texture dosyaları
```

## Launch Dosyası Açıklaması

`hw3.launch.py` tek komutla tüm sistemi başlatıyor:

```bash
ros2 launch robot_hw1 hw3.launch.py
```

### Başlatılan Node'lar (sırasıyla):
1. **Gazebo** - empty_office.world ile (ground plane yok, z-fighting önlendi)
2. **robot_state_publisher** - TF tree yayını
3. **spawn_office** - Office mesh'i Gazebo'ya spawn
4. **spawn_robot** - Pioneer 3-DX robotu pozisyon (2.0, 0.0, 0.1)'de spawn
5. **RViz2** - Konfigüre edilmiş görselleştirme
6. **corridor_navigator** - 8sn gecikmeyle başlar (sensörler hazır olsun diye)
7. **PlotJuggler** - 10sn gecikmeyle başlar

### Launch Parametreleri
| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| use_sim_time | true | Simülasyon zamanı |
| use_rviz | true | RViz aç/kapa |
| run_controller | true | Hareket node'u aç/kapa |
| robot_x/y/z | 2.0/0.0/0.1 | Robot başlangıç pozisyonu |

## Robot Sensörleri

### RGBD Kamera
- **Konum:** Robotun önünde (0.15, 0, 0.30)
- **FOV:** 90 derece (1.5708 radyan)
- **Çözünürlük:** 640x480 @ 30Hz
- **Derinlik aralığı:** 0.1m - 4.0m
- **Topic'ler:**
  - `/camera/rgbd_camera/image_raw` - RGB görüntü
  - `/camera/rgbd_camera/depth/image_raw` - Derinlik görüntüsü
  - `/camera/rgbd_camera/points` - Point cloud

### IMU Sensörü
- **Konum:** Robot merkezinde (0, 0, 0.20)
- **Güncelleme hızı:** 100Hz
- **Gürültü:** angular_velocity_stdev=0.001745, linear_acceleration_stdev=0.01
- **Topic:** `/imu/data`

## Corridor Navigator - Hareket Algoritması

### Çalışma Prensibi
Robot, derinlik kamerasından gelen görüntüyü 5 bölgeye ayırıyor:

```
+--------+------+--------+------+--------+
|  FAR   | LEFT | CENTER | RIGHT|  FAR   |
|  LEFT  |      |        |      | RIGHT  |
+--------+------+--------+------+--------+
  0-15%  15-35%  35-65%  65-85%  85-100%
```

Her bölgedeki minimum mesafe hesaplanıyor ve buna göre karar veriliyor.

### Hareket Modları

#### 1. Normal İlerleme
- Tüm yönler açık → Düz git (0.3 m/s)

#### 2. Engel Tespit
- Merkez < 0.8m → Yavaşla, boş tarafa dön
- Sol veya sağda duvar → Hafif düzeltme yap

#### 3. Kritik Durum
- Merkez < 0.4m → Dur, agresif dönüş yap

#### 4. Köşe Algılama
- center < critical_distance VE left < min_distance VE right < min_distance → Köşe
- Far-left ve far-right'a bakarak dönüş yönü seç
- Hafif geri git (-0.05 m/s) + keskin dönüş (angular_speed * 1.2)

#### 5. Takılma Kurtarma
- 1.5 saniye aynı mesafede kalırsa → Takıldı (stuck_counter > 15, 10Hz'de)
- Geri git (-0.1 m/s) + agresif dönüş (angular_speed * 1.5)
- 3 saniye sonra yön değiştir (stuck_counter > 30)

### Parametreler
```python
linear_speed = 0.3      # İleri hız (m/s)
angular_speed = 0.5     # Dönüş hızı (rad/s)
min_distance = 0.8      # Yavaşlama mesafesi (m)
critical_distance = 0.4 # Durma mesafesi (m)
```

## Office World Entegrasyonu

### Yapılan Düzenlemeler

1. **World dosyası oluşturuldu** (`empty_office.world`)
   - Ground plane kaldırıldı (office kendi zeminini içeriyor)
   - Gölgeler kapatıldı (z-fighting önlendi)
   - Işık ayarları optimize edildi

2. **Office mesh spawn yöntemi**
   - URDF xacro dosyası bash pipe ile işleniyor
   - `spawn_entity.py` ile Gazebo'ya ekleniyor
   - Static olarak işaretli (hareket etmiyor)

3. **Robot spawn pozisyonu**
   - Koridorda açık alan: (2.0, 0.0, 0.1)
   - Deneme yanılma ile bulundu

## RViz Görselleştirme

### Aktif Display'ler
- **RobotModel** - Robot 3D modeli
- **TF** - Koordinat frame'leri
- **Camera** - RGB kamera görüntüsü
- **DepthCloud** - Renkli point cloud (RGB + Depth birleşimi)
- **Odometry** - Hareket yörüngesi

### Topic Eşleştirmeleri
| Display | Topic |
|---------|-------|
| Camera | /camera/rgbd_camera/image_raw |
| DepthCloud Color | /camera/rgbd_camera/image_raw |
| DepthCloud Depth | /camera/rgbd_camera/depth/image_raw |
| Odometry | /odom |

## IMU Veri Görselleştirme

PlotJuggler veya rqt_plot ile `/imu/data` topic'i izleniyor:

### İzlenen Değerler
- `angular_velocity/x, y, z` - Açısal hız (rad/s)
- `linear_acceleration/x, y, z` - Doğrusal ivme (m/s²)

### Beklenen Davranış
- Düz giderken: `angular_velocity/z ≈ 0`
- Dönerken: `angular_velocity/z` artar/azalır
- İvmelenmede: `linear_acceleration/x` değişir

## Çalıştırma Talimatları

### Tüm sistemi başlat:
```bash
cd ~/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_hw1 hw3.launch.py
```

### Sadece Gazebo (RViz olmadan):
```bash
ros2 launch robot_hw1 hw3.launch.py use_rviz:=false
```

### Robot hareketsiz başlat:
```bash
ros2 launch robot_hw1 hw3.launch.py run_controller:=false
```

### IMU plot (ayrı terminal):
```bash
ros2 run rqt_plot rqt_plot /imu/data/angular_velocity/x /imu/data/angular_velocity/y /imu/data/angular_velocity/z
```

## Bilinen Sorunlar ve Çözümler

| Sorun | Çözüm |
|-------|-------|
| RViz libpthread hatası | `export QT_QPA_PLATFORM=xcb` |
| Zemin glitch/flickering | empty_office.world kullan (ground plane yok) |
| Robot köşede takılıyor | Stuck recovery eklendi (1.5sn sonra kurtarma) |
| Kamera topic bulunamıyor | Topic adları güncellendi (/camera/rgbd_camera/...) |

## Video ve Ekran Görüntüleri

- Video linki: [Google Drive'a yüklenecek]
- Videoda gösterilenler:
  - Gazebo'da office world ve robot
  - RViz'de kamera + depth cloud
  - PlotJuggler/rqt_plot'ta IMU verileri
  - Robot koridorda hareket ediyor
