#!/usr/bin/env python3
"""
Localization + Navigation Launch File - Phase 2: Navigate with Saved Map

This launch file loads a pre-built RTAB-Map database and runs Nav2 for navigation.
Use this AFTER you have created a map with slam_mapping.launch.py

Usage:
    # Navigate with saved map (default path)
    ros2 launch robot_project localization_nav.launch.py

    # Navigate with custom map path
    ros2 launch robot_project localization_nav.launch.py db_path:=~/maps/my_map.db

    # Run random waypoint navigation
    ros2 launch robot_project localization_nav.launch.py use_random_nav:=true

Workflow:
    1. First run: ros2 launch robot_project slam_mapping.launch.py
    2. Explore the environment (map is saved automatically)
    3. Stop the mapping launch
    4. Then run: ros2 launch robot_project localization_nav.launch.py
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
    rtabmap_config = os.path.join(pkg_robot_project, 'config', 'rtabmap_rgbd.yaml')
    nav2_params = os.path.join(pkg_robot_project, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_random_nav = LaunchConfiguration('use_random_nav', default='false')
    autostart = LaunchConfiguration('autostart', default='true')

    # Database path for loading map - must match the saved map
    db_path = LaunchConfiguration('db_path', default=os.path.expanduser('~/maps/office_slam_final.db'))

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
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_random_nav', default_value='false',
                              description='Run random waypoint navigator'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('db_path',
                              default_value=os.path.expanduser('~/maps/office_slam_final.db'),
                              description='Path to RTAB-Map database'),
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

        # ========== RTAB-MAP (Localization Mode - Load Saved Map) ==========
        # Log which database is being loaded
        TimerAction(
            period=8.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         f'echo ""; echo "========================================"; '
                         f'echo "LOCALIZATION + NAVIGATION MODE"; '
                         f'echo "Loading map from: ~/maps/office_slam_final.db"; '
                         f'echo "Make sure this map exists!"; '
                         f'ls -lh ~/maps/office_slam_final.db 2>/dev/null || echo "WARNING: Map file not found!"; '
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
                            # LOCALIZATION Mode - Use Saved Map
                            'Mem/IncrementalMemory': 'false',  # Don't add new nodes
                            'Mem/InitWMWithAllNodes': 'true',  # Load all nodes from DB
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
                    arguments=[]  # Don't delete DB - load existing
                )
            ]
        ),

        # ========== NAV2 STACK ==========
        TimerAction(
            period=14.0,
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
                    }]
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
                    ]
                ),
                # Planner Server
                Node(
                    package='nav2_planner',
                    executable='planner_server',
                    name='planner_server',
                    output='screen',
                    parameters=[configured_params]
                ),
                # Behavior Server
                Node(
                    package='nav2_behaviors',
                    executable='behavior_server',
                    name='behavior_server',
                    output='screen',
                    parameters=[configured_params]
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
                    ]
                ),
            ]
        ),

        # ========== RANDOM WAYPOINT NAVIGATOR (optional) ==========
        TimerAction(
            period=20.0,
            actions=[
                Node(
                    package='robot_project',
                    executable='random_waypoint_nav',
                    name='random_waypoint_nav',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'num_waypoints': 20,
                        'mode': 'coverage',
                        'min_obstacle_distance': 0.30,
                        'goal_timeout': 120.0,
                    }],
                    condition=IfCondition(use_random_nav)
                )
            ]
        ),

        # ========== RVIZ ==========
        TimerAction(
            period=12.0,
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
