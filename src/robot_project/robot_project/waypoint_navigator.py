#!/usr/bin/env python3
"""
Waypoint Navigator - Sends random navigation goals to Nav2

This node sends predefined waypoints to the Nav2 stack for autonomous navigation.
Used to test navigation in the office environment.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import math


class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('waypoint_navigator')

        # Nav2 action client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Predefined waypoints for Office World
        # These are safe locations in the corridors
        self.waypoints = [
            {'x': 2.0, 'y': 0.0, 'yaw': 0.0, 'name': 'Start'},
            {'x': 5.0, 'y': 0.0, 'yaw': 0.0, 'name': 'Corridor Middle'},
            {'x': 8.0, 'y': 2.0, 'yaw': 1.57, 'name': 'Room 1'},
            {'x': 8.0, 'y': -2.0, 'yaw': -1.57, 'name': 'Room 2'},
            {'x': 3.0, 'y': 3.0, 'yaw': 0.0, 'name': 'Open Area'},
        ]

        self.current_waypoint_idx = 0
        self.navigation_active = False

        # Timer to start navigation after delay
        self.startup_timer = self.create_timer(5.0, self.start_navigation)

        self.get_logger().info('Waypoint Navigator initialized')
        self.get_logger().info(f'Loaded {len(self.waypoints)} waypoints')

    def start_navigation(self):
        """Start navigation to first waypoint"""
        self.startup_timer.cancel()
        self.send_next_waypoint()

    def send_next_waypoint(self):
        """Send the next waypoint to Nav2"""
        if self.current_waypoint_idx >= len(self.waypoints):
            self.get_logger().info('All waypoints completed!')
            self.current_waypoint_idx = 0  # Loop back

        wp = self.waypoints[self.current_waypoint_idx]
        self.send_goal(wp['x'], wp['y'], wp['yaw'], wp['name'])

    def send_goal(self, x, y, yaw, name=''):
        """Send a navigation goal to Nav2"""
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Nav2 action server not available!')
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        # Convert yaw to quaternion
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(f'Navigating to: {name} ({x:.2f}, {y:.2f})')

        self.navigation_active = True
        future = self.nav_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """Handle goal acceptance/rejection"""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected!')
            self.navigation_active = False
            return

        self.get_logger().info('Goal accepted!')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """Handle navigation result"""
        result = future.result().result
        self.navigation_active = False

        wp = self.waypoints[self.current_waypoint_idx]
        self.get_logger().info(f'Reached: {wp["name"]}')

        # Move to next waypoint
        self.current_waypoint_idx += 1

        # Wait 2 seconds before next waypoint
        self.create_timer(2.0, self.send_next_waypoint_once)

    def send_next_waypoint_once(self):
        """One-shot timer callback"""
        # Cancel this timer after first call
        self.send_next_waypoint()

    def feedback_callback(self, feedback_msg):
        """Handle navigation feedback"""
        feedback = feedback_msg.feedback
        # Could log progress here if needed
        pass


def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavigator()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
