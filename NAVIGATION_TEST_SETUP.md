# Navigation Test Setup - Turkish Instructions

## Özet (Summary)
- ✅ Gazebo açılacak (Gazebo will open)
- ✅ 447MB haritanız yüklenecek (Your 447MB map will load)
- ✅ Nav2 otomatik başlayacak (Nav2 will auto-start)
- ✅ Robotunuz harita üzerinde navigasyon yapabilecek (Your robot can navigate on the map)

---

## Terminal Kurulumu (Terminal Setup)

### BAŞLAMADAN ÖNCE (BEFORE STARTING):
Sadece ÇEŞİT 1 yapın. Türü 2 sadece tamamen SIFIRLDAN SLAM yapmak istersen yaparsın.

**TİP 1: Mevcut 447MB Haritayı Kullan (USE EXISTING MAP - RECOMMENDED)**
```bash
# Terminal 1 (Gazebo, SLAM, Nav2)
cd /home/mmf/Documents/GitHub/hws_repo
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robot_project full_navigation.launch.py

# Terminal 2 (Transform Lookup Monitor)
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run tf2_ros tf2_echo map base_link

# Terminal 3 (Robot State Viewer)
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic echo /amcl_pose

# Terminal 4 (Navigation Goal Sender)
# Bunu 15-20 saniye sonra çalıştır (Run this after 15-20 seconds)
source /opt/ros/humble/setup.bash
source install/setup.bash

# Bir test hedefi gönder (Send a test goal):
ros2 topic pub --once /goal_pose geometry_msgs/PoseStamped "{
  header: {frame_id: 'map'},
  pose: {
    position: {x: 5.0, y: 2.0, z: 0.0},
    orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
  }
}"

# 5 saniye bekle, sonra başka hedef gönder
sleep 5

# İkinci hedef
ros2 topic pub --once /goal_pose geometry_msgs/PoseStamped "{
  header: {frame_id: 'map'},
  pose: {
    position: {x: -5.0, y: 3.0, z: 0.0},
    orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
  }
}"
```

---

## Ne Olacak? (What Will Happen?)

### Terminal 1 Çıktısı (Terminal 1 Output - Gazebo/SLAM/Nav2):
```
[gazebo-1] Starting Gazebo simulation...
[gazebo-1] Loading office world...
[robot_state_publisher-2] Publishing robot state...
[spawn_entity.py-3] Spawning office model...
[spawn_robot-4] Spawning pioneer3dx robot...
[ekf_filter_node-5] Starting EKF sensor fusion...
[depthimage_to_laserscan_node-6] Converting depth to laser scan...
[rtabmap-7] Initializing RTAB-Map SLAM...
[rtabmap-7] Loading database: ~/.ros/rtabmap.db
[rtabmap-7] Database loaded with 5000+ nodes
[controller_server-8] Starting Nav2 controller...
[planner_server-9] Starting Nav2 planner...
[bt_navigator-10] Starting Behavior Tree navigator...
[rviz2-11] Starting RViz visualization...
```

### Terminal 2 Çıktısı (Terminal 2 Output - TF Monitor):
```
At time 25.123
- Translation: [-0.234, 1.456, 0.100]
- Rotation: in Quaternion [0.000, 0.000, 0.523, 0.852]

At time 26.134
- Translation: [-0.198, 1.523, 0.100]
...
```
⬅️ Sürüklü güncelleme görmeliyiz (Should show continuous updates)
⚠️ "extrapolation into past" hatası OLMAMALI (Should NOT show)

### Terminal 3 Çıktısı (Terminal 3 Output - AMCL Pose):
```
header:
  stamp:
    sec: 25
    nsec: 567890123
pose:
  pose:
    position:
      x: -0.234
      y: 1.456
      z: 0.100
```
⬅️ Robot'un harita üzerindeki pozisyonu gösterir

### Terminal 4 Sonucu (Terminal 4 Result):
Robot şunları yapmalı:
1. ✅ Hedefi kabul etmelidir (Accept goal)
2. ✅ İleri doğru HAREKET etmelidir (Move FORWARD, not just rotate)
3. ✅ Hedefin yakınına gelmeli (Go near the goal position)
4. ✅ Harita üzerinde navigasyon yapması görülmeli (Visible in RViz)

---

