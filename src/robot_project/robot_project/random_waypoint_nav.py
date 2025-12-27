#!/usr/bin/env python3
"""
Office Coverage Navigator - Autonomous navigation with strategic random goals

Uses Nav2 to navigate to randomly generated waypoints that cover the entire office.
Implements Requirement 7: "Use 2D projection of the computed 3D map for navigation.
Assign random points in the environment to move the robot autonomously."

Features:
- Coverage-based exploration: Divides map into grid regions
- Edge preference: Can navigate close to walls (with safety margin)
- Strategic waypoint selection: Ensures full office coverage

Subscribes to:
    /map - OccupancyGrid from RTAB-Map
    /odometry/filtered - Robot pose from EKF

Action Client:
    /navigate_to_pose - Nav2 NavigateToPose action

Usage:
    ros2 run robot_project random_waypoint_nav
    ros2 run robot_project random_waypoint_nav --ros-args -p mode:=coverage
    ros2 run robot_project random_waypoint_nav --ros-args -p mode:=edge
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid, Odometry
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus
import numpy as np
import random
import math
import time


class OfficeCoverageNavigator(Node):
    def __init__(self):
        super().__init__('office_coverage_navigator')

        # Parameters
        self.declare_parameter('num_waypoints', 15)
        self.declare_parameter('min_obstacle_distance', 0.25)  # meters - closer to walls
        self.declare_parameter('edge_distance', 0.35)  # distance for edge cells
        self.declare_parameter('goal_timeout', 120.0)  # seconds
        self.declare_parameter('min_goal_distance', 0.5)  # min distance from robot
        self.declare_parameter('max_goal_distance', 15.0)  # max - cover whole office
        self.declare_parameter('wait_between_goals', 1.5)  # seconds
        self.declare_parameter('mode', 'coverage')  # 'random', 'coverage', 'edge'
        self.declare_parameter('grid_divisions', 4)  # divide map into NxN regions

        self.num_waypoints = self.get_parameter('num_waypoints').value
        self.min_obstacle_distance = self.get_parameter('min_obstacle_distance').value
        self.edge_distance = self.get_parameter('edge_distance').value
        self.goal_timeout = self.get_parameter('goal_timeout').value
        self.min_goal_distance = self.get_parameter('min_goal_distance').value
        self.max_goal_distance = self.get_parameter('max_goal_distance').value
        self.wait_between_goals = self.get_parameter('wait_between_goals').value
        self.mode = self.get_parameter('mode').value
        self.grid_divisions = self.get_parameter('grid_divisions').value

        # Callback groups for concurrency
        self.callback_group = ReentrantCallbackGroup()

        # Map data
        self.map_data = None
        self.map_info = None
        self.free_cells = []
        self.edge_cells = []  # Cells near walls
        self.region_cells = {}  # Cells grouped by region

        # Robot pose (from odometry)
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0

        # Navigation state
        self.is_navigating = False
        self.current_goal = None
        self.goal_handle = None
        self.visited_regions = set()

        # Metrics
        self.total_goals = 0
        self.successful_goals = 0
        self.failed_goals = 0
        self.timeout_goals = 0
        self.start_time = None
        self.navigation_times = []
        self.visited_points = []

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

        # Use odometry instead of AMCL (RTAB-Map doesn't use AMCL)
        self.odom_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.odom_callback, 10,
            callback_group=self.callback_group)

        # Nav2 action client
        self.nav_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=self.callback_group)

        # Wait for Nav2 to be ready
        self.get_logger().info('Waiting for Nav2 action server...')
        if not self.nav_client.wait_for_server(timeout_sec=60.0):
            self.get_logger().error('Nav2 action server not available!')
            return

        self.get_logger().info('Nav2 action server ready!')

        # Timer to start navigation after map is received
        self.startup_timer = self.create_timer(
            5.0, self.check_and_start_navigation,
            callback_group=self.callback_group)

        self.get_logger().info('='*50)
        self.get_logger().info('Office Coverage Navigator initialized')
        self.get_logger().info(f'Mode: {self.mode}')
        self.get_logger().info(f'Waypoints: {self.num_waypoints}')
        self.get_logger().info(f'Min obstacle distance: {self.min_obstacle_distance}m')
        self.get_logger().info('='*50)

    def map_callback(self, msg):
        """Process incoming occupancy grid map"""
        self.map_data = np.array(msg.data).reshape(
            (msg.info.height, msg.info.width))
        self.map_info = msg.info

        # Extract cells based on mode
        self.extract_navigable_cells()

    def odom_callback(self, msg):
        """Update robot pose from odometry"""
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.robot_yaw = math.atan2(siny_cosp, cosy_cosp)

    def extract_navigable_cells(self):
        """Extract navigable cells from occupancy grid with region classification"""
        if self.map_data is None or self.map_info is None:
            return

        self.free_cells = []
        self.edge_cells = []
        self.region_cells = {}

        height, width = self.map_data.shape
        resolution = self.map_info.resolution
        origin_x = self.map_info.origin.position.x
        origin_y = self.map_info.origin.position.y

        # Safety margins in cells
        safety_margin = max(1, int(self.min_obstacle_distance / resolution))
        edge_margin = max(1, int(self.edge_distance / resolution))

        # Calculate region boundaries
        region_height = height // self.grid_divisions
        region_width = width // self.grid_divisions

        for y in range(safety_margin, height - safety_margin):
            for x in range(safety_margin, width - safety_margin):
                if self.map_data[y, x] == 0:  # Free cell
                    # Check minimum safety (must have some clearance)
                    is_safe = self._check_safety(x, y, safety_margin, height, width)

                    if is_safe:
                        world_x = origin_x + x * resolution
                        world_y = origin_y + y * resolution

                        self.free_cells.append((world_x, world_y))

                        # Check if this is an edge cell (near obstacle but safe)
                        is_edge = self._check_edge(x, y, edge_margin, safety_margin, height, width)
                        if is_edge:
                            self.edge_cells.append((world_x, world_y))

                        # Assign to region
                        region_x = min(x // region_width, self.grid_divisions - 1)
                        region_y = min(y // region_height, self.grid_divisions - 1)
                        region_id = (region_x, region_y)

                        if region_id not in self.region_cells:
                            self.region_cells[region_id] = []
                        self.region_cells[region_id].append((world_x, world_y))

        self.get_logger().info(f'Map analysis complete:')
        self.get_logger().info(f'  - Total free cells: {len(self.free_cells)}')
        self.get_logger().info(f'  - Edge cells (near walls): {len(self.edge_cells)}')
        self.get_logger().info(f'  - Regions with cells: {len(self.region_cells)}')

        # Log region distribution
        for region_id, cells in self.region_cells.items():
            self.get_logger().info(f'  - Region {region_id}: {len(cells)} cells')

    def _check_safety(self, x, y, margin, height, width):
        """Check if cell has minimum safety clearance"""
        for dy in range(-margin, margin + 1):
            for dx in range(-margin, margin + 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if self.map_data[ny, nx] != 0:  # Obstacle or unknown
                        return False
        return True

    def _check_edge(self, x, y, edge_margin, safety_margin, height, width):
        """Check if cell is near an obstacle (edge cell)"""
        # Cell is edge if it has obstacle within edge_margin but outside safety_margin
        for dy in range(-edge_margin, edge_margin + 1):
            for dx in range(-edge_margin, edge_margin + 1):
                # Skip cells within safety margin
                if abs(dy) <= safety_margin and abs(dx) <= safety_margin:
                    continue

                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if self.map_data[ny, nx] > 50:  # Obstacle
                        return True
        return False

    def generate_waypoint(self):
        """Generate waypoint based on selected mode"""
        if self.mode == 'coverage':
            return self._generate_coverage_waypoint()
        elif self.mode == 'edge':
            return self._generate_edge_waypoint()
        else:  # random
            return self._generate_random_waypoint()

    def _generate_coverage_waypoint(self):
        """Generate waypoint ensuring coverage of all regions"""
        # First, try unvisited regions
        unvisited = [r for r in self.region_cells.keys() if r not in self.visited_regions]

        if unvisited:
            # Pick random unvisited region
            region = random.choice(unvisited)
            cells = self.region_cells[region]
            self.visited_regions.add(region)
            self.get_logger().info(f'Targeting unvisited region {region}')
        else:
            # All regions visited, reset and pick any
            self.visited_regions.clear()
            region = random.choice(list(self.region_cells.keys()))
            cells = self.region_cells[region]
            self.get_logger().info(f'All regions visited, revisiting {region}')

        # Select point from region
        return self._select_from_cells(cells)

    def _generate_edge_waypoint(self):
        """Generate waypoint near walls/edges"""
        if len(self.edge_cells) > 0:
            cells = self.edge_cells
            self.get_logger().info('Targeting edge cell (near wall)')
        else:
            cells = self.free_cells
            self.get_logger().info('No edge cells, using free cell')

        return self._select_from_cells(cells)

    def _generate_random_waypoint(self):
        """Generate completely random waypoint"""
        return self._select_from_cells(self.free_cells)

    def _select_from_cells(self, cells):
        """Select a valid cell from given list"""
        if len(cells) == 0:
            self.get_logger().warn('No cells available!')
            return None

        # Try to find point within distance constraints
        max_attempts = 100
        for _ in range(max_attempts):
            x, y = random.choice(cells)

            # Check distance from robot
            distance = math.sqrt((x - self.robot_x)**2 + (y - self.robot_y)**2)

            # Check not too close to already visited points
            too_close = False
            for vx, vy in self.visited_points[-5:]:  # Check last 5 visited
                if math.sqrt((x - vx)**2 + (y - vy)**2) < 1.0:
                    too_close = True
                    break

            if self.min_goal_distance <= distance <= self.max_goal_distance and not too_close:
                yaw = random.uniform(-math.pi, math.pi)
                return (x, y, yaw)

        # Fallback: just pick any cell
        x, y = random.choice(cells)
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
        self.get_logger().info('='*50)
        self.get_logger().info('Starting office coverage navigation!')
        self.get_logger().info('='*50)
        self.navigate_to_next_waypoint()

    def navigate_to_next_waypoint(self):
        """Generate and navigate to the next waypoint"""
        if self.total_goals >= self.num_waypoints:
            self.print_final_stats()
            return

        waypoint = self.generate_waypoint()
        if waypoint is None:
            self.get_logger().error('Failed to generate waypoint!')
            return

        x, y, yaw = waypoint
        self.current_goal = (x, y)
        self.total_goals += 1

        self.get_logger().info(
            f'[{self.total_goals}/{self.num_waypoints}] '
            f'Navigating to ({x:.2f}, {y:.2f}) '
            f'[dist: {math.sqrt((x-self.robot_x)**2 + (y-self.robot_y)**2):.1f}m]'
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
        pass

    def result_callback(self, future):
        """Handle navigation result"""
        result = future.result()
        status = result.status
        navigation_time = time.time() - self.start_time

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.successful_goals += 1
            self.navigation_times.append(navigation_time)
            self.visited_points.append(self.current_goal)
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

        # Calculate coverage
        regions_covered = len(self.visited_regions)
        total_regions = len(self.region_cells)
        coverage = (regions_covered / total_regions * 100) if total_regions > 0 else 0

        self.get_logger().info(
            f'\n'
            f'{"="*60}\n'
            f' OFFICE COVERAGE NAVIGATION COMPLETE\n'
            f'{"="*60}\n'
            f' Mode: {self.mode}\n'
            f' Total Goals: {self.total_goals}\n'
            f' Successful: {self.successful_goals}\n'
            f' Failed: {self.failed_goals}\n'
            f' Timeout: {self.timeout_goals}\n'
            f' Success Rate: {success_rate:.1f}%\n'
            f' Avg Navigation Time: {avg_time:.1f}s\n'
            f' Regions Covered: {regions_covered}/{total_regions} ({coverage:.0f}%)\n'
            f'{"="*60}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = OfficeCoverageNavigator()

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
