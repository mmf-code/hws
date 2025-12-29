#!/usr/bin/env python3
"""
HW3 Launch file - loads office world, spawns robot, starts rviz and controller
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # package paths
    pkg_robot_hw1 = get_package_share_directory('robot_hw1')
    pkg_cpr_office = get_package_share_directory('cpr_office_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # file paths
    robot_urdf_file = os.path.join(pkg_robot_hw1, 'urdf', 'p3dx_hw2.urdf.xacro')
    office_urdf_file = os.path.join(pkg_cpr_office, 'urdf', 'office_geometry.urdf.xacro')
    rviz_config_file = os.path.join(pkg_robot_hw1, 'rviz', 'hw3_config.rviz')
    world_file = os.path.join(pkg_robot_hw1, 'worlds', 'empty_office.world')

    # launch args
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    run_controller = LaunchConfiguration('run_controller', default='true')

    # spawn position (found this spot by trial and error lol)
    robot_x = LaunchConfiguration('robot_x', default='2.0')
    robot_y = LaunchConfiguration('robot_y', default='0.0')
    robot_z = LaunchConfiguration('robot_z', default='0.1')
    robot_yaw = LaunchConfiguration('robot_yaw', default='0.0')

    # declare args
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true', description='sim time')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='true', description='start rviz')

    declare_run_controller = DeclareLaunchArgument(
        'run_controller', default_value='true', description='run motion node')

    declare_robot_x = DeclareLaunchArgument('robot_x', default_value='2.0')
    declare_robot_y = DeclareLaunchArgument('robot_y', default_value='0.0')
    declare_robot_z = DeclareLaunchArgument('robot_z', default_value='0.1')
    declare_robot_yaw = DeclareLaunchArgument('robot_yaw', default_value='0.0')

    # process urdf with xacro
    robot_description = ParameterValue(
        Command(['xacro ', robot_urdf_file]),
        value_type=str
    )

    # robot state publisher - needed for tf
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description
        }]
    )

    # start gazebo with empty world (no ground plane, office has its own floor)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_file,
            'verbose': 'false'
        }.items()
    )

    # spawn office - had to use bash pipe because xacro wasnt working directly
    spawn_office = ExecuteProcess(
        cmd=[
            'bash', '-c',
            f'xacro {office_urdf_file} | ros2 run gazebo_ros spawn_entity.py -entity office_world -stdin -x 0.0 -y 0.0 -z 0.0'
        ],
        output='screen'
    )

    # spawn robot
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_robot',
        output='screen',
        arguments=[
            '-entity', 'pioneer3dx',
            '-topic', 'robot_description',
            '-x', robot_x,
            '-y', robot_y,
            '-z', robot_z,
            '-Y', robot_yaw
        ]
    )

    # rviz for visualization
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz)
    )

    # corridor navigator - delay so everything loads first
    corridor_navigator = TimerAction(
        period=8.0,
        actions=[
            Node(
                package='robot_hw1',
                executable='corridor_navigator',
                name='corridor_navigator',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'linear_speed': 0.3,
                    'angular_speed': 0.5,
                    'min_distance': 0.8,
                    'critical_distance': 0.4
                }],
                condition=IfCondition(run_controller)
            )
        ]
    )

    # plotjuggler for imu visualization
    plotjuggler = TimerAction(
        period=10.0,
        actions=[
            Node(
                package='plotjuggler',
                executable='plotjuggler',
                name='plotjuggler',
                output='screen',
                arguments=['--nosplash'],
                parameters=[{'use_sim_time': use_sim_time}]
            )
        ]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_rviz,
        declare_run_controller,
        declare_robot_x,
        declare_robot_y,
        declare_robot_z,
        declare_robot_yaw,
        gazebo,
        robot_state_publisher,
        spawn_office,
        spawn_robot,
        rviz,
        corridor_navigator,
        plotjuggler
    ])
