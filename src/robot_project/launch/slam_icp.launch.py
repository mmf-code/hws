#!/usr/bin/env python3
"""
RTAB-Map ICP-based SLAM Launch File

Launches RTAB-Map using ICP (Iterative Closest Point) registration.
This configuration uses point cloud matching instead of visual features.
Used for comparison with visual SLAM approach.

Usage:
    ros2 launch robot_project slam_icp.launch.py
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
        pkg_robot_project, 'config', 'rtabmap_icp.yaml'
    )

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    localization = LaunchConfiguration('localization', default='false')
    database_path = LaunchConfiguration(
        'database_path',
        default='~/.ros/rtabmap_icp.db'
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
            'database_path', default_value='~/.ros/rtabmap_icp.db',
            description='Path to RTAB-Map database'
        ),

        # ========== POINT CLOUD ASSEMBLER ==========
        # Convert depth image to point cloud if not using depth/points directly
        Node(
            package='rtabmap_util',
            executable='point_cloud_xyz',
            name='point_cloud_xyz',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'decimation': 4,
                'voxel_size': 0.05,
                'approx_sync': True,
                'approx_sync_max_interval': 0.05,
            }],
            remappings=[
                ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                ('depth/camera_info', '/camera/rgbd_camera/depth/camera_info'),
                ('cloud', '/camera/rgbd_camera/points_assembled'),
            ]
        ),

        # ========== RTAB-MAP SLAM NODE (ICP Mode) ==========
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
                    # ICP registration
                    'Reg/Strategy': '1',  # ICP
                    'Reg/Force3DoF': 'true',
                    # SLAM mode settings
                    'Mem/IncrementalMemory': 'true',
                    'Mem/InitWMWithAllNodes': 'false',
                }
            ],
            remappings=[
                # Input topics
                ('rgb/image', '/camera/rgbd_camera/image_raw'),
                ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                ('scan_cloud', '/camera/rgbd_camera/points'),  # Direct point cloud
                ('odom', '/odometry/filtered'),  # EKF-fused odometry
                # Output topics
                ('map', '/map'),
                ('cloud_map', '/rtabmap/cloud_map'),
                ('grid_map', '/rtabmap/grid_map'),
            ],
            arguments=['--delete_db_on_start'],
            condition=UnlessCondition(localization)
        ),

        # RTAB-MAP in localization mode
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
                    'Reg/Strategy': '1',
                    'Reg/Force3DoF': 'true',
                    'Mem/IncrementalMemory': 'false',
                    'Mem/InitWMWithAllNodes': 'true',
                }
            ],
            remappings=[
                ('rgb/image', '/camera/rgbd_camera/image_raw'),
                ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                ('scan_cloud', '/camera/rgbd_camera/points'),
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
                ('rgb/image', '/camera/rgbd_camera/image_raw'),
                ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                ('scan_cloud', '/camera/rgbd_camera/points'),
                ('odom', '/odometry/filtered'),
            ]
        ),
    ])
