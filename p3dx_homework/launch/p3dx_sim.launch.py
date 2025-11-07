#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_p3dx_description = get_package_share_directory('p3dx_description')
    pkg_p3dx_control = get_package_share_directory('p3dx_control')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # URDF file
    urdf_file = os.path.join(pkg_p3dx_description, 'urdf', 'p3dx', 'pioneer3dx.xacro')
    doc = xacro.process_file(urdf_file, mappings={'robot_namespace': '/'})
    robot_desc = doc.toprettyxml(indent='  ')

    # Controller config
    controller_config = os.path.join(pkg_p3dx_control, 'config', 'p3dx_controllers.yaml')

    # Parameters
    params = {
        'robot_description': robot_desc,
        'use_sim_time': True
    }

    # Nodes
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        )
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'p3dx', '-topic', 'robot_description'],
        output='screen'
    )

    # Load controller manager with config
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[controller_config],
        output='screen'
    )

    # Spawn controllers with delay
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '-c', '/controller_manager'],
        output='screen'
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '-c', '/controller_manager'],
        output='screen'
    )

    # Delayed controller spawning (wait for Gazebo to be ready)
    delayed_joint_state_spawner = TimerAction(
        period=3.0,
        actions=[joint_state_broadcaster_spawner]
    )

    delayed_diff_drive_spawner = TimerAction(
        period=4.0,
        actions=[diff_drive_controller_spawner]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,
        delayed_joint_state_spawner,
        delayed_diff_drive_spawner
    ])
