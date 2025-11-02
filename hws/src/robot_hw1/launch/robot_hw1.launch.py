#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_hw1',
            executable='cmd_vel_publisher',
            name='cmd_vel_publisher',
            output='screen',
        ),
        Node(
            package='robot_hw1',
            executable='noisy_odom_publisher',
            name='noisy_odom_publisher',
            output='screen',
        ),
    ])

