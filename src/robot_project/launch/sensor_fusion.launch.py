#!/usr/bin/env python3
"""
Sensor Fusion Launch File
Starts robot_localization EKF to fuse IMU and wheel odometry
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Get package directory
    pkg_robot_project = get_package_share_directory('robot_project')

    # Config file path
    ekf_config = os.path.join(pkg_robot_project, 'config', 'robot_localization.yaml')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([
        # Declare arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation time from Gazebo'
        ),

        # EKF Node - Fuses IMU + Wheel Odometry
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                ekf_config,
                {'use_sim_time': use_sim_time}
            ],
            remappings=[
                ('odometry/filtered', '/odometry/filtered')
            ]
        ),
    ])
