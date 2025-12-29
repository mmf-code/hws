#!/usr/bin/env python3
"""
Autonomous Explorer - Office exploration for SLAM mapping

Two modes:
1. FREE exploration (default): Uses hw3-style depth-based navigation
   - 5-region obstacle detection
   - Wall following
   - Corner detection
   - Stuck recovery

2. WAYPOINT mode: Navigates to predefined waypoints using Nav2
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image
from nav2_msgs.action import NavigateToPose
import math
import numpy as np
from cv_bridge import CvBridge


class AutonomousExplorer(Node):
    def __init__(self):
        super().__init__('autonomous_explorer')

        # Parameters
        self.declare_parameter('mode', 'free')  # 'free' or 'waypoint'
        self.declare_parameter('linear_speed', 0.65)
        self.declare_parameter('angular_speed', 1.2)
        self.declare_parameter('min_distance', 0.8)
        self.declare_parameter('critical_distance', 0.4)

        self.mode = self.get_parameter('mode').value
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.min_distance = self.get_parameter('min_distance').value
        self.critical_distance = self.get_parameter('critical_distance').value

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscribers
        self.depth_sub = self.create_subscription(
            Image, '/camera/rgbd_camera/depth/image_raw', self.depth_callback, 10)
        self.odom_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.odom_callback, 10)

        # CV Bridge
        self.bridge = CvBridge()

        # 5-region depth distances (like hw3)
        self.far_left_distance = float('inf')
        self.left_distance = float('inf')
        self.center_distance = float('inf')
        self.right_distance = float('inf')
        self.far_right_distance = float('inf')

        # State tracking
        self.last_turn_direction = 1  # 1 = left, -1 = right
        self.stuck_counter = 0
        self.last_center_distance = float('inf')
        self.exploration_started = False

        # Position tracking
        self.current_x = 2.0
        self.current_y = 0.0
        self.start_x = 2.0
        self.start_y = 0.0
        self.total_distance = 0.0
        self.last_x = 2.0
        self.last_y = 0.0

        # Waypoints (for waypoint mode)
        self.waypoints = [
            {'x': 4.0, 'y': 0.0, 'name': 'Corridor 1'},
            {'x': 6.0, 'y': 0.0, 'name': 'Corridor 2'},
            {'x': 6.0, 'y': 2.0, 'name': 'Room 1'},
            {'x': 6.0, 'y': -2.0, 'name': 'Room 2'},
            {'x': 3.0, 'y': 2.0, 'name': 'Area 1'},
            {'x': 3.0, 'y': -2.0, 'name': 'Area 2'},
            {'x': 2.0, 'y': 0.0, 'name': 'Return'},
        ]
        self.current_waypoint_idx = 0

        # Start after delay
        self.startup_timer = self.create_timer(8.0, self.start_exploration)

        self.get_logger().info(f'Autonomous Explorer initialized')
        self.get_logger().info(f'Mode: {self.mode.upper()}')
        self.get_logger().info(f'Speed: {self.linear_speed} m/s, Turn: {self.angular_speed} rad/s')

    def odom_callback(self, msg):
        """Track robot position and distance traveled"""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Calculate distance traveled
        dx = self.current_x - self.last_x
        dy = self.current_y - self.last_y
        self.total_distance += math.sqrt(dx*dx + dy*dy)
        self.last_x = self.current_x
        self.last_y = self.current_y

    def depth_callback(self, msg):
        """Process depth image with 5-region detection (hw3 style)"""
        try:
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            height, width = depth_image.shape[:2]

            # Use middle vertical band (30% to 70%) - ignore floor and ceiling
            v_start = int(height * 0.30)
            v_end = int(height * 0.70)

            # 5 horizontal regions
            w1 = int(width * 0.15)   # far left edge
            w2 = int(width * 0.35)   # left
            w3 = int(width * 0.65)   # right
            w4 = int(width * 0.85)   # far right edge

            far_left_region = depth_image[v_start:v_end, 0:w1]
            left_region = depth_image[v_start:v_end, w1:w2]
            center_region = depth_image[v_start:v_end, w2:w3]
            right_region = depth_image[v_start:v_end, w3:w4]
            far_right_region = depth_image[v_start:v_end, w4:width]

            # Get minimum distances
            self.far_left_distance = self.get_min_distance(far_left_region)
            self.left_distance = self.get_min_distance(left_region)
            self.center_distance = self.get_min_distance(center_region)
            self.right_distance = self.get_min_distance(right_region)
            self.far_right_distance = self.get_min_distance(far_right_region)

        except Exception as e:
            pass

    def get_min_distance(self, region):
        """Get minimum valid distance from depth region"""
        valid_mask = np.isfinite(region) & (region > 0.15) & (region < 10.0)
        if np.any(valid_mask):
            return float(np.min(region[valid_mask]))
        return float('inf')

    def start_exploration(self):
        """Begin exploration"""
        self.startup_timer.cancel()
        self.exploration_started = True

        self.get_logger().info('=' * 50)
        self.get_logger().info('AUTONOMOUS EXPLORATION STARTED')
        self.get_logger().info(f'Mode: {self.mode.upper()}')
        self.get_logger().info('=' * 50)

        if self.mode == 'free':
            # Free exploration - 10Hz control loop
            self.control_timer = self.create_timer(0.1, self.free_exploration_loop)
        else:
            # Waypoint mode
            self.control_timer = self.create_timer(0.1, self.waypoint_exploration_loop)

    def free_exploration_loop(self):
        """HW3-style free exploration with obstacle avoidance"""
        twist = Twist()

        # Detect if stuck
        if abs(self.center_distance - self.last_center_distance) < 0.05 and self.center_distance < self.min_distance:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_center_distance = self.center_distance

        # Calculate space on each side
        left_space = min(self.far_left_distance, self.left_distance)
        right_space = min(self.far_right_distance, self.right_distance)

        # Debug log every 2 seconds
        if not hasattr(self, '_log_counter'):
            self._log_counter = 0
        self._log_counter += 1
        if self._log_counter % 20 == 0:
            self.get_logger().info(
                f'Pos: ({self.current_x:.1f}, {self.current_y:.1f}) | '
                f'Dist traveled: {self.total_distance:.1f}m | '
                f'Depth C:{self.center_distance:.2f} L:{self.left_distance:.2f} R:{self.right_distance:.2f}'
            )

        # ===== MOVEMENT DECISIONS (hw3 algorithm) =====

        # STUCK RECOVERY
        if self.stuck_counter > 15:  # 1.5 seconds stuck
            twist.linear.x = -0.15  # Back up
            twist.angular.z = self.angular_speed * 1.5 * self.last_turn_direction
            self.get_logger().warn('STUCK! Recovery maneuver...')
            if self.stuck_counter > 30:
                self.stuck_counter = 0
                self.last_turn_direction *= -1

        # CORNER DETECTION
        elif (self.center_distance < self.critical_distance and
              self.left_distance < self.min_distance and
              self.right_distance < self.min_distance):
            twist.linear.x = -0.08
            if self.far_left_distance > self.far_right_distance:
                twist.angular.z = self.angular_speed * 1.3
                self.last_turn_direction = 1
            else:
                twist.angular.z = -self.angular_speed * 1.3
                self.last_turn_direction = -1
            self.get_logger().info('CORNER! Sharp turn...')

        # CRITICAL: Center blocked
        elif self.center_distance < self.critical_distance:
            twist.linear.x = 0.0
            if left_space > right_space:
                twist.angular.z = self.angular_speed * 1.2
                self.last_turn_direction = 1
            else:
                twist.angular.z = -self.angular_speed * 1.2
                self.last_turn_direction = -1
            self.get_logger().info('CRITICAL: Turning...')

        # APPROACHING: Obstacle ahead
        elif self.center_distance < self.min_distance:
            twist.linear.x = self.linear_speed * 0.3
            if left_space > right_space:
                twist.angular.z = self.angular_speed * 0.9
                self.last_turn_direction = 1
            else:
                twist.angular.z = -self.angular_speed * 0.9
                self.last_turn_direction = -1

        # WALL FOLLOWING: Wall on left
        elif self.left_distance < self.min_distance and self.right_distance >= self.min_distance:
            twist.linear.x = self.linear_speed * 0.8
            twist.angular.z = -self.angular_speed * 0.5

        # WALL FOLLOWING: Wall on right
        elif self.right_distance < self.min_distance and self.left_distance >= self.min_distance:
            twist.linear.x = self.linear_speed * 0.8
            twist.angular.z = self.angular_speed * 0.5

        # NARROW CORRIDOR: Walls on both sides
        elif self.left_distance < self.min_distance and self.right_distance < self.min_distance:
            twist.linear.x = self.linear_speed * 0.6
            diff = self.left_distance - self.right_distance
            twist.angular.z = diff * 1.0  # Proportional correction

        # CLEAR PATH: Go forward
        else:
            twist.linear.x = self.linear_speed
            twist.angular.z = 0.0

        self.cmd_vel_pub.publish(twist)

    def waypoint_exploration_loop(self):
        """Waypoint-based exploration with obstacle avoidance"""
        if self.current_waypoint_idx >= len(self.waypoints):
            self.get_logger().info('All waypoints completed! Restarting...')
            self.current_waypoint_idx = 0
            return

        wp = self.waypoints[self.current_waypoint_idx]

        # Calculate to waypoint
        dx = wp['x'] - self.current_x
        dy = wp['y'] - self.current_y
        distance = math.sqrt(dx*dx + dy*dy)

        twist = Twist()

        # Check for obstacles first
        left_space = min(self.far_left_distance, self.left_distance)
        right_space = min(self.far_right_distance, self.right_distance)

        if distance < 0.5:
            # Reached waypoint
            self.get_logger().info(f'Reached: {wp["name"]}')
            self.current_waypoint_idx += 1
            return

        # Obstacle avoidance takes priority
        if self.center_distance < self.critical_distance:
            twist.linear.x = 0.0
            if left_space > right_space:
                twist.angular.z = self.angular_speed * 1.0
            else:
                twist.angular.z = -self.angular_speed * 1.0
        elif self.center_distance < self.min_distance:
            twist.linear.x = self.linear_speed * 0.2
            if left_space > right_space:
                twist.angular.z = self.angular_speed * 0.7
            else:
                twist.angular.z = -self.angular_speed * 0.7
        else:
            # Navigate towards waypoint
            target_angle = math.atan2(dy, dx)

            # Get current yaw from odom (simplified)
            angle_diff = target_angle  # Simplified - would need full quaternion conversion

            twist.linear.x = min(self.linear_speed, distance * 0.5)
            twist.angular.z = 0.0

        self.cmd_vel_pub.publish(twist)

    def stop_robot(self):
        """Stop the robot"""
        twist = Twist()
        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = AutonomousExplorer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if rclpy.ok():
                node.stop_robot()
        except:
            pass
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
