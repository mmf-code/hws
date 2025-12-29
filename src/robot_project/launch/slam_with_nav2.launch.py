#!/usr/bin/env python3
"""
HW3 Requirement 7: SLAM + Navigation
Phase 1: Build 3D map with autonomous explorer
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, TimerAction,
    ExecuteProcess, SetEnvironmentVariable, LogInfo
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_robot_hw1 = get_package_share_directory('robot_hw1')
    pkg_robot_project = get_package_share_directory('robot_project')
    pkg_cpr_office = get_package_share_directory('cpr_office_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    robot_urdf = os.path.join(pkg_robot_hw1, 'urdf', 'p3dx_hw2.urdf.xacro')
    office_urdf = os.path.join(pkg_cpr_office, 'urdf', 'office_geometry.urdf.xacro')
    world_file = os.path.join(pkg_robot_hw1, 'worlds', 'empty_office.world')
    ekf_config = os.path.join(pkg_robot_project, 'config', 'robot_localization.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_explorer = LaunchConfiguration('use_explorer', default='true')

    robot_description = ParameterValue(Command(['xacro ', robot_urdf]), value_type=str)

    return LaunchDescription([
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        SetEnvironmentVariable('RCUTILS_LOGGING_BUFFERED_STREAM', '1'),

        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_explorer', default_value='true'),

        # Cleanup
        ExecuteProcess(cmd=['rm', '-f', os.path.expanduser('~/.ros/rtabmap.db')], output='log'),

        # GAZEBO (2x speed)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')),
            launch_arguments={'world': world_file, 'verbose': 'false'}.items()
        ),

        # ROBOT STATE PUBLISHER
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            output='log',
            parameters=[{'use_sim_time': use_sim_time, 'robot_description': robot_description}]
        ),

        # SPAWN OFFICE (T=2s)
        TimerAction(period=2.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c',
                     f'xacro {office_urdf} | ros2 run gazebo_ros spawn_entity.py -entity office -stdin'],
                output='log'
            )
        ]),

        # SPAWN ROBOT (T=4s)
        TimerAction(period=4.0, actions=[
            Node(
                package='gazebo_ros', executable='spawn_entity.py',
                output='log',
                arguments=['-entity', 'pioneer3dx', '-topic', 'robot_description',
                          '-x', '2.0', '-y', '0.0', '-z', '0.1']
            )
        ]),

        # EKF (T=6s)
        TimerAction(period=6.0, actions=[
            Node(
                package='robot_localization', executable='ekf_node',
                name='ekf_filter_node', output='log',
                parameters=[ekf_config, {'use_sim_time': use_sim_time}]
            )
        ]),

        # DEPTH TO LASERSCAN (T=7s)
        TimerAction(period=7.0, actions=[
            Node(
                package='depthimage_to_laserscan', executable='depthimage_to_laserscan_node',
                name='depthimage_to_laserscan', output='log',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'scan_time': 0.033, 'range_min': 0.1, 'range_max': 4.0,
                    'scan_height': 60, 'output_frame_id': 'camera_link',
                }],
                remappings=[
                    ('depth', '/camera/rgbd_camera/depth/image_raw'),
                    ('depth_camera_info', '/camera/rgbd_camera/depth/camera_info'),
                    ('scan', '/scan'),
                ]
            )
        ]),

        # RTAB-MAP SLAM (T=9s)
        TimerAction(period=9.0, actions=[
            Node(
                package='rtabmap_slam', executable='rtabmap',
                name='rtabmap', output='log',
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

                    # Features
                    'Rtabmap/DetectionRate': '2.0',
                    'Kp/DetectorStrategy': '6',
                    'Kp/MaxFeatures': '500',
                    'Kp/MaxDepth': '4.0',

                    # 3D to 2D Projection - CRITICAL FOR NAV2
                    'RGBD/CreateOccupancyGrid': 'true',
                    'Grid/FromDepth': 'true',
                    'Grid/CellSize': '0.05',
                    'Grid/RangeMax': '4.0',
                    'Grid/RangeMin': '0.2',
                    'Grid/MaxObstacleHeight': '2.0',

                    # Graph
                    'Optimizer/Strategy': '1',
                    'Optimizer/Slam2D': 'true',
                    'RGBD/LinearUpdate': '0.1',
                    'RGBD/AngularUpdate': '0.1',

                    # TF
                    'publish_tf': True,
                    'wait_for_transform': 0.5,
                }],
                remappings=[
                    ('rgb/image', '/camera/rgbd_camera/image_raw'),
                    ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                    ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                    ('odom', '/odometry/filtered'),
                ]
            )
        ]),

        # AUTONOMOUS EXPLORER (T=14s)
        TimerAction(period=14.0, actions=[
            Node(
                package='robot_project', executable='autonomous_explorer',
                name='autonomous_explorer', output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'mode': 'free',
                    'linear_speed': 0.35,
                    'angular_speed': 0.8,
                    'min_distance': 1.0,
                    'critical_distance': 0.7,
                }],
                condition=IfCondition(use_explorer)
            )
        ]),

        # RVIZ (T=12s)
        TimerAction(period=12.0, actions=[
            Node(
                package='rviz2', executable='rviz2',
                name='rviz2', output='log',
                arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': use_sim_time}],
                condition=IfCondition(use_rviz)
            )
        ]),

        # STATUS MESSAGE (T=16s)
        TimerAction(period=16.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c', '''
echo ""
echo "========================================"
echo "  SLAM STARTED (2x speed)"
echo "========================================"
echo "  Robot is exploring..."
echo ""
echo "  When map is ready, in Terminal 2:"
echo "    ros2 run robot_project stop_robot --ros-args -p return_to_center:=true"
echo ""
echo "  Then start Nav2:"
echo "    ros2 launch robot_project add_nav2.launch.py"
echo "========================================"
echo ""
'''],
                output='screen'
            )
        ]),
    ])
