# SLAM Metrics Verification Report

**Team 14 - KON414E Final Project**
**Date:** 27 December 2024

---

## Problem Summary

SLAM metrics were incorrectly showing 0 or identical values to EKF metrics due to:
1. **TF-based SLAM pose = EKF pose** - Static `map -> odom` identity transform
2. **RTAB-Map `/rtabmap/odom` topic had 0 publishers** - Topic doesn't exist in our configuration

## Solution Applied

Changed from TF-based approach to **topic-based SLAM metrics**:

| Before | After |
|--------|-------|
| TF lookup `map -> base_link` | Subscribe to `/localization_pose` topic |
| Odometry type message | PoseWithCovarianceStamped message |
| Index-based pose matching | Timestamp-based pose matching |

### Code Changes

**File:** `src/robot_project/robot_project/evaluation_node.py`

```python
# OLD (TF-based - didn't work)
# self.tf_timer = self.create_timer(0.1, self.sample_slam_from_tf)

# NEW (Topic-based - works correctly)
from geometry_msgs.msg import PoseWithCovarianceStamped

self.slam_sub = self.create_subscription(
    PoseWithCovarianceStamped, '/localization_pose', self.slam_pose_callback, 10)

def slam_pose_callback(self, msg):
    """Handle PoseWithCovarianceStamped from /localization_pose"""
    pose = {
        'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
        'x': msg.pose.pose.position.x,
        'y': msg.pose.pose.position.y,
        'z': msg.pose.pose.position.z
    }
    self.slam_poses.append(pose)
    self.slam_trajectory.append(pose)
```

---

## Verification Results

### 1. TF Transform Check

```bash
ros2 run tf2_ros tf2_echo map odom
```

**Result:** Static identity transform (as expected with static_transform_publisher)
```
Translation: [0.000, 0.000, 0.000]
Rotation: [0.000, 0.000, 0.000, 1.000]
```

**Conclusion:** TF-based approach was returning `odom` frame data for `map` frame lookups.

### 2. Topic Frame Verification

| Topic | frame_id | Expected | Status |
|-------|----------|----------|--------|
| `/localization_pose` | `map` | `map` | PASS |
| `/odometry/filtered` | `odom` | `odom` | PASS |

### 3. Position Comparison (Same Timestamp)

| Topic | x | y | z |
|-------|---|---|---|
| `/localization_pose` | -3.39 | 0.33 | 0.0007 |
| `/odometry/filtered` | -3.94 | 0.96 | 0.0 |

**Difference:** ~0.8m in position - Confirms SLAM and EKF are providing different (independent) measurements.

### 4. Metrics Verification

**RGBD Mode Test (~3 minutes):**
```
EKF RMSE:  0.0108m
SLAM RMSE: 0.0991m
```

**ICP Mode Test (~3 minutes):**
```
EKF RMSE:  0.0101m
SLAM RMSE: 0.0945m
```

**Key Finding:** SLAM and EKF metrics are now **different** (as expected).

---

## Scientific Interpretation

### Why SLAM RMSE > EKF RMSE?

1. **EKF uses wheel odometry directly** - Low drift in short distances
2. **SLAM uses visual/ICP matching** - More computation, occasional feature mismatch
3. **Simulation ideal conditions** - No wheel slip, perfect sensor models

### Expected vs Observed

| Metric | Expected | Observed | Status |
|--------|----------|----------|--------|
| SLAM != EKF | Different values | 0.09m vs 0.01m | PASS |
| ICP slightly better than RGBD | ICP < RGBD | 0.0945 < 0.0991 | PASS |
| Low EKF error | < 0.05m | ~0.01m | PASS (simulation) |

---

## Data Sources Summary

| Data Type | Topic | Message Type | Frame |
|-----------|-------|--------------|-------|
| Ground Truth | `/ground_truth/odom` | Odometry | `world` |
| EKF Fused | `/odometry/filtered` | Odometry | `odom` |
| SLAM Corrected | `/localization_pose` | PoseWithCovarianceStamped | `map` |

---

## Files Modified

1. `src/robot_project/robot_project/evaluation_node.py`
   - Changed SLAM subscription from `/rtabmap/odom` to `/localization_pose`
   - Added timestamp-based pose matching
   - Updated RPE calculation to use time deltas

---

## Commit Information

**Commit:** `26d9403`
**Message:** "Fix SLAM metrics: Use /localization_pose topic instead of TF-based approach"

---

## Conclusion

The SLAM metrics fix is **verified and working correctly**:

- SLAM pose comes from `/localization_pose` (RTAB-Map loop-closure corrected pose)
- EKF pose comes from `/odometry/filtered` (robot_localization sensor fusion)
- Both provide independent measurements with different error characteristics
- Static `map -> odom` TF is kept for RViz visualization only
