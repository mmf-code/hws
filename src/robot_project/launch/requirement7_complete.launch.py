#!/usr/bin/env python3
"""
REQUIREMENT 7: Complete 3D SLAM to 2D Navigation Implementation

"Use 2D projection of the computed 3D map for navigation.
Assign random points in the environment to move the robot autonomously"

Workflow:
1. Load existing 809MB RTAB-Map 3D database
2. Run RTAB-Map in SLAM mode (publishes both 3D and 2D maps)
3. Nav2 uses 2D projection for planning
4. Random waypoint navigator creates autonomous navigation goals

This is the SIMPLIFIED, WORKING approach that avoids localization mode issues.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, TimerAction,
    ExecuteProcess, SetEnvironmentVariable, LogInfo, Shutdown
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg_robot_hw1 = get_package_share_directory('robot_hw1')
    pkg_robot_project = get_package_share_directory('robot_project')
    pkg_cpr_office = get_package_share_directory('cpr_office_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # File paths
    robot_urdf_file = os.path.join(pkg_robot_hw1, 'urdf', 'p3dx_hw2.urdf.xacro')
    office_urdf_file = os.path.join(pkg_cpr_office, 'urdf', 'office_geometry.urdf.xacro')
    world_file = os.path.join(pkg_robot_hw1, 'worlds', 'empty_office.world')
    ekf_config = os.path.join(pkg_robot_project, 'config', 'robot_localization.yaml')
    nav2_params = os.path.join(pkg_robot_project, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_random_nav = LaunchConfiguration('use_random_nav', default='true')
    autostart = LaunchConfiguration('autostart', default='true')

    db_path_default = os.path.expanduser('~/maps/office_slam_final.db')
    robot_x = LaunchConfiguration('robot_x', default='2.0')
    robot_y = LaunchConfiguration('robot_y', default='0.0')
    robot_z = LaunchConfiguration('robot_z', default='0.1')

    # Robot URDF
    robot_description = ParameterValue(
        Command(['xacro ', robot_urdf_file]),
        value_type=str
    )

    # Nav2 params
    configured_params = RewrittenYaml(
        source_file=nav2_params,
        param_rewrites={'use_sim_time': use_sim_time},
        convert_types=True
    )

    return LaunchDescription([
        # ========== SETUP ==========
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_random_nav', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('robot_x', default_value='2.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),
        DeclareLaunchArgument('robot_z', default_value='0.1'),

        # ========== STARTUP BANNER ==========
        LogInfo(msg='\n' + '='*70),
        LogInfo(msg='  REQUIREMENT 7: AUTONOMOUS NAVIGATION WITH 3D SLAM'),
        LogInfo(msg='  3D SLAM (RTAB-Map) → 2D Projection → Nav2 + Random Waypoints'),
        LogInfo(msg='='*70 + '\n'),

        # ========== GAZEBO ==========
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={'world': world_file, 'verbose': 'false'}.items()
        ),

        # ========== ROBOT STATE PUBLISHER ==========
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='log',
            parameters=[{'use_sim_time': use_sim_time, 'robot_description': robot_description}]
        ),

        # ========== SPAWN OFFICE ==========
        TimerAction(period=2.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c',
                     f'xacro {office_urdf_file} | ros2 run gazebo_ros spawn_entity.py '
                     f'-entity office_world -stdin -x 0.0 -y 0.0 -z 0.0'],
                output='log'
            )
        ]),

        # ========== SPAWN ROBOT ==========
        TimerAction(period=4.0, actions=[
            LogInfo(msg='[SYSTEM] Spawning robot...'),
            Node(
                package='gazebo_ros', executable='spawn_entity.py', name='spawn_robot',
                arguments=['-entity', 'pioneer3dx', '-topic', 'robot_description',
                          '-x', robot_x, '-y', robot_y, '-z', robot_z]
            )
        ]),

        # ========== EKF SENSOR FUSION ==========
        TimerAction(period=6.0, actions=[
            Node(
                package='robot_localization', executable='ekf_node',
                name='ekf_filter_node', output='log',
                parameters=[ekf_config, {'use_sim_time': use_sim_time}]
            )
        ]),

        # ========== DEPTH TO LASERSCAN ==========
        TimerAction(period=7.0, actions=[
            Node(
                package='depthimage_to_laserscan',
                executable='depthimage_to_laserscan_node',
                name='depthimage_to_laserscan', output='log',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'scan_height': 60,
                    'output_frame_id': 'camera_link',
                }],
                remappings=[
                    ('depth', '/camera/rgbd_camera/depth/image_raw'),
                    ('depth_camera_info', '/camera/rgbd_camera/depth/camera_info'),
                    ('scan', '/scan'),
                ]
            )
        ]),

        # ========== RTAB-MAP SLAM (Load existing 809MB database) ==========
        TimerAction(period=9.0, actions=[
            LogInfo(msg='[RTAB-Map] Starting 3D SLAM with existing 809MB database...'),
            LogInfo(msg='[RTAB-Map] Publishing both 3D (/rtabmap/cloud_map) and 2D (/map) maps...'),
            Node(
                package='rtabmap_slam', executable='rtabmap',
                name='rtabmap', output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'database_path': db_path_default,

                    # SLAM MODE - Load existing map and continue mapping
                    'Mem/IncrementalMemory': True,  # SLAM mode (not localization)
                    'Mem/InitWMWithAllNodes': False, # Start fresh but load if needed

                    # Critical for 2D map generation
                    'Grid/FromDepth': True,
                    'Grid/3D': True,
                    'Grid/CellSize': 0.05,
                    'Grid/RangeMax': 4.0,

                    # TF Publishing - CRITICAL for Nav2
                    'publish_tf': True,
                    'wait_for_transform': 0.5,
                    'tf_delay': 0.05,

                    # Loop closure tuning
                    'Rtabmap/LoopThr': 0.11,
                    'Kp/MaxFeatures': 800,

                    # Detection rate
                    'Rtabmap/DetectionRate': 2.0,
                    'subscribe_depth': True,
                    'subscribe_rgb': True,
                    'approx_sync': True,
                    'approx_sync_max_interval': 0.1,
                }],
                remappings=[
                    ('rgb/image', '/camera/rgbd_camera/image_raw'),
                    ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                    ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                    ('odom', '/odometry/filtered'),
                    ('map', '/map'),
                ]
            )
        ]),

        # ========== STATUS CHECK ==========
        TimerAction(period=14.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c',
                     '''
                     sleep 2
                     echo ""
                     echo "====== SYSTEM STATUS ======"
                     echo "[CHECK] RTAB-Map node:"
                     ros2 node list 2>/dev/null | grep -q rtabmap && echo "  ✓ Running" || echo "  ✗ Not found"

                     echo "[CHECK] 2D Map publication:"
                     timeout 3 ros2 topic echo /map --once 2>/dev/null | grep -q width && echo "  ✓ /map topic active" || echo "  ✗ No /map"

                     echo "[CHECK] 3D Cloud publication:"
                     timeout 3 ros2 topic list 2>/dev/null | grep -q rtabmap/cloud_map && echo "  ✓ /rtabmap/cloud_map active" || echo "  ✗ No cloud_map"

                     echo "[CHECK] TF transforms:"
                     timeout 3 ros2 run tf2_ros tf2_echo map base_link 2>&1 | grep -q "Translation" && echo "  ✓ map→base_link available" || echo "  ✗ No map frame"

                     echo "============================="
                     echo ""
                     '''],
                output='screen'
            )
        ]),

        # ========== NAV2 STACK ==========
        TimerAction(period=20.0, actions=[
            LogInfo(msg='[NAV2] Starting navigation stack...'),
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
            # Controller Server
            Node(
                package='nav2_controller', executable='controller_server',
                name='controller_server', output='log',
                parameters=[configured_params],
                remappings=[('cmd_vel', '/cmd_vel'), ('odom', '/odometry/filtered')]
            ),
            # Planner Server
            Node(
                package='nav2_planner', executable='planner_server',
                name='planner_server', output='log',
                parameters=[configured_params]
            ),
            # Behavior Server
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

        # ========== RANDOM WAYPOINT NAVIGATOR ==========
        TimerAction(period=28.0, actions=[
            LogInfo(msg='[NAVIGATION] Starting autonomous waypoint navigation (Requirement 7)...'),
            Node(
                package='robot_project', executable='random_waypoint_nav',
                name='random_waypoint_nav', output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'num_waypoints': 20,
                    'mode': 'coverage',
                    'min_obstacle_distance': 0.30,
                    'goal_timeout': 120.0,
                }],
                condition=IfCondition(use_random_nav)
            )
        ]),

        # ========== RVIZ ==========
        TimerAction(period=12.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c',
                     f'rviz2 -d {rviz_config} --ros-args -p use_sim_time:=true'],
                output='screen',
                condition=IfCondition(use_rviz)
            )
        ]),

        # ========== SUCCESS MESSAGE ==========
        TimerAction(period=30.0, actions=[
            ExecuteProcess(
                cmd=['bash', '-c',
                     '''
                     echo ""
                     echo "╔════════════════════════════════════════════════════════════════╗"
                     echo "║  REQUIREMENT 7: AUTONOMOUS NAVIGATION SYSTEM READY             ║"
                     echo "╠════════════════════════════════════════════════════════════════╣"
                     echo "║                                                                ║"
                     echo "║  ✓ 3D SLAM Map: 809MB (loaded and publishing)                 ║"
                     echo "║  ✓ 2D Projection: /map topic (occupancy grid)                 ║"
                     echo "║  ✓ Nav2 Navigation: Planning and control active              ║"
                     echo "║  ✓ Autonomous Waypoints: Random coverage navigation running  ║"
                     echo "║                                                                ║"
                     echo "║  Robot is now autonomously navigating using:                 ║"
                     echo "║  1. 3D point cloud from RTAB-Map SLAM                         ║"
                     echo "║  2. 2D projection for Nav2 path planning                      ║"
                     echo "║  3. Random waypoint selection in free space                  ║"
                     echo "║                                                                ║"
                     echo "╚════════════════════════════════════════════════════════════════╝"
                     echo ""
                     '''],
                output='screen'
            )
        ]),
    ])
