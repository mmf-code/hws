#!/usr/bin/env python3
"""
Nav2 Navigation Launch File

Launches the Nav2 stack for autonomous navigation.
Requires: Map from RTAB-Map or saved map file.

Usage:
    # With RTAB-Map live map
    ros2 launch robot_project navigation.launch.py

    # With saved map
    ros2 launch robot_project navigation.launch.py map:=/path/to/map.yaml
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    GroupAction,
    SetEnvironmentVariable
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, SetRemap
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Package directories
    pkg_robot_project = get_package_share_directory('robot_project')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    # Config files
    nav2_params = os.path.join(pkg_robot_project, 'config', 'nav2_params.yaml')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_yaml_file = LaunchConfiguration('map', default='')
    use_rtabmap_map = LaunchConfiguration('use_rtabmap_map', default='true')
    autostart = LaunchConfiguration('autostart', default='true')

    # Configured parameters (rewrite use_sim_time)
    configured_params = RewrittenYaml(
        source_file=nav2_params,
        param_rewrites={'use_sim_time': use_sim_time},
        convert_types=True
    )

    return LaunchDescription([
        # ========== ENVIRONMENT ==========
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation time'
        ),
        DeclareLaunchArgument(
            'map', default_value='',
            description='Path to map yaml file (empty = use RTAB-Map live map)'
        ),
        DeclareLaunchArgument(
            'use_rtabmap_map', default_value='true',
            description='Use RTAB-Map published map instead of static map'
        ),
        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically start Nav2 lifecycle nodes'
        ),

        # ========== DEPTH TO LASERSCAN ==========
        # Convert depth image to laser scan for Nav2 costmaps
        Node(
            package='depthimage_to_laserscan',
            executable='depthimage_to_laserscan_node',
            name='depthimage_to_laserscan',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'scan_time': 0.033,
                'range_min': 0.1,
                'range_max': 4.0,
                'scan_height': 10,  # Use 10 rows from center
                'output_frame_id': 'camera_link',
            }],
            remappings=[
                ('depth', '/camera/rgbd_camera/depth/image_raw'),
                ('depth_camera_info', '/camera/rgbd_camera/depth/camera_info'),
                ('scan', '/scan'),
            ]
        ),

        # ========== MAP SERVER (for saved maps) ==========
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'yaml_filename': map_yaml_file,
            }],
            condition=UnlessCondition(use_rtabmap_map)
        ),

        # ========== NAV2 LIFECYCLE MANAGER ==========
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'bond_timeout': 15.0,  # Increased for simulation startup
                'attempt_respawn_reconnection': True,
                'bond_respawn_max_duration': 15.0,
                'node_names': [
                    'controller_server',
                    'smoother_server',
                    'planner_server',
                    'behavior_server',
                    'bt_navigator',
                    'waypoint_follower',
                    'velocity_smoother',
                ]
            }]
        ),

        # ========== NAV2 CONTROLLER SERVER ==========
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[configured_params],
            remappings=[
                ('cmd_vel', '/cmd_vel'),
                ('odom', '/odometry/filtered'),
            ]
        ),

        # ========== NAV2 SMOOTHER SERVER ==========
        Node(
            package='nav2_smoother',
            executable='smoother_server',
            name='smoother_server',
            output='screen',
            parameters=[configured_params]
        ),

        # ========== NAV2 PLANNER SERVER ==========
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[configured_params]
        ),

        # ========== NAV2 BEHAVIOR SERVER ==========
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[configured_params]
        ),

        # ========== NAV2 BT NAVIGATOR ==========
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[configured_params],
            remappings=[
                ('odom', '/odometry/filtered'),
            ]
        ),

        # ========== NAV2 WAYPOINT FOLLOWER ==========
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[configured_params]
        ),

        # ========== NAV2 VELOCITY SMOOTHER ==========
        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[configured_params],
            remappings=[
                ('cmd_vel', '/cmd_vel'),
                ('cmd_vel_smoothed', '/cmd_vel_smoothed'),
                ('odom', '/odometry/filtered'),
            ]
        ),
    ])
