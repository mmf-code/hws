#!/usr/bin/env python3
"""
Simple Goal Navigator - Direct cmd_vel control without Nav2
Requirement 7: "Use 2D projection of computed 3D map for navigation.
Assign random points to move the robot autonomously."
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import Image
import numpy as np
import math
import random
import time
from cv_bridge import CvBridge


class SimpleGoalNav(Node):
    def __init__(self):
        super().__init__('simple_goal_nav')

        # Parameters
        self.declare_parameter('num_goals', 10)
        self.declare_parameter('linear_speed', 0.5)
        self.declare_parameter('angular_speed', 1.0)
        self.declare_parameter('goal_tolerance', 0.5)

        self.num_goals = self.get_parameter('num_goals').value
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.goal_tolerance = self.get_parameter('goal_tolerance').value

        # Publishers
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscribers
        map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, map_qos)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.depth_sub = self.create_subscription(Image, '/camera/rgbd_camera/depth/image_raw',
                                                   self.depth_callback, 10)

        # State
        self.map_data = None
        self.map_info = None
        self.free_cells = []
        self.open_area_cells = []
        self.robot_x = 2.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.goal_x = None
        self.goal_y = None
        self.goals_completed = 0
        self.goal_index = 0  # Current goal number (1-indexed for display)
        self.bridge = CvBridge()
        self.center_distance = float('inf')
        self.left_distance = float('inf')
        self.right_distance = float('inf')
        self.navigating = False  # Flag to prevent double-counting
        self.finished = False

        # Timeout tracking
        self.goal_start_time = None
        self.goal_initial_dist = 0.0
        self.goal_timeout = 60.0

        # Start after delay
        self.create_timer(5.0, self.start_navigation, callback_group=None)
        self.control_timer = None
        self.started = False

        self.get_logger().info('=' * 50)
        self.get_logger().info('Simple Goal Navigator - Direct Control')
        self.get_logger().info(f'Total Goals: {self.num_goals}')
        self.get_logger().info('=' * 50)

    def map_callback(self, msg):
        """Process map and extract free cells, prioritize open areas"""
        if self.map_data is not None:
            return

        self.map_info = msg.info
        self.map_data = np.array(msg.data).reshape((msg.info.height, msg.info.width))

        # Find free cells and score by openness
        for y in range(2, msg.info.height - 2):
            for x in range(2, msg.info.width - 2):
                if self.map_data[y, x] == 0:
                    wx = msg.info.origin.position.x + x * msg.info.resolution
                    wy = msg.info.origin.position.y + y * msg.info.resolution
                    self.free_cells.append((wx, wy))

                    # Check if open area (count free neighbors in 5x5 area)
                    neighbors = self.map_data[y-2:y+3, x-2:x+3]
                    free_count = np.sum(neighbors == 0)
                    if free_count >= 20:
                        self.open_area_cells.append((wx, wy))

        self.get_logger().info(f'Map: {len(self.free_cells)} free cells, {len(self.open_area_cells)} open areas')

    def odom_callback(self, msg):
        """Track robot position"""
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.robot_yaw = math.atan2(2.0*(q.w*q.z + q.x*q.y), 1.0 - 2.0*(q.y*q.y + q.z*q.z))

    def depth_callback(self, msg):
        """Process depth for obstacle avoidance"""
        try:
            depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            h, w = depth.shape[:2]
            v_start, v_end = int(h * 0.3), int(h * 0.7)

            left = depth[v_start:v_end, :int(w*0.33)]
            center = depth[v_start:v_end, int(w*0.33):int(w*0.66)]
            right = depth[v_start:v_end, int(w*0.66):]

            self.left_distance = self.get_min_dist(left)
            self.center_distance = self.get_min_dist(center)
            self.right_distance = self.get_min_dist(right)
        except:
            pass

    def get_min_dist(self, region):
        valid = np.isfinite(region) & (region > 0.1) & (region < 10.0)
        return float(np.min(region[valid])) if np.any(valid) else float('inf')

    def start_navigation(self):
        """Begin navigation"""
        if self.started:
            return
        self.started = True

        if not self.free_cells:
            self.get_logger().warn('No map data yet, waiting...')
            self.create_timer(2.0, self.start_navigation)
            return

        self.select_new_goal()
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('Navigation started!')

    def select_new_goal(self):
        """Select goal based on phase"""
        if not self.free_cells or self.finished:
            return False

        self.goal_index += 1

        if self.goal_index > self.num_goals:
            self.finish()
            return False

        # Determine distance range based on goal number
        # Office map is ~32m x 35m
        if self.goal_index <= 3:
            min_dist, max_dist = 3.0, 7.0
            phase = "SHORT"
        elif self.goal_index <= 6:
            min_dist, max_dist = 7.0, 12.0
            phase = "MEDIUM"
        else:
            min_dist, max_dist = 10.0, 20.0
            phase = "LONG"

        source_cells = self.open_area_cells if self.open_area_cells else self.free_cells

        # Filter cells by distance
        valid_cells = []
        for wx, wy in source_cells:
            dist = math.sqrt((wx - self.robot_x)**2 + (wy - self.robot_y)**2)
            if min_dist < dist < max_dist:
                valid_cells.append((wx, wy, dist))

        # If no cells in range, expand search
        if not valid_cells:
            for wx, wy in self.free_cells:
                dist = math.sqrt((wx - self.robot_x)**2 + (wy - self.robot_y)**2)
                if 1.0 < dist < 8.0:
                    valid_cells.append((wx, wy, dist))

        if not valid_cells:
            self.get_logger().warn(f'No valid goal for [{self.goal_index}], skipping...')
            return self.select_new_goal()

        # Select random goal
        wx, wy, dist = random.choice(valid_cells)
        self.goal_x, self.goal_y = wx, wy
        self.goal_start_time = time.time()
        self.goal_initial_dist = dist
        self.navigating = True

        # Timeout: ~12 sec per meter + base time for turning/obstacles
        self.goal_timeout = 30.0 + (dist * 12.0)
        self.get_logger().info(f'[{self.goal_index}/{self.num_goals}] {phase}: ({self.goal_x:.1f}, {self.goal_y:.1f}) dist={dist:.1f}m timeout={self.goal_timeout:.0f}s')
        return True

    def control_loop(self):
        """Main control loop with timeout"""
        if self.finished or not self.navigating:
            return

        if self.goal_x is None:
            return

        twist = Twist()

        # Distance to goal
        dx = self.goal_x - self.robot_x
        dy = self.goal_y - self.robot_y
        dist = math.sqrt(dx*dx + dy*dy)

        # Check timeout
        elapsed = time.time() - self.goal_start_time

        if elapsed > self.goal_timeout:
            self.get_logger().warn(f'[{self.goal_index}/{self.num_goals}] TIMEOUT ({elapsed:.0f}s)')
            self.navigating = False
            self.goal_x = None
            self.create_timer(1.0, self.select_new_goal, callback_group=None)
            return

        # Goal reached?
        if dist < self.goal_tolerance:
            self.goals_completed += 1
            self.get_logger().info(f'[{self.goal_index}/{self.num_goals}] REACHED! (Success: {self.goals_completed}/{self.goal_index})')
            self.navigating = False
            self.goal_x = None

            # Stop robot
            self.cmd_pub.publish(Twist())

            if self.goal_index < self.num_goals:
                self.create_timer(2.0, self.select_new_goal, callback_group=None)
            else:
                self.finish()
            return

        # Angle to goal
        target_yaw = math.atan2(dy, dx)
        angle_diff = target_yaw - self.robot_yaw
        while angle_diff > math.pi: angle_diff -= 2*math.pi
        while angle_diff < -math.pi: angle_diff += 2*math.pi

        # Obstacle avoidance
        if self.center_distance < 0.4:
            twist.linear.x = 0.0
            twist.angular.z = self.angular_speed if self.left_distance > self.right_distance else -self.angular_speed
        elif self.center_distance < 0.8:
            twist.linear.x = self.linear_speed * 0.3
            twist.angular.z = self.angular_speed * 0.8 * (1 if self.left_distance > self.right_distance else -1)
        else:
            if abs(angle_diff) > 0.3:
                twist.linear.x = self.linear_speed * 0.2
                twist.angular.z = self.angular_speed * (1 if angle_diff > 0 else -1)
            else:
                twist.linear.x = min(self.linear_speed, dist * 0.5)
                twist.angular.z = angle_diff * 1.5

        self.cmd_pub.publish(twist)

    def finish(self):
        """Navigation complete"""
        if self.finished:
            return
        self.finished = True

        if self.control_timer:
            self.control_timer.cancel()

        self.cmd_pub.publish(Twist())

        rate = (self.goals_completed / self.num_goals * 100) if self.num_goals > 0 else 0

        self.get_logger().info('=' * 50)
        self.get_logger().info('NAVIGATION COMPLETE')
        self.get_logger().info(f'Goals Reached: {self.goals_completed}/{self.num_goals}')
        self.get_logger().info(f'Success Rate: {rate:.1f}%')
        self.get_logger().info('=' * 50)


def main(args=None):
    rclpy.init(args=args)
    node = SimpleGoalNav()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
