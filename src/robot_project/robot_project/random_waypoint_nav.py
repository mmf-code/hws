#!/usr/bin/env python3
"""
Random Waypoint Navigator - Autonomous navigation with random goals

Uses Nav2 to navigate to randomly generated waypoints from the 2D occupancy grid.
Implements Requirement 7: "Use 2D projection of the computed 3D map for navigation.
Assign random points in the environment to move the robot autonomously."

Subscribes to:
    /map - OccupancyGrid from RTAB-Map
    /amcl_pose - Robot pose from AMCL

Action Client:
    /navigate_to_pose - Nav2 NavigateToPose action

Usage:
    ros2 run robot_project random_waypoint_nav
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus
import numpy as np
import random
import math
import time


class RandomWaypointNavigator(Node):
    def __init__(self):
        super().__init__('random_waypoint_navigator')

        # Parameters
        self.declare_parameter('num_waypoints', 10)
        self.declare_parameter('min_obstacle_distance', 0.5)  # meters
        self.declare_parameter('goal_timeout', 120.0)  # seconds
        self.declare_parameter('min_goal_distance', 1.0)  # min distance from robot
        self.declare_parameter('max_goal_distance', 8.0)  # max distance from robot
        self.declare_parameter('wait_between_goals', 2.0)  # seconds

        self.num_waypoints = self.get_parameter('num_waypoints').value
        self.min_obstacle_distance = self.get_parameter('min_obstacle_distance').value
        self.goal_timeout = self.get_parameter('goal_timeout').value
        self.min_goal_distance = self.get_parameter('min_goal_distance').value
        self.max_goal_distance = self.get_parameter('max_goal_distance').value
        self.wait_between_goals = self.get_parameter('wait_between_goals').value

        # Callback groups for concurrency
        self.callback_group = ReentrantCallbackGroup()

        # Map data
        self.map_data = None
        self.map_info = None
        self.free_cells = []

        # Robot pose
        self.robot_pose = None

        # Navigation state
        self.is_navigating = False
        self.current_goal = None
        self.goal_handle = None

        # Metrics
        self.total_goals = 0
        self.successful_goals = 0
        self.failed_goals = 0
        self.timeout_goals = 0
        self.start_time = None
        self.navigation_times = []

        # QoS for map (RTAB-Map uses TRANSIENT_LOCAL)
        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        # Subscribers
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, map_qos,
            callback_group=self.callback_group)
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10,
            callback_group=self.callback_group)

        # Nav2 action client
        self.nav_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=self.callback_group)

        # Wait for Nav2 to be ready
        self.get_logger().info('Waiting for Nav2 action server...')
        if not self.nav_client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error('Nav2 action server not available!')
            return

        self.get_logger().info('Nav2 action server ready!')

        # Timer to start navigation after map is received
        self.startup_timer = self.create_timer(
            5.0, self.check_and_start_navigation,
            callback_group=self.callback_group)

        self.get_logger().info('Random Waypoint Navigator initialized')
        self.get_logger().info(f'Will navigate to {self.num_waypoints} random waypoints')

    def map_callback(self, msg):
        """Process incoming occupancy grid map"""
        self.map_data = np.array(msg.data).reshape(
            (msg.info.height, msg.info.width))
        self.map_info = msg.info

        # Extract free cells (value == 0)
        self.extract_free_cells()

    def pose_callback(self, msg):
        """Update robot pose from AMCL"""
        self.robot_pose = msg.pose.pose

    def extract_free_cells(self):
        """Extract coordinates of free cells from occupancy grid"""
        if self.map_data is None or self.map_info is None:
            return

        self.free_cells = []
        height, width = self.map_data.shape
        resolution = self.map_info.resolution
        origin_x = self.map_info.origin.position.x
        origin_y = self.map_info.origin.position.y

        # Find free cells (value == 0) that are not too close to obstacles
        safety_margin = int(self.min_obstacle_distance / resolution)

        for y in range(safety_margin, height - safety_margin):
            for x in range(safety_margin, width - safety_margin):
                if self.map_data[y, x] == 0:  # Free
                    # Check if surrounded by free cells (safety margin)
                    is_safe = True
                    for dy in range(-safety_margin, safety_margin + 1):
                        for dx in range(-safety_margin, safety_margin + 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < height and 0 <= nx < width:
                                if self.map_data[ny, nx] != 0:  # Not free
                                    is_safe = False
                                    break
                        if not is_safe:
                            break

                    if is_safe:
                        world_x = origin_x + x * resolution
                        world_y = origin_y + y * resolution
                        self.free_cells.append((world_x, world_y))

        self.get_logger().info(f'Found {len(self.free_cells)} safe free cells')

    def generate_random_waypoint(self):
        """Generate a random valid waypoint"""
        if len(self.free_cells) == 0:
            self.get_logger().warn('No free cells available!')
            return None

        # Get current robot position
        robot_x = 0.0
        robot_y = 0.0
        if self.robot_pose:
            robot_x = self.robot_pose.position.x
            robot_y = self.robot_pose.position.y

        # Try to find a valid point within distance constraints
        max_attempts = 100
        for _ in range(max_attempts):
            x, y = random.choice(self.free_cells)

            # Calculate distance from robot
            distance = math.sqrt((x - robot_x)**2 + (y - robot_y)**2)

            if self.min_goal_distance <= distance <= self.max_goal_distance:
                # Generate random yaw
                yaw = random.uniform(-math.pi, math.pi)
                return (x, y, yaw)

        # If no point found within constraints, just pick any free cell
        x, y = random.choice(self.free_cells)
        yaw = random.uniform(-math.pi, math.pi)
        return (x, y, yaw)

    def check_and_start_navigation(self):
        """Check if ready and start navigation"""
        if self.map_data is None:
            self.get_logger().info('Waiting for map...')
            return

        if len(self.free_cells) == 0:
            self.get_logger().info('Waiting for free cells...')
            return

        # Cancel the startup timer
        self.startup_timer.cancel()

        # Start navigation
        self.get_logger().info('Starting random waypoint navigation!')
        self.navigate_to_next_waypoint()

    def navigate_to_next_waypoint(self):
        """Generate and navigate to the next random waypoint"""
        if self.total_goals >= self.num_waypoints:
            self.print_final_stats()
            return

        waypoint = self.generate_random_waypoint()
        if waypoint is None:
            self.get_logger().error('Failed to generate waypoint!')
            return

        x, y, yaw = waypoint
        self.current_goal = (x, y)
        self.total_goals += 1

        self.get_logger().info(
            f'[{self.total_goals}/{self.num_waypoints}] '
            f'Navigating to ({x:.2f}, {y:.2f})'
        )

        # Create goal
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        # Convert yaw to quaternion
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2)

        # Send goal
        self.is_navigating = True
        self.start_time = time.time()

        send_goal_future = self.nav_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """Handle goal acceptance/rejection"""
        self.goal_handle = future.result()

        if not self.goal_handle.accepted:
            self.get_logger().warn('Goal rejected!')
            self.failed_goals += 1
            self.is_navigating = False
            self.schedule_next_navigation()
            return

        self.get_logger().info('Goal accepted!')

        # Get result
        result_future = self.goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        """Handle navigation feedback"""
        feedback = feedback_msg.feedback
        # Could log progress here if needed
        pass

    def result_callback(self, future):
        """Handle navigation result"""
        result = future.result()
        status = result.status
        navigation_time = time.time() - self.start_time

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.successful_goals += 1
            self.navigation_times.append(navigation_time)
            self.get_logger().info(
                f'Goal reached in {navigation_time:.1f}s! '
                f'(Success: {self.successful_goals}/{self.total_goals})'
            )
        elif status == GoalStatus.STATUS_ABORTED:
            self.failed_goals += 1
            self.get_logger().warn(f'Goal aborted after {navigation_time:.1f}s')
        elif status == GoalStatus.STATUS_CANCELED:
            self.timeout_goals += 1
            self.get_logger().warn(f'Goal canceled after {navigation_time:.1f}s')
        else:
            self.failed_goals += 1
            self.get_logger().warn(f'Goal failed with status {status}')

        self.is_navigating = False
        self.schedule_next_navigation()

    def schedule_next_navigation(self):
        """Schedule the next navigation attempt"""
        if self.total_goals >= self.num_waypoints:
            self.print_final_stats()
            return

        # Wait before next goal
        self.create_timer(
            self.wait_between_goals,
            self.navigate_to_next_waypoint,
            callback_group=self.callback_group
        )

    def print_final_stats(self):
        """Print final navigation statistics"""
        avg_time = (sum(self.navigation_times) / len(self.navigation_times)
                   if self.navigation_times else 0)
        success_rate = (self.successful_goals / self.total_goals * 100
                       if self.total_goals > 0 else 0)

        self.get_logger().info(
            f'\n'
            f'{"="*50}\n'
            f' RANDOM WAYPOINT NAVIGATION COMPLETE\n'
            f'{"="*50}\n'
            f' Total Goals: {self.total_goals}\n'
            f' Successful: {self.successful_goals}\n'
            f' Failed: {self.failed_goals}\n'
            f' Timeout: {self.timeout_goals}\n'
            f' Success Rate: {success_rate:.1f}%\n'
            f' Avg Navigation Time: {avg_time:.1f}s\n'
            f'{"="*50}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = RandomWaypointNavigator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Navigation interrupted')
        node.print_final_stats()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
