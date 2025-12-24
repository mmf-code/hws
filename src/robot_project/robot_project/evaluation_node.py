#!/usr/bin/env python3
"""
Evaluation Node - Compares SLAM output with ground truth

Subscribes to:
    /ground_truth/odom - Perfect odometry from Gazebo
    /odometry/filtered - EKF fused odometry
    /rtabmap/odom      - SLAM odometry (when available)

Publishes:
    /evaluation/metrics - Evaluation metrics (RMSE, etc.)

Saves:
    CSV files with trajectory data for plotting
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64
import numpy as np
from collections import deque
import csv
import os
from datetime import datetime


class EvaluationNode(Node):
    def __init__(self):
        super().__init__('evaluation_node')

        # Parameters
        self.declare_parameter('output_dir', 'project/results/data')
        self.declare_parameter('window_size', 100)

        self.output_dir = self.get_parameter('output_dir').value
        self.window_size = self.get_parameter('window_size').value

        # Data storage (circular buffers)
        self.gt_poses = deque(maxlen=self.window_size)
        self.filtered_poses = deque(maxlen=self.window_size)
        self.slam_poses = deque(maxlen=self.window_size)

        # Full trajectory storage for saving
        self.gt_trajectory = []
        self.filtered_trajectory = []

        # Subscribers
        self.gt_sub = self.create_subscription(
            Odometry, '/ground_truth/odom', self.gt_callback, 10)
        self.filtered_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.filtered_callback, 10)

        # Publisher for RMSE
        self.rmse_pub = self.create_publisher(Float64, '/evaluation/rmse', 10)

        # Timer for periodic metrics calculation (every 2 seconds)
        self.timer = self.create_timer(2.0, self.calculate_metrics)

        self.get_logger().info('Evaluation node started')
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

    def calculate_metrics(self):
        """Calculate RMSE between ground truth and filtered odometry"""
        if len(self.gt_poses) < 10 or len(self.filtered_poses) < 10:
            return

        # Simple RMSE calculation (position only)
        n = min(len(self.gt_poses), len(self.filtered_poses))
        errors = []

        gt_list = list(self.gt_poses)
        filtered_list = list(self.filtered_poses)

        for i in range(n):
            gt = gt_list[i]
            filt = filtered_list[i]
            error = np.sqrt(
                (gt['x'] - filt['x'])**2 +
                (gt['y'] - filt['y'])**2 +
                (gt['z'] - filt['z'])**2
            )
            errors.append(error)

        rmse = np.sqrt(np.mean(np.array(errors)**2))
        max_error = np.max(errors)
        mean_error = np.mean(errors)

        # Publish RMSE
        rmse_msg = Float64()
        rmse_msg.data = rmse
        self.rmse_pub.publish(rmse_msg)

        self.get_logger().info(
            f'RMSE: {rmse:.4f}m | Mean: {mean_error:.4f}m | Max: {max_error:.4f}m'
        )

    def save_results(self):
        """Save trajectory data to CSV files"""
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save ground truth
        gt_file = os.path.join(self.output_dir, f'ground_truth_{timestamp}.csv')
        with open(gt_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y', 'z'])
            writer.writeheader()
            writer.writerows(self.gt_trajectory)

        # Save filtered
        filt_file = os.path.join(self.output_dir, f'filtered_{timestamp}.csv')
        with open(filt_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y', 'z'])
            writer.writeheader()
            writer.writerows(self.filtered_trajectory)

        self.get_logger().info(f'Results saved to {self.output_dir}')


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
        rclpy.shutdown()


if __name__ == '__main__':
    main()
