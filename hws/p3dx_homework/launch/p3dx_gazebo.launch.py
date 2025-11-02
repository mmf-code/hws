#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    # Package directories
    pkg_p3dx_gazebo = get_package_share_directory('p3dx_gazebo')
    pkg_p3dx_description = get_package_share_directory('p3dx_description')
    pkg_p3dx_control = get_package_share_directory('p3dx_control')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')
    z_pose = LaunchConfiguration('z_pose', default='0.01')

    # URDF file path
    urdf_file = os.path.join(pkg_p3dx_description, 'urdf', 'p3dx', 'pioneer3dx.xacro')

    # Process xacro to get robot description
    doc = xacro.process_file(urdf_file, mappings={'robot_namespace': '/'})
    robot_desc = doc.toprettyxml(indent='  ')

    params = {
        'robot_description': robot_desc,
        'use_sim_time': use_sim_time
    }

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
        ),
        launch_arguments={'verbose': 'false'}.items()
    )

    # Spawn robot in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'p3dx',
            '-topic', 'robot_description',
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose
        ],
        output='screen'
    )

    # Controller configuration file
    controller_config = os.path.join(
        pkg_p3dx_control,
        'config',
        'p3dx_controllers.yaml'
    )

    # Controller manager (will be spawned by gazebo_ros2_control plugin)
    # We just need to spawn the controllers after a delay
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true',
                            description='Use simulation clock'),
        DeclareLaunchArgument('x_pose', default_value='0.0',
                            description='Initial x position'),
        DeclareLaunchArgument('y_pose', default_value='0.0',
                            description='Initial y position'),
        DeclareLaunchArgument('z_pose', default_value='0.01',
                            description='Initial z position'),

        gazebo,
        robot_state_publisher,
        spawn_entity,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner
    ])
