#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_p3dx_description = get_package_share_directory('p3dx_description')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # URDF file path
    urdf_file = os.path.join(pkg_p3dx_description, 'urdf', 'p3dx', 'pioneer3dx.xacro')

    # Process xacro
    doc = xacro.process_file(urdf_file, mappings={'robot_namespace': '/'})
    robot_desc = doc.toprettyxml(indent='  ')

    params = {'robot_description': robot_desc, 'use_sim_time': True}

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        )
    )

    # Spawn robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'p3dx', '-topic', 'robot_description'],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity
    ])
