#!/usr/bin/env python3
"""
HW3: Corridor Navigator Node
Uses depth camera to navigate through corridors while avoiding obstacles.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import numpy as np


class CorridorNavigator(Node):
    def __init__(self):
        super().__init__('corridor_navigator')

        # Parameters
        self.declare_parameter('linear_speed', 0.3)  # Forward speed (m/s)
        self.declare_parameter('angular_speed', 0.5)  # Turn speed (rad/s)
        self.declare_parameter('min_distance', 0.8)  # Minimum distance to obstacle (m)
        self.declare_parameter('critical_distance', 0.4)  # Stop distance (m)

        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.min_distance = self.get_parameter('min_distance').value
        self.critical_distance = self.get_parameter('critical_distance').value

        # CV Bridge for image conversion
        self.bridge = CvBridge()

        # Publisher for velocity commands
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscriber for depth image (from RGBD camera)
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/rgbd_camera/depth/image_raw',
            self.depth_callback,
            10
        )

        # Timer for control loop (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

        # State variables
        self.left_distance = float('inf')
        self.center_distance = float('inf')
        self.right_distance = float('inf')
        self.far_left_distance = float('inf')
        self.far_right_distance = float('inf')
        self.last_turn_direction = 1  # 1 = left, -1 = right
        self.stuck_counter = 0  # Count how long we've been stuck
        self.last_center_distance = float('inf')
        self.turn_in_progress = False
        self.turn_start_time = None

        self.get_logger().info('Corridor Navigator started')
        self.get_logger().info(f'Min distance: {self.min_distance}m, Critical: {self.critical_distance}m')

    def depth_callback(self, msg):
        """Process depth image to detect obstacles in 5 regions for better corner detection."""
        try:
            # Convert ROS Image to numpy array
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

            # Get image dimensions
            height, width = depth_image.shape[:2]

            # Define regions of interest
            # Use middle vertical strip for better obstacle detection
            v_start = int(height * 0.3)
            v_end = int(height * 0.7)

            # 5 horizontal divisions for better corner detection
            w1 = int(width * 0.15)   # far left edge
            w2 = int(width * 0.35)   # left
            w3 = int(width * 0.65)   # right
            w4 = int(width * 0.85)   # far right edge

            far_left_region = depth_image[v_start:v_end, 0:w1]
            left_region = depth_image[v_start:v_end, w1:w2]
            center_region = depth_image[v_start:v_end, w2:w3]
            right_region = depth_image[v_start:v_end, w3:w4]
            far_right_region = depth_image[v_start:v_end, w4:width]

            # Calculate minimum distance in each region (ignore invalid readings)
            self.far_left_distance = self.get_min_distance(far_left_region)
            self.left_distance = self.get_min_distance(left_region)
            self.center_distance = self.get_min_distance(center_region)
            self.right_distance = self.get_min_distance(right_region)
            self.far_right_distance = self.get_min_distance(far_right_region)

        except Exception as e:
            self.get_logger().error(f'Error processing depth image: {e}')

    def get_min_distance(self, region):
        """Get minimum valid distance from a depth region."""
        # Filter out invalid values (0, nan, inf)
        valid_mask = np.isfinite(region) & (region > 0.1) & (region < 10.0)
        if np.any(valid_mask):
            return float(np.min(region[valid_mask]))
        return float('inf')

    def control_loop(self):
        """Main control loop - decide movement based on obstacle distances."""
        twist = Twist()
        current_time = self.get_clock().now()

        # Detect if stuck (distance not changing much)
        if abs(self.center_distance - self.last_center_distance) < 0.05 and self.center_distance < self.min_distance:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_center_distance = self.center_distance

        # Calculate total space on each side (including far regions)
        left_space = min(self.far_left_distance, self.left_distance)
        right_space = min(self.far_right_distance, self.right_distance)

        # Log distances periodically
        self.get_logger().debug(
            f'Distances - FL: {self.far_left_distance:.2f}m, L: {self.left_distance:.2f}m, '
            f'C: {self.center_distance:.2f}m, R: {self.right_distance:.2f}m, FR: {self.far_right_distance:.2f}m'
        )

        # STUCK RECOVERY: If stuck for too long, do aggressive turn
        if self.stuck_counter > 15:  # 1.5 seconds stuck
            twist.linear.x = -0.1  # Back up slightly
            twist.angular.z = self.angular_speed * 1.5 * self.last_turn_direction
            self.get_logger().warn('STUCK! Aggressive recovery maneuver...')
            if self.stuck_counter > 30:  # Reset after 3 seconds
                self.stuck_counter = 0
                self.last_turn_direction *= -1  # Try other direction

        # CORNER DETECTION: All forward directions blocked
        elif (self.center_distance < self.critical_distance and
              self.left_distance < self.min_distance and
              self.right_distance < self.min_distance):
            # Corner! Stop and turn aggressively
            twist.linear.x = -0.05  # Tiny reverse
            # Check far edges to decide turn direction
            if self.far_left_distance > self.far_right_distance:
                twist.angular.z = self.angular_speed * 1.2
                self.last_turn_direction = 1
            else:
                twist.angular.z = -self.angular_speed * 1.2
                self.last_turn_direction = -1
            self.get_logger().info('CORNER detected! Sharp turn...')

        # CRITICAL: Center blocked
        elif self.center_distance < self.critical_distance:
            twist.linear.x = 0.0
            # Use far regions for better decision
            if left_space > right_space:
                twist.angular.z = self.angular_speed * 1.0
                self.last_turn_direction = 1
            else:
                twist.angular.z = -self.angular_speed * 1.0
                self.last_turn_direction = -1
            self.get_logger().info('CRITICAL: Obstacle ahead! Turning...')

        # APPROACHING: Center obstacle detected
        elif self.center_distance < self.min_distance:
            twist.linear.x = self.linear_speed * 0.2
            if left_space > right_space:
                twist.angular.z = self.angular_speed * 0.8
                self.last_turn_direction = 1
            else:
                twist.angular.z = -self.angular_speed * 0.8
                self.last_turn_direction = -1
            self.get_logger().info('Obstacle detected, adjusting course...')

        # WALL FOLLOWING: Wall on one side
        elif self.left_distance < self.min_distance and self.right_distance >= self.min_distance:
            twist.linear.x = self.linear_speed * 0.8
            twist.angular.z = -self.angular_speed * 0.4

        elif self.right_distance < self.min_distance and self.left_distance >= self.min_distance:
            twist.linear.x = self.linear_speed * 0.8
            twist.angular.z = self.angular_speed * 0.4

        # NARROW CORRIDOR: Walls on both sides
        elif self.left_distance < self.min_distance and self.right_distance < self.min_distance:
            twist.linear.x = self.linear_speed * 0.5
            diff = self.left_distance - self.right_distance
            twist.angular.z = diff * 0.8  # Proportional correction

        # CLEAR PATH: Go forward
        else:
            twist.linear.x = self.linear_speed
            twist.angular.z = 0.0

        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = CorridorNavigator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the robot before shutting down
        stop_twist = Twist()
        node.cmd_vel_pub.publish(stop_twist)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
