#!/usr/bin/env python3
"""
SLAM Mapping Launch File - Phase 1: Create Map

This launch file runs RTAB-Map in SLAM mode to create and save a map.
Use this FIRST to explore and build the map, then save it.

Usage:
    # Start mapping (explore with teleop or autonomous_explorer)
    ros2 launch robot_project slam_mapping.launch.py

    # To save the map when done:
    ros2 service call /rtabmap/save_map std_srvs/srv/Empty

    # Or use map_saver_cli for 2D map:
    ros2 run nav2_map_server map_saver_cli -f ~/maps/office_map

After mapping is complete, use localization_nav.launch.py for navigation.
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
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


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
    rtabmap_config = os.path.join(pkg_robot_project, 'config', 'rtabmap_rgbd.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_explorer = LaunchConfiguration('use_explorer', default='true')

    # Database path for saving map - use ~/maps/ for better organization
    db_path = LaunchConfiguration('db_path', default=os.path.expanduser('~/maps/office_slam_final.db'))

    # Whether to delete existing database (default: false to preserve maps)
    delete_db = LaunchConfiguration('delete_db', default='false')

    # Robot spawn position
    robot_x = LaunchConfiguration('robot_x', default='2.0')
    robot_y = LaunchConfiguration('robot_y', default='0.0')
    robot_z = LaunchConfiguration('robot_z', default='0.1')

    # Process URDF
    robot_description = ParameterValue(
        Command(['xacro ', robot_urdf_file]),
        value_type=str
    )

    return LaunchDescription([
        # ========== ENVIRONMENT ==========
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_explorer', default_value='true',
                              description='Run autonomous explorer for mapping'),
        DeclareLaunchArgument('db_path',
                              default_value=os.path.expanduser('~/maps/office_slam_final.db'),
                              description='Path to save RTAB-Map database'),
        DeclareLaunchArgument('delete_db', default_value='false',
                              description='Delete existing database before starting (true/false)'),
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
        TimerAction(
            period=7.0,
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
                        'scan_height': 60,
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

        # ========== RTAB-MAP SLAM (Mapping Mode) ==========
        # Log which database is being used
        TimerAction(
            period=8.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         f'echo ""; echo "========================================"; '
                         f'echo "SLAM MAPPING MODE"; '
                         f'echo "Database: ~/maps/office_slam_final.db"; '
                         f'echo "Map will be SAVED to this location"; '
                         f'echo "========================================"; echo ""'],
                    output='screen'
                )
            ]
        ),
        TimerAction(
            period=9.0,
            actions=[
                Node(
                    package='rtabmap_slam',
                    executable='rtabmap',
                    name='rtabmap',
                    output='screen',
                    parameters=[
                        rtabmap_config,
                        {
                            'use_sim_time': use_sim_time,
                            'database_path': db_path,
                            # SLAM Mode - Building Map
                            'Mem/IncrementalMemory': 'true',
                            'Mem/InitWMWithAllNodes': 'false',
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
                    ],
                    # NO --delete_db_on_start: continues from existing map if present
                    # To start fresh: delete ~/maps/office_slam_final.db manually
                    arguments=[]
                )
            ]
        ),

        # ========== AUTONOMOUS EXPLORER (for mapping) ==========
        TimerAction(
            period=12.0,
            actions=[
                Node(
                    package='robot_project',
                    executable='autonomous_explorer',
                    name='autonomous_explorer',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'mode': 'free',
                        'linear_speed': 0.5,  # Slower for better mapping
                        'angular_speed': 1.0,
                        'min_distance': 0.8,
                        'critical_distance': 0.4,
                    }],
                    condition=IfCondition(use_explorer)
                )
            ]
        ),

        # ========== RVIZ ==========
        TimerAction(
            period=10.0,
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
