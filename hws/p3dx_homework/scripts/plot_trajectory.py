#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class TrajectoryPlotter(Node):
    def __init__(self):
        super().__init__('trajectory_plotter')
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.x_data = []
        self.y_data = []

        # Setup plot
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_xlabel('X Position (m)')
        self.ax.set_ylabel('Y Position (m)')
        self.ax.set_title('Robot Trajectory (X-Y Odometry)')
        self.ax.grid(True)
        self.ax.axis('equal')

        self.line, = self.ax.plot([], [], 'r-', linewidth=2, label='Trajectory')
        self.ax.legend()

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        self.x_data.append(x)
        self.y_data.append(y)

        # Keep last 1000 points
        if len(self.x_data) > 1000:
            self.x_data.pop(0)
            self.y_data.pop(0)

    def update_plot(self, frame):
        if len(self.x_data) > 0:
            self.line.set_data(self.x_data, self.y_data)
            self.ax.relim()
            self.ax.autoscale_view()
        return self.line,


def main():
    rclpy.init()
    node = TrajectoryPlotter()

    # Animation
    ani = FuncAnimation(node.fig, node.update_plot, interval=100, blit=True)

    plt.show(block=False)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()
    plt.close()


if __name__ == '__main__':
    main()
