#!/usr/bin/env python3
"""
Evaluation Node - Compares SLAM/EKF output with ground truth

Subscribes to:
    /ground_truth/odom  - Perfect odometry from Gazebo p3d plugin
    /odometry/filtered  - EKF fused odometry (IMU + wheel)
    /localization_pose  - SLAM corrected pose from RTAB-Map

Publishes:
    /evaluation/rmse   - Real-time RMSE value
    /evaluation/ate    - Absolute Trajectory Error

Saves:
    CSV files with trajectory data and metrics for comparison

Metrics:
    - RMSE: Root Mean Square Error
    - ATE: Absolute Trajectory Error
    - RPE: Relative Pose Error
    - Max Error, Std Dev
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import Float64
import numpy as np
from collections import deque
import csv
import os
from datetime import datetime
# SLAM corrected pose comes from /localization_pose topic (RTAB-Map output)


class EvaluationNode(Node):
    def __init__(self):
        super().__init__('evaluation_node')

        # Parameters
        self.declare_parameter('output_dir', 'project/results/data')
        self.declare_parameter('window_size', 100)
        self.declare_parameter('slam_mode', 'rgbd')  # 'rgbd' or 'icp'
        self.declare_parameter('save_interval', 30.0)  # Save metrics every N seconds

        self.output_dir = self.get_parameter('output_dir').value
        self.window_size = self.get_parameter('window_size').value
        self.slam_mode = self.get_parameter('slam_mode').value
        self.save_interval = self.get_parameter('save_interval').value

        # Data storage (circular buffers for real-time metrics)
        self.gt_poses = deque(maxlen=self.window_size)
        self.filtered_poses = deque(maxlen=self.window_size)
        self.slam_poses = deque(maxlen=self.window_size)

        # Full trajectory storage for saving
        self.gt_trajectory = []
        self.filtered_trajectory = []
        self.slam_trajectory = []

        # Metrics history
        self.metrics_history = []

        # Subscribers
        self.gt_sub = self.create_subscription(
            Odometry, '/ground_truth/odom', self.gt_callback, 10)
        self.filtered_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.filtered_callback, 10)
        # SLAM corrected pose from RTAB-Map localization
        self.slam_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/localization_pose', self.slam_pose_callback, 10)

        # Publishers
        self.rmse_pub = self.create_publisher(Float64, '/evaluation/rmse', 10)
        self.ate_pub = self.create_publisher(Float64, '/evaluation/ate', 10)

        # Timer for periodic metrics calculation (every 2 seconds)
        self.metrics_timer = self.create_timer(2.0, self.calculate_metrics)

        # Timer for periodic saving
        self.save_timer = self.create_timer(self.save_interval, self.save_metrics_snapshot)

        self.get_logger().info(f'Evaluation node started (SLAM mode: {self.slam_mode})')
        self.get_logger().info(f'Output directory: {self.output_dir}')

    def extract_pose(self, msg):
        """Extract x, y, z, timestamp from Odometry message"""
        return {
            'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            'x': msg.pose.pose.position.x,
            'y': msg.pose.pose.position.y,
            'z': msg.pose.pose.position.z
        }

    def gt_callback(self, msg):
        pose = self.extract_pose(msg)
        self.gt_poses.append(pose)
        self.gt_trajectory.append(pose)

    def filtered_callback(self, msg):
        pose = self.extract_pose(msg)
        self.filtered_poses.append(pose)
        self.filtered_trajectory.append(pose)

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

    def find_closest_by_timestamp(self, target_ts, pose_list, max_diff=0.5):
        """Find pose with closest timestamp within max_diff seconds"""
        if len(pose_list) == 0:
            return None

        best_idx = 0
        best_diff = abs(pose_list[0]['timestamp'] - target_ts)

        for i, pose in enumerate(pose_list):
            diff = abs(pose['timestamp'] - target_ts)
            if diff < best_diff:
                best_diff = diff
                best_idx = i

        if best_diff > max_diff:
            return None
        return pose_list[best_idx]

    def calculate_position_errors(self, gt_list, est_list):
        """Calculate position errors between ground truth and estimate using timestamp matching"""
        if len(gt_list) < 2 or len(est_list) < 2:
            return None

        errors = []
        for gt in gt_list:
            # Find estimate with closest timestamp
            est = self.find_closest_by_timestamp(gt['timestamp'], est_list)
            if est is None:
                continue

            error = np.sqrt(
                (gt['x'] - est['x'])**2 +
                (gt['y'] - est['y'])**2 +
                (gt['z'] - est['z'])**2
            )
            errors.append(error)

        if len(errors) == 0:
            return None
        return np.array(errors)

    def calculate_ate(self, errors):
        """Absolute Trajectory Error - mean of position errors"""
        if errors is None or len(errors) == 0:
            return 0.0
        return np.mean(errors)

    def calculate_rmse(self, errors):
        """Root Mean Square Error"""
        if errors is None or len(errors) == 0:
            return 0.0
        return np.sqrt(np.mean(errors**2))

    def calculate_rpe(self, gt_list, est_list, time_delta=1.0):
        """
        Relative Pose Error - error in relative motion between poses
        time_delta: time difference in seconds between pose pairs
        """
        if len(gt_list) < 10 or len(est_list) < 10:
            return 0.0

        rpe_errors = []
        for gt_start in gt_list[:-10]:
            # Find GT pose ~time_delta seconds later
            target_ts = gt_start['timestamp'] + time_delta
            gt_end = self.find_closest_by_timestamp(target_ts, gt_list, max_diff=0.5)
            if gt_end is None:
                continue

            # Find corresponding estimated poses
            est_start = self.find_closest_by_timestamp(gt_start['timestamp'], est_list)
            est_end = self.find_closest_by_timestamp(gt_end['timestamp'], est_list)

            if est_start is None or est_end is None:
                continue

            # Ground truth relative motion
            gt_dx = gt_end['x'] - gt_start['x']
            gt_dy = gt_end['y'] - gt_start['y']

            # Estimated relative motion
            est_dx = est_end['x'] - est_start['x']
            est_dy = est_end['y'] - est_start['y']

            # RPE is the error in relative motion
            rpe = np.sqrt((gt_dx - est_dx)**2 + (gt_dy - est_dy)**2)
            rpe_errors.append(rpe)

        if len(rpe_errors) == 0:
            return 0.0
        return np.mean(rpe_errors)

    def calculate_metrics(self):
        """Calculate all metrics between ground truth and odometry sources"""
        if len(self.gt_poses) < 10:
            return

        gt_list = list(self.gt_poses)
        filtered_list = list(self.filtered_poses)
        slam_list = list(self.slam_poses)

        # EKF metrics
        ekf_errors = self.calculate_position_errors(gt_list, filtered_list)
        ekf_rmse = self.calculate_rmse(ekf_errors) if ekf_errors is not None else 0.0
        ekf_ate = self.calculate_ate(ekf_errors) if ekf_errors is not None else 0.0
        ekf_rpe = self.calculate_rpe(gt_list, filtered_list)
        ekf_max = np.max(ekf_errors) if ekf_errors is not None and len(ekf_errors) > 0 else 0.0
        ekf_std = np.std(ekf_errors) if ekf_errors is not None and len(ekf_errors) > 0 else 0.0

        # SLAM metrics (if available)
        slam_errors = self.calculate_position_errors(gt_list, slam_list)
        slam_rmse = self.calculate_rmse(slam_errors) if slam_errors is not None else 0.0
        slam_ate = self.calculate_ate(slam_errors) if slam_errors is not None else 0.0
        slam_rpe = self.calculate_rpe(gt_list, slam_list)
        slam_max = np.max(slam_errors) if slam_errors is not None and len(slam_errors) > 0 else 0.0
        slam_std = np.std(slam_errors) if slam_errors is not None and len(slam_errors) > 0 else 0.0

        # Publish RMSE and ATE
        rmse_msg = Float64()
        rmse_msg.data = ekf_rmse
        self.rmse_pub.publish(rmse_msg)

        ate_msg = Float64()
        ate_msg.data = ekf_ate
        self.ate_pub.publish(ate_msg)

        # Store metrics
        current_time = self.get_clock().now().nanoseconds / 1e9
        metrics = {
            'timestamp': current_time,
            'slam_mode': self.slam_mode,
            'ekf_rmse': ekf_rmse,
            'ekf_ate': ekf_ate,
            'ekf_rpe': ekf_rpe,
            'ekf_max': ekf_max,
            'ekf_std': ekf_std,
            'slam_rmse': slam_rmse,
            'slam_ate': slam_ate,
            'slam_rpe': slam_rpe,
            'slam_max': slam_max,
            'slam_std': slam_std,
        }
        self.metrics_history.append(metrics)

        # Log metrics
        log_msg = (
            f'[{self.slam_mode.upper()}] '
            f'EKF: RMSE={ekf_rmse:.4f}m ATE={ekf_ate:.4f}m RPE={ekf_rpe:.4f}m '
            f'Max={ekf_max:.4f}m Std={ekf_std:.4f}m'
        )
        if len(slam_list) > 10:
            log_msg += (
                f' | SLAM: RMSE={slam_rmse:.4f}m ATE={slam_ate:.4f}m RPE={slam_rpe:.4f}m'
            )
        self.get_logger().info(log_msg)

    def save_metrics_snapshot(self):
        """Periodically save metrics to file"""
        if len(self.metrics_history) == 0:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save metrics history
        metrics_file = os.path.join(
            self.output_dir,
            f'metrics_{self.slam_mode}_{timestamp}.csv'
        )
        fieldnames = [
            'timestamp', 'slam_mode',
            'ekf_rmse', 'ekf_ate', 'ekf_rpe', 'ekf_max', 'ekf_std',
            'slam_rmse', 'slam_ate', 'slam_rpe', 'slam_max', 'slam_std'
        ]
        with open(metrics_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics_history)

        self.get_logger().info(f'Metrics snapshot saved to {metrics_file}')

    def save_results(self):
        """Save all trajectory data to CSV files"""
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save ground truth
        if len(self.gt_trajectory) > 0:
            gt_file = os.path.join(self.output_dir, f'ground_truth_{timestamp}.csv')
            with open(gt_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y', 'z'])
                writer.writeheader()
                writer.writerows(self.gt_trajectory)
            self.get_logger().info(f'Ground truth saved: {len(self.gt_trajectory)} poses')

        # Save EKF filtered
        if len(self.filtered_trajectory) > 0:
            filt_file = os.path.join(self.output_dir, f'filtered_{self.slam_mode}_{timestamp}.csv')
            with open(filt_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y', 'z'])
                writer.writeheader()
                writer.writerows(self.filtered_trajectory)
            self.get_logger().info(f'EKF filtered saved: {len(self.filtered_trajectory)} poses')

        # Save SLAM odometry
        if len(self.slam_trajectory) > 0:
            slam_file = os.path.join(self.output_dir, f'slam_{self.slam_mode}_{timestamp}.csv')
            with open(slam_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y', 'z'])
                writer.writeheader()
                writer.writerows(self.slam_trajectory)
            self.get_logger().info(f'SLAM odometry saved: {len(self.slam_trajectory)} poses')

        # Save final metrics summary
        if len(self.metrics_history) > 0:
            metrics_file = os.path.join(
                self.output_dir,
                f'metrics_{self.slam_mode}_{timestamp}.csv'
            )
            fieldnames = [
                'timestamp', 'slam_mode',
                'ekf_rmse', 'ekf_ate', 'ekf_rpe', 'ekf_max', 'ekf_std',
                'slam_rmse', 'slam_ate', 'slam_rpe', 'slam_max', 'slam_std'
            ]
            with open(metrics_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.metrics_history)
            self.get_logger().info(f'Metrics saved: {len(self.metrics_history)} entries')

        # Print final summary
        if len(self.metrics_history) > 0:
            last = self.metrics_history[-1]
            self.get_logger().info(
                f'\n'
                f'========== FINAL SUMMARY ({self.slam_mode.upper()}) ==========\n'
                f'EKF vs Ground Truth:\n'
                f'  RMSE: {last["ekf_rmse"]:.4f} m\n'
                f'  ATE:  {last["ekf_ate"]:.4f} m\n'
                f'  RPE:  {last["ekf_rpe"]:.4f} m\n'
                f'  Max:  {last["ekf_max"]:.4f} m\n'
                f'  Std:  {last["ekf_std"]:.4f} m\n'
                f'SLAM vs Ground Truth:\n'
                f'  RMSE: {last["slam_rmse"]:.4f} m\n'
                f'  ATE:  {last["slam_ate"]:.4f} m\n'
                f'  RPE:  {last["slam_rpe"]:.4f} m\n'
                f'================================================'
            )


def main(args=None):
    rclpy.init(args=args)
    node = EvaluationNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down, saving results...')
        node.save_results()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
