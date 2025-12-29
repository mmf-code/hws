#!/usr/bin/env python3
"""
SLAM Hybrid Launch - Fresh SLAM with PyGame manual/auto control

Features:
- Fresh SLAM (deletes existing database)
- Hybrid controller: AUTO/MANUAL/TURBO modes
- PyGame window for visual feedback and keyboard control
- WASD + speed levels + special rotations

Usage:
    # Default (AUTO mode)
    ros2 launch robot_project slam_hybrid.launch.py

    # Start in MANUAL mode
    ros2 launch robot_project slam_hybrid.launch.py start_mode:=manual

    # Without RViz
    ros2 launch robot_project slam_hybrid.launch.py use_rviz:=false

    # Custom speed
    ros2 launch robot_project slam_hybrid.launch.py base_speed:=1.2
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
    LogInfo
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
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'hybrid_slam.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    start_mode = LaunchConfiguration('start_mode', default='auto')
    base_speed = LaunchConfiguration('base_speed', default='0.9')
    robot_x = LaunchConfiguration('robot_x', default='2.0')
    robot_y = LaunchConfiguration('robot_y', default='0.0')

    # Robot URDF
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
        DeclareLaunchArgument('start_mode', default_value='manual',
                              description='Start mode: auto, manual, or turbo'),
        DeclareLaunchArgument('base_speed', default_value='0.9',
                              description='Base linear speed (m/s)'),
        DeclareLaunchArgument('robot_x', default_value='2.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),

        # ========== BANNER ==========
        LogInfo(msg='\n' + '='*70),
        LogInfo(msg='    SLAM HYBRID CONTROLLER'),
        LogInfo(msg='    Fresh SLAM + PyGame Manual/Auto Control'),
        LogInfo(msg='    Press SPACE to toggle AUTO/MANUAL mode'),
        LogInfo(msg='='*70 + '\n'),

        # ========== DELETE OLD DATABASE ==========
        ExecuteProcess(
            cmd=['rm', '-f', os.path.expanduser('~/.ros/rtabmap.db')],
            output='log'
        ),

        # ========== GAZEBO ==========
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={'world': world_file, 'verbose': 'false'}.items()
        ),

        # ========== ROBOT STATE PUBLISHER ==========
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='log',
            parameters=[{
                'use_sim_time': use_sim_time,
                'robot_description': robot_description
            }]
        ),

        # ========== SPAWN OFFICE (T=2s) ==========
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         f'xacro {office_urdf_file} | ros2 run gazebo_ros spawn_entity.py '
                         f'-entity office_world -stdin -x 0.0 -y 0.0 -z 0.0'],
                    output='log'
                )
            ]
        ),

        # ========== SPAWN ROBOT (T=4s) ==========
        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    name='spawn_robot',
                    output='log',
                    arguments=[
                        '-entity', 'pioneer3dx',
                        '-topic', 'robot_description',
                        '-x', robot_x,
                        '-y', robot_y,
                        '-z', '0.1'
                    ]
                )
            ]
        ),

        # ========== EKF SENSOR FUSION (T=6s) ==========
        TimerAction(
            period=6.0,
            actions=[
                Node(
                    package='robot_localization',
                    executable='ekf_node',
                    name='ekf_filter_node',
                    output='log',
                    parameters=[
                        ekf_config,
                        {'use_sim_time': use_sim_time}
                    ]
                )
            ]
        ),

        # ========== DEPTH TO LASERSCAN (T=7s) ==========
        TimerAction(
            period=7.0,
            actions=[
                Node(
                    package='depthimage_to_laserscan',
                    executable='depthimage_to_laserscan_node',
                    name='depthimage_to_laserscan',
                    output='log',
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

        # ========== RTAB-MAP SLAM (T=9s) - FRESH START ==========
        TimerAction(
            period=9.0,
            actions=[
                LogInfo(msg='[RTAB-Map] Starting fresh SLAM...'),
                Node(
                    package='rtabmap_slam',
                    executable='rtabmap',
                    name='rtabmap',
                    output='log',
                    arguments=['--delete_db_on_start', '--ros-args', '--log-level', 'warn'],
                    parameters=[{
                        'use_sim_time': True,
                        'frame_id': 'base_link',
                        'odom_frame_id': 'odom',
                        'map_frame_id': 'map',

                        # Subscriptions
                        'subscribe_depth': True,
                        'subscribe_rgb': True,
                        'subscribe_scan': False,
                        'approx_sync': True,
                        'approx_sync_max_interval': 0.1,
                        'queue_size': 10,

                        # SLAM Mode
                        'Mem/IncrementalMemory': 'true',
                        'Mem/InitWMWithAllNodes': 'false',

                        # Features - optimized for speed
                        'Rtabmap/DetectionRate': '2.0',
                        'Kp/DetectorStrategy': '6',
                        'Kp/MaxFeatures': '500',
                        'Kp/MaxDepth': '4.0',

                        # Loop Closure - STRICT to prevent false matches
                        'Vis/MinInliers': '20',           # Min visual inliers (default 20)
                        'RGBD/OptimizeMaxError': '1.0',   # Reject bad loop closures
                        'Rtabmap/LoopThr': '0.11',        # Loop closure threshold (higher = stricter)
                        'Mem/RehearsalSimilarity': '0.6', # Memory rehearsal threshold
                        'RGBD/LoopClosureReextractFeatures': 'true',  # Re-extract for verification

                        # Grid for Nav2
                        'RGBD/CreateOccupancyGrid': 'true',
                        'Grid/FromDepth': 'true',
                        'Grid/CellSize': '0.05',
                        'Grid/RangeMax': '4.0',
                        'Grid/RangeMin': '0.2',
                        'Grid/MaxObstacleHeight': '2.0',

                        # Graph optimization
                        'Optimizer/Strategy': '1',
                        'Optimizer/Slam2D': 'true',
                        'RGBD/LinearUpdate': '0.1',
                        'RGBD/AngularUpdate': '0.1',

                        # TF publishing
                        'publish_tf': True,
                        'wait_for_transform': 0.5,
                        'tf_delay': 0.05,
                    }],
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

        # ========== HYBRID CONTROLLER (T=18s) ==========
        TimerAction(
            period=18.0,
            actions=[
                LogInfo(msg='[Controller] Starting Hybrid Controller with PyGame...'),
                LogInfo(msg='[Controller] Focus PyGame window for keyboard control!'),
                Node(
                    package='robot_project',
                    executable='hybrid_slam_controller',
                    name='hybrid_slam_controller',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'start_mode': start_mode,
                        'base_linear_speed': base_speed,
                        'base_angular_speed': 1.8,
                        'min_distance': 0.8,
                        'critical_distance': 0.4,
                        'start_delay': 5.0,
                    }]
                )
            ]
        ),

        # ========== MAP METRICS (T=20s) ==========
        TimerAction(
            period=20.0,
            actions=[
                Node(
                    package='robot_project',
                    executable='map_metrics',
                    name='map_metrics',
                    output='log',
                    parameters=[{'use_sim_time': use_sim_time}]
                )
            ]
        ),

        # ========== RVIZ (T=15s) ==========
        TimerAction(
            period=15.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'bash', '-c',
                        'export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr ":" "\\n" | grep -v snap | tr "\\n" ":"); '
                        'unset GTK_PATH; '
                        f'rviz2 -d {rviz_config} --ros-args -p use_sim_time:=true'
                    ],
                    output='log',
                    condition=IfCondition(use_rviz)
                )
            ]
        ),
    ])
