# Realistic Simulation Parameters

## Overview

This document explains the realistic parameters added to the Pioneer 3-DX simulation to model real-world robot behavior, including sensor noise, odometry drift, and wheel slip.

---

## Why Add Realism?

**Default Gazebo behavior:**
- Perfect sensor readings (no noise)
- Ideal wheel encoders (no accumulated error)
- Perfect friction (no slip)
- Deterministic physics (repeatable exactly)

**Real robots experience:**
- Sensor measurement noise
- Encoder quantization errors
- Wheel slippage on surfaces
- Odometry drift over time
- Environmental uncertainties

---

## Parameters Added

### 1. Odometry Plugin Noise (`pioneer3dx_plugins_simple.xacro`)

Located in: `~/p3dx_ws/src/p3dx/p3dx_description/urdf/p3dx/pioneer3dx_plugins_simple.xacro`

```xml
<!-- Realistic noise parameters for odometry -->
<odometry_source>encoder</odometry_source>

<!-- Covariance for pose (x, y, yaw) - models accumulated error -->
<covariance_x>0.0001</covariance_x>
<covariance_y>0.0001</covariance_y>
<covariance_yaw>0.01</covariance_yaw>

<!-- Noise in odometry measurements -->
<noise>0.05</noise>

<!-- Simulate wheel slip on turns -->
<wheel_slip_compliance>0.02</wheel_slip_compliance>
```

**Explanation:**
- `odometry_source="encoder"`: Uses encoder-based odometry (not ground truth GPS)
- `covariance_x/y/yaw`: Models uncertainty that accumulates over time
- `noise`: Adds 5 cm Gaussian noise to position measurements
- `wheel_slip_compliance`: 2% slip during turns (realistic for smooth floors)

---

### 2. Wheel Friction Parameters (`pioneer3dx_wheel.xacro`)

Located in: `~/p3dx_ws/src/p3dx/p3dx_description/urdf/p3dx/pioneer3dx_wheel.xacro`

```xml
<!-- Realistic friction parameters -->
<mu1>0.8</mu1>  <!-- Friction coefficient in primary direction -->
<mu2>0.7</mu2>  <!-- Friction coefficient in secondary direction -->
<kp>1000000.0</kp>  <!-- Contact stiffness -->
<kd>100.0</kd>  <!-- Contact damping -->
<slip1>0.02</slip1>  <!-- Slip in primary direction (rolling) -->
<slip2>0.03</slip2>  <!-- Slip in secondary direction (lateral) -->
```

**Explanation:**
- `mu1 ≠ mu2`: Anisotropic friction (different in rolling vs lateral direction)
- `kp/kd`: Contact dynamics between wheel and floor
- `slip1/slip2`: Small slip percentages model real tire-floor interaction
- Values chosen to match indoor smooth floor (like lab tile)

---

## Expected Behavior

### Before Realistic Parameters:
- ✅ Robot returns to exact same coordinates
- ✅ Circular trajectory perfectly overlaps
- ✅ No visible drift over time

### After Realistic Parameters:
- ⚠️ Small position drift accumulates (few centimeters per loop)
- ⚠️ Trajectory spirals slightly outward/inward
- ⚠️ Multiple loops show non-overlapping paths
- ⚠️ Odometry covariance increases over time

---

## Testing Drift

### Run Circular Motion Test:

```bash
# Terminal 1: Launch Gazebo
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 launch p3dx_gazebo p3dx.launch.py

# Terminal 2: Run motion controller
source /opt/ros/humble/setup.bash
source ~/p3dx_ws/install/setup.bash
ros2 run p3dx_gazebo cmd_vel_publisher.py

# Terminal 3: Plot trajectory
source /opt/ros/humble/setup.bash
ros2 run plotjuggler plotjuggler
# Subscribe to /odom
# Plot X vs Y in 2D XY plot
```

### What to Observe:

1. **Plotjuggler X-Y Plot:**
   - Initial circles are tight
   - Over time (30-60 seconds), trajectory drifts
   - Circles no longer perfectly overlap

2. **RViz Odometry Display:**
   - Enable "Covariance" option in Odometry display
   - Observe ellipse growing over time (uncertainty increase)

3. **Ground Truth Comparison:**
   - Subscribe to `/ground_truth/pose` topic
   - Compare with `/odom` topic
   - Difference shows accumulated odometry error

---

## Parameter Tuning Guide

### To Increase Drift (More Realistic):
```xml
<noise>0.10</noise>  <!-- 10 cm noise -->
<covariance_yaw>0.02</covariance_yaw>  <!-- More yaw uncertainty -->
<slip1>0.05</slip1>  <!-- 5% slip -->
```

### To Decrease Drift (Better Sensors):
```xml
<noise>0.01</noise>  <!-- 1 cm noise -->
<covariance_yaw>0.001</covariance_yaw>  <!-- Less yaw uncertainty -->
<slip1>0.005</slip1>  <!-- 0.5% slip -->
```

### To Simulate Different Surfaces:

**Carpet (high friction, more slip):**
```xml
<mu1>1.2</mu1>
<mu2>1.0</mu2>
<slip1>0.05</slip1>
<slip2>0.08</slip2>
```

**Ice/Slippery (low friction, lots of slip):**
```xml
<mu1>0.2</mu1>
<mu2>0.15</mu2>
<slip1>0.15</slip1>
<slip2>0.20</slip2>
```

**Ideal Lab Floor (current settings):**
```xml
<mu1>0.8</mu1>
<mu2>0.7</mu2>
<slip1>0.02</slip1>
<slip2>0.03</slip2>
```

---

## Real-World Equivalents

| Parameter | Simulation Value | Real Robot Equivalent |
|-----------|------------------|----------------------|
| `noise` | 0.05 m | Wheel encoder resolution ~1-2 mm |
| `covariance_x/y` | 0.0001 | Position drift ~1-2 cm after 10m |
| `covariance_yaw` | 0.01 rad | Heading drift ~0.5° per turn |
| `slip1` | 0.02 | 2% wheel slip (smooth floor) |
| `mu1` | 0.8 | Rubber on tile coefficient |

---

## Benefits of Realistic Simulation

1. **Better Testing:** Algorithms must handle uncertainty
2. **Real-World Preparation:** Results translate to actual robots
3. **Failure Case Discovery:** Exposes edge cases early
4. **Algorithm Robustness:** Forces use of sensor fusion (e.g., IMU + odometry)
5. **Educational Value:** Students learn about real robot challenges

---

## References

- Gazebo Diff Drive Plugin: http://classic.gazebosim.org/tutorials?tut=ros2_installing
- ODE Friction Parameters: https://docs.gazebosim.org/
- Pioneer 3-DX Specs: https://www.generationrobots.com/media/Pioneer3DX-P3DX-RevA.pdf

---

**Modified Files:**
- `p3dx_description/urdf/p3dx/pioneer3dx_plugins_simple.xacro`
- `p3dx_description/urdf/p3dx/pioneer3dx_wheel.xacro`

**Author:** mmf
**Date:** October 2025
