#!/usr/bin/env python3
"""
RTAB-Map RGB-D Visual SLAM Launch File

Launches RTAB-Map in visual SLAM mode using RGB-D features.
Requires: Gazebo simulation running with robot spawned.

Usage:
    ros2 launch robot_project slam_rgbd.launch.py
    ros2 launch robot_project slam_rgbd.launch.py localization:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Package directories
    pkg_robot_project = get_package_share_directory('robot_project')

    # Config file
    rtabmap_config = os.path.join(
        pkg_robot_project, 'config', 'rtabmap_rgbd.yaml'
    )

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    localization = LaunchConfiguration('localization', default='false')
    database_path = LaunchConfiguration(
        'database_path',
        default='~/.ros/rtabmap_rgbd.db'
    )

    return LaunchDescription([
        # ========== ARGUMENTS ==========
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'localization', default_value='false',
            description='True for localization mode, False for SLAM mode'
        ),
        DeclareLaunchArgument(
            'database_path', default_value='~/.ros/rtabmap_rgbd.db',
            description='Path to RTAB-Map database'
        ),

        # ========== RTAB-MAP SLAM NODE ==========
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[
                rtabmap_config,
                {
                    'use_sim_time': use_sim_time,
                    'database_path': database_path,
                    # SLAM mode settings
                    'Mem/IncrementalMemory': True,
                    'Mem/InitWMWithAllNodes': False,
                }
            ],
            remappings=[
                # Input topics
                ('rgb/image', '/camera/rgb/image_raw'),
                ('rgb/camera_info', '/camera/rgb/camera_info'),
                ('depth/image', '/camera/depth/image_raw'),
                ('odom', '/odometry/filtered'),  # EKF-fused odometry
                # Output topics
                ('map', '/map'),
                ('cloud_map', '/rtabmap/cloud_map'),
                ('grid_map', '/rtabmap/grid_map'),
            ],
            arguments=['--delete_db_on_start'],
            condition=UnlessCondition(localization)
        ),

        # RTAB-MAP in localization mode (uses existing map)
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[
                rtabmap_config,
                {
                    'use_sim_time': use_sim_time,
                    'database_path': database_path,
                    # Localization mode settings
                    'Mem/IncrementalMemory': False,
                    'Mem/InitWMWithAllNodes': True,
                }
            ],
            remappings=[
                ('rgb/image', '/camera/rgb/image_raw'),
                ('rgb/camera_info', '/camera/rgb/camera_info'),
                ('depth/image', '/camera/depth/image_raw'),
                ('odom', '/odometry/filtered'),
                ('map', '/map'),
                ('cloud_map', '/rtabmap/cloud_map'),
                ('grid_map', '/rtabmap/grid_map'),
            ],
            condition=IfCondition(localization)
        ),

        # ========== RTAB-MAP VISUALIZATION ==========
        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            name='rtabmap_viz',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
            }],
            remappings=[
                ('rgb/image', '/camera/rgb/image_raw'),
                ('rgb/camera_info', '/camera/rgb/camera_info'),
                ('depth/image', '/camera/depth/image_raw'),
                ('odom', '/odometry/filtered'),
            ]
        ),

        # ========== POINT CLOUD TO DEPTH (if needed) ==========
        # Usually not needed as we have depth/image_raw directly
    ])
