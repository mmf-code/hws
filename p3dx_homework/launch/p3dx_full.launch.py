#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_p3dx_description = get_package_share_directory('p3dx_description')
    pkg_p3dx_control = get_package_share_directory('p3dx_control')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # Paths
    urdf_file = os.path.join(pkg_p3dx_description, 'urdf', 'p3dx', 'pioneer3dx.xacro')
    controller_config = os.path.join(pkg_p3dx_control, 'config', 'p3dx_controllers.yaml')

    # Process xacro with controller config path
    doc = xacro.process_file(
        urdf_file,
        mappings={
            'robot_namespace': '/',
            'controller_config_file': controller_config
        }
    )
    robot_desc = doc.toprettyxml(indent='  ')

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_desc,
            'use_sim_time': True
        }]
    )

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        )
    )

    # Spawn Robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'p3dx', '-topic', 'robot_description'],
        output='screen'
    )

    # Controller Spawners (with delay to wait for gazebo_ros2_control)
    joint_state_broadcaster_spawner = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['joint_state_broadcaster'],
                output='screen'
            )
        ]
    )

    diff_drive_controller_spawner = TimerAction(
        period=6.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['diff_drive_controller'],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner
    ])
