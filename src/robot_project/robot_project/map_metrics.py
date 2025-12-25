#!/usr/bin/env python3
"""
Map Metrics Node - Calculates 3D map quality metrics

Subscribes to:
    /rtabmap/cloud_map - 3D point cloud map

Calculates:
    - Point cloud density (points per cubic meter)
    - Coverage area (2D footprint)
    - Bounding box dimensions
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import numpy as np

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
        self.declare_parameter('voxel_size', 0.1)
        self.voxel_size = self.get_parameter('voxel_size').value

        # Subscribers
        self.map_sub = self.create_subscription(
            PointCloud2, '/rtabmap/cloud_map', self.map_callback, 10)

        # Store latest metrics
        self.latest_metrics = {}

        # Timer for periodic reporting
        self.timer = self.create_timer(10.0, self.report_metrics)

        self.get_logger().info('Map Metrics node started')

    def map_callback(self, msg):
        """Process incoming point cloud map"""
        if not HAS_PC2:
            self.get_logger().warn('Cannot process point cloud without sensor_msgs_py')
            return

        try:
            # Read points from message
            points_gen = pc2.read_points(
                msg,
                field_names=['x', 'y', 'z'],
                skip_nans=True
            )

            # Convert structured array to regular 2D array
            points_list = []
            for p in points_gen:
                points_list.append([p[0], p[1], p[2]])

            if len(points_list) == 0:
                return

            points_array = np.array(points_list, dtype=np.float32)

            # Calculate metrics
            self.latest_metrics = {
                'num_points': len(points_array),
                'density': self.calculate_density(points_array),
                'coverage': self.calculate_coverage(points_array),
                'bbox': self.calculate_bounding_box(points_array)
            }

        except Exception as e:
            self.get_logger().error(f'Error processing point cloud: {e}')

    def calculate_density(self, points):
        """Calculate points per cubic meter"""
        if len(points) == 0:
            return 0.0

        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        dimensions = max_coords - min_coords

        # Avoid division by zero
        volume = np.prod(np.maximum(dimensions, 0.001))

        return len(points) / volume

    def calculate_coverage(self, points):
        """Calculate 2D footprint area in square meters"""
        if len(points) == 0:
            return 0.0

        min_xy = np.min(points[:, :2], axis=0)
        max_xy = np.max(points[:, :2], axis=0)

        return np.prod(max_xy - min_xy)

    def calculate_bounding_box(self, points):
        """Calculate 3D bounding box dimensions"""
        if len(points) == 0:
            return {'x': 0, 'y': 0, 'z': 0}

        min_coords = np.min(points, axis=0)
        max_coords = np.max(points, axis=0)
        dimensions = max_coords - min_coords

        return {
            'x': float(dimensions[0]),
            'y': float(dimensions[1]),
            'z': float(dimensions[2])
        }

    def report_metrics(self):
        """Log current metrics"""
        if not self.latest_metrics:
            self.get_logger().info('Waiting for point cloud data...')
            return

        m = self.latest_metrics
        bbox = m.get('bbox', {})

        self.get_logger().info(
            f"Map Metrics:\n"
            f"  Points: {m.get('num_points', 0):,}\n"
            f"  Density: {m.get('density', 0):.2f} pts/m³\n"
            f"  Coverage: {m.get('coverage', 0):.2f} m²\n"
            f"  Bbox: {bbox.get('x', 0):.2f}m x {bbox.get('y', 0):.2f}m x {bbox.get('z', 0):.2f}m"
        )


def main(args=None):
    rclpy.init(args=args)
    node = MapMetricsNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
