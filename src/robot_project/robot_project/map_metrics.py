#!/usr/bin/env python3
"""
Map Metrics Node - Calculates 3D map quality metrics for SLAM comparison

Subscribes to:
    /rtabmap/cloud_map - 3D point cloud map from RTAB-Map

Calculates:
    - Point cloud density (points per cubic meter)
    - 2D density (points per square meter)
    - Coverage area (2D footprint in m²)
    - Volume coverage (3D bounding box)
    - Bounding box dimensions (X, Y, Z)

Saves:
    CSV files with metrics history for RGBD vs ICP comparison
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import numpy as np
import csv
import os
from datetime import datetime

# For reading PointCloud2 data
try:
    import sensor_msgs_py.point_cloud2 as pc2
    HAS_PC2 = True
except ImportError:
    HAS_PC2 = False


class MapMetricsNode(Node):
    def __init__(self):
        super().__init__('map_metrics_node')

        if not HAS_PC2:
            self.get_logger().warn(
                'sensor_msgs_py not available, limited functionality'
            )

        # Parameters
        self.declare_parameter('output_dir', 'project/results/data')
        self.declare_parameter('slam_mode', 'rgbd')  # 'rgbd' or 'icp'
        self.declare_parameter('save_interval', 30.0)  # Save every N seconds
        self.declare_parameter('voxel_size', 0.1)

        self.output_dir = self.get_parameter('output_dir').value
        self.slam_mode = self.get_parameter('slam_mode').value
        self.save_interval = self.get_parameter('save_interval').value
        self.voxel_size = self.get_parameter('voxel_size').value

        # Subscribers
        self.map_sub = self.create_subscription(
            PointCloud2, '/rtabmap/cloud_map', self.map_callback, 10)

        # Store metrics history
        self.metrics_history = []
        self.latest_metrics = {}
        self.start_time = self.get_clock().now().nanoseconds / 1e9

        # Timer for periodic reporting
        self.report_timer = self.create_timer(10.0, self.report_metrics)

        # Timer for periodic saving
        self.save_timer = self.create_timer(self.save_interval, self.save_metrics)

        self.get_logger().info(f'Map Metrics node started (SLAM mode: {self.slam_mode})')
        self.get_logger().info(f'Output directory: {self.output_dir}')

    def map_callback(self, msg):
        """Process incoming point cloud map"""
        if not HAS_PC2:
            return

        try:
            # Read points from message
            points_gen = pc2.read_points(
                msg,
                field_names=['x', 'y', 'z'],
                skip_nans=True
            )

            # Convert to numpy array
            points_list = []
            for p in points_gen:
                points_list.append([p[0], p[1], p[2]])

            if len(points_list) == 0:
                return

            points_array = np.array(points_list, dtype=np.float32)

            # Calculate all metrics
            current_time = self.get_clock().now().nanoseconds / 1e9
            elapsed_time = current_time - self.start_time

            metrics = {
                'timestamp': current_time,
                'elapsed_time': elapsed_time,
                'slam_mode': self.slam_mode,
                'num_points': len(points_array),
                'density_3d': self.calculate_density_3d(points_array),
                'density_2d': self.calculate_density_2d(points_array),
                'coverage_2d': self.calculate_coverage_2d(points_array),
                'volume': self.calculate_volume(points_array),
                'bbox_x': 0.0,
                'bbox_y': 0.0,
                'bbox_z': 0.0,
                'z_range_min': 0.0,
                'z_range_max': 0.0,
            }

            # Add bounding box
            bbox = self.calculate_bounding_box(points_array)
            metrics['bbox_x'] = bbox['x']
            metrics['bbox_y'] = bbox['y']
            metrics['bbox_z'] = bbox['z']
            metrics['z_range_min'] = bbox.get('z_min', 0.0)
            metrics['z_range_max'] = bbox.get('z_max', 0.0)

            self.latest_metrics = metrics
            self.metrics_history.append(metrics)

        except Exception as e:
            self.get_logger().error(f'Error processing point cloud: {e}')

    def calculate_density_3d(self, points):
        """Calculate points per cubic meter (3D density)"""
        if len(points) == 0:
            return 0.0

        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        dimensions = max_coords - min_coords

        # Avoid division by zero
        volume = np.prod(np.maximum(dimensions, 0.001))

        return len(points) / volume

    def calculate_density_2d(self, points):
        """Calculate points per square meter (2D projection density)"""
        if len(points) == 0:
            return 0.0

        min_xy = np.min(points[:, :2], axis=0)
        max_xy = np.max(points[:, :2], axis=0)
        area = np.prod(np.maximum(max_xy - min_xy, 0.001))

        return len(points) / area

    def calculate_coverage_2d(self, points):
        """Calculate 2D footprint area in square meters"""
        if len(points) == 0:
            return 0.0

        min_xy = np.min(points[:, :2], axis=0)
        max_xy = np.max(points[:, :2], axis=0)

        return np.prod(max_xy - min_xy)

    def calculate_volume(self, points):
        """Calculate 3D bounding box volume"""
        if len(points) == 0:
            return 0.0

        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)

        return np.prod(max_coords - min_coords)

    def calculate_bounding_box(self, points):
        """Calculate 3D bounding box dimensions"""
        if len(points) == 0:
            return {'x': 0, 'y': 0, 'z': 0, 'z_min': 0, 'z_max': 0}

        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        dimensions = max_coords - min_coords

        return {
            'x': float(dimensions[0]),
            'y': float(dimensions[1]),
            'z': float(dimensions[2]),
            'z_min': float(min_coords[2]),
            'z_max': float(max_coords[2])
        }

    def report_metrics(self):
        """Log current metrics to console"""
        if not self.latest_metrics:
            self.get_logger().info('Waiting for point cloud data...')
            return

        m = self.latest_metrics
        self.get_logger().info(
            f'\n[{self.slam_mode.upper()}] Map Metrics:\n'
            f'  Points: {m.get("num_points", 0):,}\n'
            f'  3D Density: {m.get("density_3d", 0):.2f} pts/m³\n'
            f'  2D Density: {m.get("density_2d", 0):.2f} pts/m²\n'
            f'  Coverage: {m.get("coverage_2d", 0):.2f} m²\n'
            f'  Volume: {m.get("volume", 0):.2f} m³\n'
            f'  BBox: {m.get("bbox_x", 0):.2f}m x {m.get("bbox_y", 0):.2f}m x {m.get("bbox_z", 0):.2f}m\n'
            f'  Z range: [{m.get("z_range_min", 0):.2f}, {m.get("z_range_max", 0):.2f}]m'
        )

    def save_metrics(self):
        """Save metrics history to CSV file"""
        if len(self.metrics_history) == 0:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        filename = os.path.join(
            self.output_dir,
            f'map_metrics_{self.slam_mode}_{timestamp}.csv'
        )

        fieldnames = [
            'timestamp', 'elapsed_time', 'slam_mode', 'num_points',
            'density_3d', 'density_2d', 'coverage_2d', 'volume',
            'bbox_x', 'bbox_y', 'bbox_z', 'z_range_min', 'z_range_max'
        ]

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics_history)

        self.get_logger().info(f'Metrics saved to {filename}')

    def save_final_results(self):
        """Save final metrics and summary"""
        if len(self.metrics_history) == 0:
            return

        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save full history
        filename = os.path.join(
            self.output_dir,
            f'map_metrics_{self.slam_mode}_{timestamp}.csv'
        )

        fieldnames = [
            'timestamp', 'elapsed_time', 'slam_mode', 'num_points',
            'density_3d', 'density_2d', 'coverage_2d', 'volume',
            'bbox_x', 'bbox_y', 'bbox_z', 'z_range_min', 'z_range_max'
        ]

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.metrics_history)

        # Print final summary
        if len(self.metrics_history) > 0:
            last = self.metrics_history[-1]
            first = self.metrics_history[0]

            self.get_logger().info(
                f'\n'
                f'========== FINAL MAP METRICS ({self.slam_mode.upper()}) ==========\n'
                f'Duration: {last["elapsed_time"]:.1f} seconds\n'
                f'Final Point Count: {last["num_points"]:,}\n'
                f'Final 3D Density: {last["density_3d"]:.2f} pts/m³\n'
                f'Final 2D Density: {last["density_2d"]:.2f} pts/m²\n'
                f'Final Coverage: {last["coverage_2d"]:.2f} m²\n'
                f'Final Volume: {last["volume"]:.2f} m³\n'
                f'BBox: {last["bbox_x"]:.2f}m x {last["bbox_y"]:.2f}m x {last["bbox_z"]:.2f}m\n'
                f'Growth: {first["num_points"]} -> {last["num_points"]} points\n'
                f'================================================'
            )

        self.get_logger().info(f'Final results saved to {filename}')


def main(args=None):
    rclpy.init(args=args)
    node = MapMetricsNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down, saving final results...')
        node.save_final_results()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