## Gazebo Nerede? (Where is Gazebo?)

**Terminal 1'de Gazebo penceresi açılacak!**

```
Timing:
- 0-2s: Gazebo başlıyor
- 2s: Office dünyası yükleniyor
- 4s: Robot spawn ediliyor
- 6s: EKF başlıyor
- 8s: Depth to LaserScan başlıyor
- 10s: RTAB-Map SLAM başlıyor (447MB harita yükleniyor!)
- 12s: Evaluation nodes başlıyor
- 15s: Nav2 stack başlıyor
- 16s: RViz açılıyor
```

---

## Haritanız Nerede? (Where is Your Map?)

**Dosya konumu:**
```
~/.ros/rtabmap.db (447MB)
```

**Launch dosyasında:**
```
src/robot_project/launch/full_navigation.launch.py - Line 210:
'database_path': '~/.ros/rtabmap.db'
```

✅ **Bu dosya otomatik olarak yüklenecektir!** (Will auto-load)

---

## Eğer Yeni SLAM Yapmak İstersen (If You Want Fresh SLAM)

Eğer haritayı sifirlardan yapmak istersen:

**Seçenek 1: Veritabanını sil**
```bash
rm ~/.ros/rtabmap.db
# Sonra normal launch et
ros2 launch robot_project full_navigation.launch.py
```

**Seçenek 2: Veritabanını yedekle ve yeni başla**
```bash
mv ~/.ros/rtabmap.db ~/.ros/rtabmap.db.backup
ros2 launch robot_project full_navigation.launch.py
```

---

## RViz'de Göreceklerin (What You'll See in RViz)

- 🗺️ **3D Map Points**: Senin 447MB haritandaki 5000+ nod
- 🤖 **Robot**: Pivoting gözüken model
- 📍 **AMCL Pose**: Harita üzerindeki robot pozisyonu
- 📊 **Costmap**: Nav2'nin bariyer algıladığı bölgeler
- ➡️ **Global Plan**: Robot'un gideceği yol
- 🎯 **Goal**: Gönderdiğin hedef noktası

---

## Test Kontrol Listesi (Test Checklist)

Başarılı olup olmadığını kontrol et:

- [ ] Terminal 1: Gazebo açıldı ve simulation çalışıyor
- [ ] Terminal 1: "Loading database" mesajı görüldü
- [ ] Terminal 1: Nav2 nodes başlamadan hata yok
- [ ] Terminal 2: TF'ler sürekli güncelleniyor (extrapolation hatası yok)
- [ ] Terminal 3: Robot pozisyonu güncelleniyor
- [ ] RViz: Harita görülüyor (pek çok point cloud)
- [ ] RViz: Robot modeli harita üzerinde görülüyor
- [ ] Terminal 4: Robot hedefi kabul etti (INFO log, ERROR yok)
- [ ] RViz: Robot yolunu planlıyor ve hareket ediyor
- [ ] ✅ **Robot İLERİ hareket ediyor (sadece dönmüyor)**

---

## Sorun Çözme (Troubleshooting)

### Problem: "extrapolation into past" hatası
**Çözüm:** TF synchronization düzeltmesi yaptık - başarılı olmalı

### Problem: "Goal rejected" hatası
**Çözüm:**
1. Nav2'nin çıkmasını bekle (15+ saniye)
2. Gazebo'da robot hareket edip etmediğini kontrol et
3. TF tree'ye bak: `ros2 run tf2_tools view_frames`

### Problem: Robot hareket etmiyor, sadece dönüyor
**Çözüm:**
1. Harita görülüyor mu? (Terminal 1'de "Loading database" var mı?)
2. Costmaps güncel mi? (RViz'de gösteriyor mu?)
3. TF'ler doğru mu? (Terminal 2 çalışıyor mu?)

### Problem: Gazebo penceresi açılmadı
**Çözüm:**
```bash
export QT_QPA_PLATFORM=xcb
ros2 launch robot_project full_navigation.launch.py
```

---

## Sonuç (Conclusion)

✅ **Tüm ayarlamalar yapıldı:**
- TF synchronization düzeltildi
- 447MB haritanız yüklenecek
- Nav2 otonom navigasyon yapabilecek
- Gazebo simülasyonu çalışacak

**Şimdi test etmeye hazırsınız!** 🚀
