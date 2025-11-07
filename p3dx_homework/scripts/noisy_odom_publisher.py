#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import numpy as np
import copy

class NoisyOdomPublisher(Node):
    def __init__(self):
        super().__init__('noisy_odom_publisher')

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom_clean',
            self.odom_callback,
            10
        )

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        self.position_noise = 0.15
        self.orientation_noise = 0.05
        self.velocity_noise = 0.05

        self.drift_x = 0.0
        self.drift_y = 0.0
        self.drift_theta = 0.0
        self.drift_rate = 0.005

        self.get_logger().info('Noisy odometry publisher started')

    def odom_callback(self, msg):
        noisy_msg = copy.deepcopy(msg)

        noise_x = np.random.normal(0, self.position_noise)
        noise_y = np.random.normal(0, self.position_noise)

        self.drift_x += np.random.normal(0, self.drift_rate)
        self.drift_y += np.random.normal(0, self.drift_rate)
        self.drift_theta += np.random.normal(0, self.drift_rate * 0.1)

        noisy_msg.pose.pose.position.x += noise_x + self.drift_x
        noisy_msg.pose.pose.position.y += noise_y + self.drift_y

        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)

        yaw_noisy = yaw + np.random.normal(0, self.orientation_noise) + self.drift_theta

        noisy_msg.pose.pose.orientation.x = 0.0
        noisy_msg.pose.pose.orientation.y = 0.0
        noisy_msg.pose.pose.orientation.z = np.sin(yaw_noisy / 2.0)
        noisy_msg.pose.pose.orientation.w = np.cos(yaw_noisy / 2.0)

        noisy_msg.twist.twist.linear.x += np.random.normal(0, self.velocity_noise)
        noisy_msg.twist.twist.angular.z += np.random.normal(0, self.orientation_noise)

        time_factor = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        noisy_msg.pose.covariance[0] = 0.0001 + time_factor * 0.0001
        noisy_msg.pose.covariance[7] = 0.0001 + time_factor * 0.0001
        noisy_msg.pose.covariance[35] = 0.001 + time_factor * 0.001

        self.odom_pub.publish(noisy_msg)

def main(args=None):
    rclpy.init(args=args)
    node = NoisyOdomPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
