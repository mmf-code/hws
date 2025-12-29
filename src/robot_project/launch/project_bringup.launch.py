#!/usr/bin/env python3
"""
Project Bringup Launch File
Main entry point for the final project

Launches:
1. Gazebo with Office World
2. Pioneer 3-DX robot with sensors
3. robot_localization (EKF sensor fusion)
4. RViz visualization

Usage:
    ros2 launch robot_project project_bringup.launch.py
    ros2 launch robot_project project_bringup.launch.py use_rviz:=false
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    ExecuteProcess,
    SetEnvironmentVariable
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

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_ekf = LaunchConfiguration('use_ekf', default='true')

    # Robot spawn position (center of office corridor)
    robot_x = LaunchConfiguration('robot_x', default='2.0')
    robot_y = LaunchConfiguration('robot_y', default='0.0')
    robot_z = LaunchConfiguration('robot_z', default='0.1')

    # Process URDF with xacro
    robot_description = ParameterValue(
        Command(['xacro ', robot_urdf_file]),
        value_type=str
    )

    return LaunchDescription([
        # ========== ENVIRONMENT ==========
        # Fix RViz libpthread crash (snap vs apt conflict)
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_ekf', default_value='true'),
        DeclareLaunchArgument('robot_x', default_value='2.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),
        DeclareLaunchArgument('robot_z', default_value='0.1'),

        # ========== GAZEBO ==========
        # Start Gazebo with empty office world
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
        # Publishes TF tree from URDF
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

        # ========== SPAWN OFFICE WORLD ==========
        # Spawn office mesh into Gazebo (xacro must be processed first)
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
        # Spawn Pioneer 3-DX into Gazebo
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
        # Fuse IMU + Wheel Odometry
        TimerAction(
            period=8.0,
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
                    ],
                    condition=IfCondition(use_ekf)
                )
            ]
        ),

        # ========== RVIZ ==========
        # Visualization (delayed to let everything start)
        TimerAction(
            period=10.0,
            actions=[
                Node(
                    package='rviz2',
                    executable='rviz2',
                    name='rviz2',
                    output='screen',
                    parameters=[{'use_sim_time': use_sim_time}],
                    condition=IfCondition(use_rviz)
                )
            ]
        ),
    ])
