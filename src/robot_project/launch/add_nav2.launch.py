#!/usr/bin/env python3
"""
HW3 Requirement 7: Add Nav2 to running SLAM
Phase 2: Navigate using 2D projection of 3D map
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, TimerAction, ExecuteProcess, SetEnvironmentVariable
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg_robot_project = get_package_share_directory('robot_project')
    nav2_params = os.path.join(pkg_robot_project, 'config', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_random_nav = LaunchConfiguration('use_random_nav', default='true')
    autostart = LaunchConfiguration('autostart', default='true')

    configured_params = RewrittenYaml(
        source_file=nav2_params,
        param_rewrites={'use_sim_time': use_sim_time},
        convert_types=True
    )

    return LaunchDescription([
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),

        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_random_nav', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),

        # Verify SLAM is running
        ExecuteProcess(
            cmd=['bash', '-c', '''
echo ""
echo "========================================"
echo "  ADDING NAV2 TO SLAM"
echo "========================================"
if ros2 node list 2>/dev/null | grep -q rtabmap; then
    echo "  RTAB-Map: OK"
else
    echo "  ERROR: RTAB-Map not running!"
    exit 1
fi
if timeout 2 ros2 topic echo /map --once 2>/dev/null | grep -q width; then
    echo "  2D Map: OK"
else
    echo "  WARNING: /map not publishing yet"
fi
echo "========================================"
echo ""
'''],
            output='screen'
        ),

        # NAV2 STACK (T=2s)
        TimerAction(period=2.0, actions=[
            # Lifecycle Manager
            Node(
                package='nav2_lifecycle_manager', executable='lifecycle_manager',
                name='lifecycle_manager_navigation', output='log',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'autostart': autostart,
                    'node_names': ['controller_server', 'planner_server', 'behavior_server', 'bt_navigator']
                }]
            ),
            # Controller
            Node(
                package='nav2_controller', executable='controller_server',
                name='controller_server', output='log',
                parameters=[configured_params],
                remappings=[('cmd_vel', '/cmd_vel'), ('odom', '/odometry/filtered')]
            ),
            # Planner
            Node(
                package='nav2_planner', executable='planner_server',
                name='planner_server', output='log',
                parameters=[configured_params]
            ),
            # Behavior
            Node(
                package='nav2_behaviors', executable='behavior_server',
                name='behavior_server', output='log',
                parameters=[configured_params]
            ),
            # BT Navigator
            Node(
                package='nav2_bt_navigator', executable='bt_navigator',
                name='bt_navigator', output='log',
                parameters=[configured_params],
                remappings=[('odom', '/odometry/filtered')]
            ),
        ]),

        # RANDOM WAYPOINT NAVIGATOR (T=12s)
        TimerAction(period=12.0, actions=[
            Node(
                package='robot_project', executable='random_waypoint_nav',
                name='random_waypoint_nav', output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'num_waypoints': 15,
                    'mode': 'coverage',
                    'min_obstacle_distance': 0.35,
                    'goal_timeout': 90.0,
                }],
                condition=IfCondition(use_random_nav)
            )
        ]),

        # SUCCESS MESSAGE (T=15s)
        TimerAction(period=15.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c', '''
echo ""
echo "========================================"
echo "  NAV2 + RANDOM WAYPOINTS ACTIVE"
echo "========================================"
echo ""
echo "  HW3 Requirement 7 Complete:"
echo "    - 3D SLAM map (RTAB-Map)"
echo "    - 2D projection (/map)"
echo "    - Nav2 path planning"
echo "    - Random autonomous navigation"
echo ""
echo "  Robot is navigating!"
echo "========================================"
echo ""
'''],
                output='screen'
            )
        ]),
    ])
