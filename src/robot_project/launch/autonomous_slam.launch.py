#!/usr/bin/env python3
"""
Autonomous SLAM Launch File

Launches complete autonomous exploration and mapping:
1. Gazebo with Office World
2. Robot with sensors
3. robot_localization (EKF sensor fusion)
4. RTAB-Map SLAM
5. Autonomous Explorer (hw3-style depth-based navigation)
6. Evaluation nodes (ground truth comparison)
7. RViz visualization (2D/3D mapping)

Usage:
    ros2 launch robot_project autonomous_slam.launch.py
    ros2 launch robot_project autonomous_slam.launch.py slam_mode:=icp
    ros2 launch robot_project autonomous_slam.launch.py use_rviz:=false
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
from launch.substitutions import LaunchConfiguration, Command, PythonExpression
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
    rtabmap_rgbd_config = os.path.join(pkg_robot_project, 'config', 'rtabmap_rgbd.yaml')
    rtabmap_icp_config = os.path.join(pkg_robot_project, 'config', 'rtabmap_icp.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    slam_mode = LaunchConfiguration('slam_mode', default='rgbd')
    run_explorer = LaunchConfiguration('run_explorer', default='true')

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

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('slam_mode', default_value='rgbd',
                              description='SLAM mode: rgbd or icp'),
        DeclareLaunchArgument('run_explorer', default_value='true',
                              description='Run autonomous explorer (set false for Nav2)'),
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

        # ========== STATIC TF: world -> map ==========
        # Ground truth publishes in 'world' frame, SLAM uses 'map' frame
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='world_to_map_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'world', 'map'],
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # ========== STATIC TF: map -> odom ==========
        # Initial identity transform (RTAB-Map will correct via loop closures)
        # This enables TF lookup: map -> odom -> base_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
            parameters=[{'use_sim_time': use_sim_time}]
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

        # ========== SENSOR FUSION (EKF) ==========
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
                    ],
                    remappings=[
                        ('odometry/filtered', '/odometry/filtered')
                    ]
                )
            ]
        ),

        # ========== RTAB-MAP SLAM (RGB-D Mode) ==========
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
                    arguments=['--delete_db_on_start'],
                    condition=IfCondition(
                        PythonExpression(["'", slam_mode, "' == 'rgbd'"])
                    )
                ),
                # ICP Mode
                Node(
                    package='rtabmap_slam',
                    executable='rtabmap',
                    name='rtabmap',
                    output='screen',
                    parameters=[
                        rtabmap_icp_config,
                        {
                            'use_sim_time': use_sim_time,
                            'database_path': '~/.ros/rtabmap.db',
                            'Reg/Strategy': '1',
                            'Reg/Force3DoF': 'true',
                            'Mem/IncrementalMemory': 'true',
                            'Mem/InitWMWithAllNodes': 'false',
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
                    arguments=['--delete_db_on_start'],
                    condition=IfCondition(
                        PythonExpression(["'", slam_mode, "' == 'icp'"])
                    )
                )
            ]
        ),

        # ========== AUTONOMOUS EXPLORER ==========
        TimerAction(
            period=15.0,
            actions=[
                Node(
                    package='robot_project',
                    executable='autonomous_explorer',
                    name='autonomous_explorer',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'mode': 'free',  # 'free' (hw3-style) or 'waypoint'
                        'linear_speed': 0.35,
                        'angular_speed': 0.6,
                        'min_distance': 0.8,
                        'critical_distance': 0.4,
                    }],
                    condition=IfCondition(run_explorer)
                )
            ]
        ),

        # ========== EVALUATION NODE ==========
        TimerAction(
            period=12.0,
            actions=[
                Node(
                    package='robot_project',
                    executable='evaluation_node',
                    name='evaluation_node',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'slam_mode': slam_mode,
                        'output_dir': 'project/results/data',
                    }]
                )
            ]
        ),

        # ========== MAP METRICS NODE ==========
        TimerAction(
            period=12.0,
            actions=[
                Node(
                    package='robot_project',
                    executable='map_metrics',
                    name='map_metrics',
                    output='screen',
                    parameters=[{
                        'use_sim_time': use_sim_time,
                        'slam_mode': slam_mode,
                        'output_dir': 'project/results/data',
                    }]
                )
            ]
        ),

        # ========== RVIZ ==========
        TimerAction(
            period=20.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'bash', '-c',
                        'export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr ":" "\\n" | grep -v snap | tr "\\n" ":"); '
                        'unset GTK_PATH; '
                        'export OGRE_RTT_MODE=FBO; '
                        f'rviz2 -d {rviz_config} --ros-args -p use_sim_time:=true'
                    ],
                    output='screen',
                    condition=IfCondition(use_rviz)
                )
            ]
        ),
    ])
