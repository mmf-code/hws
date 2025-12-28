#!/usr/bin/env python3
"""
Localization + Navigation Launch File

Uses existing RTAB-Map database for localization and Nav2 navigation.
- RTAB-Map in LOCALIZATION mode (doesn't build new map)
- Full Nav2 stack for autonomous navigation
- Lightweight configuration (won't crash PC)
- Includes random waypoint navigator for Team 14 Requirement 7

Usage:
    # Terminal 1: Start the navigation system
    ros2 launch robot_project localization_navigation.launch.py

    # Terminal 2: Start random waypoint navigator (after map loads ~10-20s)
    ros2 run robot_project random_waypoint_nav

    # Or with parameters:
    ros2 run robot_project random_waypoint_nav --ros-args -p mode:=coverage -p num_waypoints:=15

Expected output:
    - RViz showing robot, 2D map, and navigation plan
    - Robot localizes in the map
    - Nav2 lifecycle nodes transition to active
    - Random waypoint navigator sends goals to Nav2
    - Robot autonomously navigates to random points

Team 14 Requirement 7:
    "Use 2D projection of the computed 3D map for navigation.
     Assign random points in the environment to move the robot autonomously."

This launch file provides:
    - 2D map projection: /map topic from RTAB-Map
    - Random waypoint generation: random_waypoint_nav.py node
    - Autonomous navigation: Nav2 stack (controller, planner, BT navigator)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    ExecuteProcess,
    SetEnvironmentVariable,
    GroupAction
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Package directories
    pkg_robot_hw1 = get_package_share_directory('robot_hw1')
    pkg_robot_project = get_package_share_directory('robot_project')
    pkg_cpr_office = get_package_share_directory('cpr_office_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # File paths
    robot_urdf_file = os.path.join(pkg_robot_hw1, 'urdf', 'p3dx_hw2.urdf.xacro')
    office_urdf_file = os.path.join(pkg_cpr_office, 'urdf', 'office_geometry.urdf.xacro')
    world_file = os.path.join(pkg_robot_hw1, 'worlds', 'empty_office.world')
    ekf_config = os.path.join(pkg_robot_project, 'config', 'robot_localization.yaml')
    rtabmap_rgbd_config = os.path.join(pkg_robot_project, 'config', 'rtabmap_rgbd.yaml')
    nav2_params = os.path.join(pkg_robot_project, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_nav2 = LaunchConfiguration('use_nav2', default='true')
    autostart = LaunchConfiguration('autostart', default='true')

    # Robot spawn position
    robot_x = LaunchConfiguration('robot_x', default='2.0')
    robot_y = LaunchConfiguration('robot_y', default='0.0')
    robot_z = LaunchConfiguration('robot_z', default='0.1')

    # Process URDF
    robot_description = ParameterValue(
        Command(['xacro ', robot_urdf_file]),
        value_type=str
    )

    # Rewritten Nav2 params
    configured_params = RewrittenYaml(
        source_file=nav2_params,
        param_rewrites={'use_sim_time': use_sim_time},
        convert_types=True
    )

    return LaunchDescription([
        # ========== ENVIRONMENT ==========
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true',
                              description='Enable RViz visualization'),
        DeclareLaunchArgument('use_nav2', default_value='true',
                              description='Enable Nav2 navigation stack'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('robot_x', default_value='2.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),
        DeclareLaunchArgument('robot_z', default_value='0.1'),

        # ========== GAZEBO ==========
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={
                'world': world_file,
                'verbose': 'false'
            }.items()
        ),

        # ========== ROBOT STATE PUBLISHER ==========
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'robot_description': robot_description
            }]
        ),

        # ========== SPAWN OFFICE ==========
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'bash', '-c',
                        f'xacro {office_urdf_file} | ros2 run gazebo_ros spawn_entity.py '
                        f'-entity office_world -stdin -x 0.0 -y 0.0 -z 0.0'
                    ],
                    output='screen'
                )
            ]
        ),

        # ========== SPAWN ROBOT ==========
        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    name='spawn_robot',
                    output='screen',
                    arguments=[
                        '-entity', 'pioneer3dx',
                        '-topic', 'robot_description',
                        '-x', robot_x,
                        '-y', robot_y,
                        '-z', robot_z
                    ]
                )
            ]
        ),

        # ========== EKF SENSOR FUSION ==========
        TimerAction(
            period=6.0,
            actions=[
                Node(
                    package='robot_localization',
                    executable='ekf_node',
                    name='ekf_filter_node',
                    output='screen',
                    parameters=[
                        ekf_config,
                        {'use_sim_time': use_sim_time}
                    ]
                )
            ]
        ),

        # ========== DEPTH TO LASERSCAN ==========
        # Converts depth image to LaserScan for Nav2 costmaps
        TimerAction(
            period=8.0,
            actions=[
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
                        'scan_height': 10,
                        'output_frame_id': 'camera_link',
                    }],
                    remappings=[
                        ('depth', '/camera/rgbd_camera/depth/image_raw'),
                        ('depth_camera_info', '/camera/rgbd_camera/depth/camera_info'),
                        ('scan', '/scan'),
                    ]
                )
            ]
        ),

        # ========== RTAB-MAP LOCALIZATION ==========
        # Load existing map for localization (doesn't build new map)
        TimerAction(
            period=10.0,
            actions=[
                Node(
                    package='rtabmap_slam',
                    executable='rtabmap',
                    name='rtabmap',
                    output='screen',
                    parameters=[
                        rtabmap_rgbd_config,
                        {
                            'use_sim_time': use_sim_time,
                            'database_path': '~/.ros/rtabmap.db',
                            'Mem/IncrementalMemory': 'false',  # LOCALIZATION mode - don't build new map
                            'Mem/InitWMWithAllNodes': 'true',  # Load entire map at startup
                            'Grid/FromDepth': 'true',
                        }
                    ],
                    remappings=[
                        ('rgb/image', '/camera/rgbd_camera/image_raw'),
                        ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                        ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                        ('odom', '/odometry/filtered'),
                        ('map', '/map'),
                        ('cloud_map', '/rtabmap/cloud_map'),
                        ('grid_map', '/rtabmap/grid_map'),
                    ]
                )
            ]
        ),

        # ========== NAV2 STACK ==========
        TimerAction(
            period=15.0,
            actions=[
                # Lifecycle Manager
                Node(
                    package='nav2_lifecycle_manager',
                    executable='lifecycle_manager',
                    name='lifecycle_manager_navigation',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'autostart': autostart,
                        'node_names': [
                            'controller_server',
                            'planner_server',
                            'behavior_server',
                            'bt_navigator',
                        ]
                    }],
                    condition=IfCondition(use_nav2)
                ),
                # Controller Server
                Node(
                    package='nav2_controller',
                    executable='controller_server',
                    name='controller_server',
                    output='screen',
                    parameters=[configured_params],
                    remappings=[
                        ('cmd_vel', '/cmd_vel'),
                        ('odom', '/odometry/filtered'),
                    ],
                    condition=IfCondition(use_nav2)
                ),
                # Planner Server
                Node(
                    package='nav2_planner',
                    executable='planner_server',
                    name='planner_server',
                    output='screen',
                    parameters=[configured_params],
                    condition=IfCondition(use_nav2)
                ),
                # Behavior Server
                Node(
                    package='nav2_behaviors',
                    executable='behavior_server',
                    name='behavior_server',
                    output='screen',
                    parameters=[configured_params],
                    condition=IfCondition(use_nav2)
                ),
                # BT Navigator
                Node(
                    package='nav2_bt_navigator',
                    executable='bt_navigator',
                    name='bt_navigator',
                    output='screen',
                    parameters=[configured_params],
                    remappings=[
                        ('odom', '/odometry/filtered'),
                    ],
                    condition=IfCondition(use_nav2)
                ),
            ]
        ),

        # ========== RVIZ ==========
        TimerAction(
            period=16.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'bash', '-c',
                        'export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr ":" "\\n" | grep -v snap | tr "\\n" ":"); '
                        'unset GTK_PATH; '
                        f'rviz2 -d {rviz_config} --ros-args -p use_sim_time:=true'
                    ],
                    output='screen',
                    condition=IfCondition(use_rviz)
                )
            ]
        ),
    ])
