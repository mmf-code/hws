#!/usr/bin/env python3
"""
Stop Robot - Kills explorer, stops robot, returns to center, WAITS

Usage:
    ros2 run robot_project stop_robot --ros-args -p return_to_center:=true
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import subprocess
import math
import time


class StopRobot(Node):
    def __init__(self):
        super().__init__('stop_robot')

        self.declare_parameter('return_to_center', False)
        self.declare_parameter('center_x', 2.0)
        self.declare_parameter('center_y', 0.0)

        self.return_to_center = self.get_parameter('return_to_center').value
        self.center_x = self.get_parameter('center_x').value
        self.center_y = self.get_parameter('center_y').value

        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.current_x = 2.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.odom_received = False
        self.reached_center = False

        self.odom_sub = self.create_subscription(
            Odometry, '/odometry/filtered', self.odom_callback, 10)

        # STEP 1: Kill explorer
        self.get_logger().info('')
        self.get_logger().info('='*50)
        self.get_logger().info('STOPPING EXPLORER...')
        self.kill_explorer()

        # STEP 2: Stop robot
        self.get_logger().info('STOPPING ROBOT...')
        self.stop_robot()
        self.get_logger().info('='*50)

        if self.return_to_center:
            self.get_logger().info(f'Returning to center ({self.center_x}, {self.center_y})...')
            self.state = 'waiting'
            self.wait_count = 0
            self.wait_timer = self.create_timer(0.1, self.wait_for_odom)
        else:
            self.get_logger().info('Robot stopped.')
            self.show_next_step()

    def kill_explorer(self):
        try:
            subprocess.run(['pkill', '-2', '-f', 'autonomous_explorer'],
                          capture_output=True, timeout=3)
            time.sleep(0.3)
            subprocess.run(['pkill', '-9', '-f', 'autonomous_explorer'],
                          capture_output=True, timeout=3)
        except:
            pass

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)
        self.odom_received = True

    def stop_robot(self):
        twist = Twist()
        for _ in range(20):
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.02)

    def wait_for_odom(self):
        self.wait_count += 1
        if self.odom_received:
            self.wait_timer.cancel()
            self.state = 'rotating'
            self.control_timer = self.create_timer(0.1, self.navigate_to_center)
        elif self.wait_count > 30:
            self.wait_timer.cancel()
            self.get_logger().error('No odometry. Exiting.')
            raise SystemExit

    def navigate_to_center(self):
        if self.reached_center:
            return

        dx = self.center_x - self.current_x
        dy = self.center_y - self.current_y
        distance = math.sqrt(dx*dx + dy*dy)
        target_angle = math.atan2(dy, dx)

        angle_diff = target_angle - self.current_yaw
        while angle_diff > math.pi: angle_diff -= 2*math.pi
        while angle_diff < -math.pi: angle_diff += 2*math.pi

        twist = Twist()

        if distance < 0.25:
            self.reached_center = True
            self.stop_robot()
            self.control_timer.cancel()
            self.get_logger().info('')
            self.get_logger().info('='*50)
            self.get_logger().info('REACHED CENTER!')
            self.get_logger().info('='*50)
            self.show_next_step()
            return

        if self.state == 'rotating':
            if abs(angle_diff) > 0.15:
                twist.angular.z = 0.5 if angle_diff > 0 else -0.5
            else:
                self.state = 'driving'
        else:
            twist.linear.x = min(0.25, distance * 0.3)
            twist.angular.z = angle_diff * 0.6
            if abs(angle_diff) > 0.35:
                self.state = 'rotating'

        self.cmd_vel_pub.publish(twist)

    def show_next_step(self):
        self.get_logger().info('')
        self.get_logger().info('Ready for Nav2!')
        self.get_logger().info('')
        self.get_logger().info('Now run in this terminal:')
        self.get_logger().info('  ros2 launch robot_project add_nav2.launch.py')
        self.get_logger().info('')
        self.get_logger().info('Press Ctrl+C to exit, then run the command above.')
        self.get_logger().info('='*50)


def main(args=None):
    rclpy.init(args=args)
    node = StopRobot()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # Final stop
        twist = Twist()
        for _ in range(10):
            node.cmd_vel_pub.publish(twist)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
