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
    LogInfo,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
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
    nav2_params = os.path.join(pkg_robot_project, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(pkg_robot_project, 'rviz', 'slam_config.rviz')

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_random_nav = LaunchConfiguration('use_random_nav', default='false')
    autostart = LaunchConfiguration('autostart', default='true')

    # Database path for loading map
    db_path_default = os.path.expanduser('~/maps/office_slam_final.db')
    db_path = LaunchConfiguration('db_path', default=db_path_default)

    # Robot spawn position - should match SLAM start position
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
        # Suppress RTAB-Map VWDictionary warnings
        SetEnvironmentVariable('RCUTILS_CONSOLE_OUTPUT_FORMAT', '[{severity}] [{name}]: {message}'),

        # ========== ARGUMENTS ==========
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_random_nav', default_value='false',
                              description='Run random waypoint navigator'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('db_path',
                              default_value=db_path_default,
                              description='Path to RTAB-Map database'),
        DeclareLaunchArgument('robot_x', default_value='2.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),
        DeclareLaunchArgument('robot_z', default_value='0.1'),

        # ========== MAP VERIFICATION ==========
        LogInfo(msg='\n' + '='*60),
        LogInfo(msg='  LOCALIZATION + NAVIGATION MODE'),
        LogInfo(msg='='*60),

        ExecuteProcess(
            cmd=['bash', '-c',
                 f'''
                 echo ""
                 echo "========================================"
                 echo "  MAP VERIFICATION"
                 echo "========================================"
                 DB_PATH="{db_path_default}"
                 if [ -f "$DB_PATH" ]; then
                     SIZE=$(ls -lh "$DB_PATH" | awk '{{print $5}}')
                     echo "  [OK] Map found: $DB_PATH"
                     echo "  [OK] Size: $SIZE"
                     echo ""
                     echo "  Loading map for LOCALIZATION mode..."
                     echo "  Robot will use saved map (no new mapping)"
                     echo "========================================"
                 else
                     echo "  [ERROR] Map NOT found: $DB_PATH"
                     echo "  Please run slam_mapping.launch.py first!"
                     echo "========================================"
                     exit 1
                 fi
                 echo ""
                 '''],
            output='screen'
        ),

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
                LogInfo(msg='[LAUNCH] Spawning robot at position (2.0, 0.0)...'),
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
                LogInfo(msg='[LAUNCH] Starting EKF sensor fusion...'),
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

        # ========== RTAB-MAP (LOCALIZATION MODE) ==========
        TimerAction(
            period=10.0,
            actions=[
                LogInfo(msg='[LAUNCH] Starting RTAB-Map in LOCALIZATION mode...'),
                LogInfo(msg='[LAUNCH] Loading 809MB database - please wait ~30-60 seconds...'),
                Node(
                    package='rtabmap_slam',
                    executable='rtabmap',
                    name='rtabmap',
                    output='screen',
                    arguments=[
                        '--ros-args',
                        '--log-level', 'rtabmap:=warn',  # Suppress INFO/DEBUG messages
                    ],
                    parameters=[{
                        'use_sim_time': use_sim_time,

                        # DATABASE - Load existing map
                        'database_path': db_path_default,

                        # LOCALIZATION MODE - Critical settings
                        'Mem/IncrementalMemory': 'false',      # NO new nodes
                        'Mem/InitWMWithAllNodes': 'true',      # Load ALL nodes from DB

                        # Frame configuration
                        'frame_id': 'base_link',
                        'odom_frame_id': 'odom',
                        'map_frame_id': 'map',

                        # Subscription
                        'subscribe_depth': True,
                        'subscribe_rgb': True,
                        'approx_sync': True,
                        'approx_sync_max_interval': 0.1,

                        # LOCALIZATION - Relaxed matching for better localization
                        'Rtabmap/LoopThr': '0.08',             # Lower threshold
                        'Vis/MinInliers': '8',                 # Lower inlier requirement
                        'Vis/MaxFeatures': '1000',             # More features
                        'RGBD/OptimizeFromGraphEnd': 'false',  # Optimize from start
                        'Reg/Strategy': '0',                   # Visual registration
                        'Reg/Force3DoF': 'true',               # 2D mode (ground robot)

                        # Map publishing
                        'Rtabmap/DetectionRate': '2.0',
                        'Grid/FromDepth': 'true',
                        'Grid/CellSize': '0.05',
                        'Grid/RangeMax': '4.0',

                        # TF publishing
                        'publish_tf': True,
                        'wait_for_transform': 0.5,
                        'tf_delay': 0.05,
                    }],
                    remappings=[
                        ('rgb/image', '/camera/rgbd_camera/image_raw'),
                        ('rgb/camera_info', '/camera/rgbd_camera/camera_info'),
                        ('depth/image', '/camera/rgbd_camera/depth/image_raw'),
                        ('odom', '/odometry/filtered'),
                        ('map', '/map'),
                    ]
                )
            ]
        ),

        # ========== RTAB-MAP LOADING MONITOR ==========
        TimerAction(
            period=15.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         '''
                         echo ""
                         echo "========================================"
                         echo "  CHECKING MAP LOADING STATUS..."
                         echo "========================================"

                         # Wait for rtabmap node
                         for i in {1..30}; do
                             if ros2 node list 2>/dev/null | grep -q rtabmap; then
                                 echo "  [OK] RTAB-Map node is running"
                                 break
                             fi
                             sleep 1
                         done

                         # Check if map is published
                         sleep 3
                         MAP_INFO=$(timeout 5 ros2 topic echo /map --once 2>/dev/null | grep -E "width|height" | head -2)
                         if [ -n "$MAP_INFO" ]; then
                             echo "  [OK] Map is being published:"
                             echo "$MAP_INFO" | sed 's/^/       /'
                         else
                             echo "  [WAIT] Map not yet published, still loading..."
                         fi

                         # Check TF
                         TF_CHECK=$(timeout 3 ros2 run tf2_ros tf2_echo map base_link 2>&1 | head -3)
                         if echo "$TF_CHECK" | grep -q "Translation"; then
                             echo "  [OK] TF map->base_link is available"
                         else
                             echo "  [WAIT] TF not yet available"
                         fi

                         echo "========================================"
                         echo ""
                         '''],
                    output='screen'
                )
            ]
        ),

        # ========== NAV2 STACK ==========
        TimerAction(
            period=30.0,  # Wait for RTAB-Map to fully load
            actions=[
                LogInfo(msg='[LAUNCH] Starting Nav2 navigation stack...'),
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
            period=45.0,  # Wait for Nav2 to be fully ready
            actions=[
                LogInfo(msg='[LAUNCH] Starting random waypoint navigator...'),
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
