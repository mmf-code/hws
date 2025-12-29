#!/usr/bin/env python3
"""
Map Viewer Launch File - View RTAB-Map databases in RViz

This launch file visualizes RTAB-Map databases without running simulation.
Use it to inspect and compare different map databases.

Usage:
    # View default map (rtabmap_final_401mb_backup.db - recommended)
    ros2 launch robot_project view_map.launch.py

    # View specific database
    ros2 launch robot_project view_map.launch.py db_path:=~/.ros/rtabmap_715mb_broken.db

    # View with different map name
    ros2 launch robot_project view_map.launch.py db_name:=broken

Available maps:
    - rtabmap_final_401mb_backup.db (BEST - 703/750 poses optimized)
    - rtabmap_improved_230153.db (OK - 384/719 poses)
    - rtabmap.db (BROKEN - 0 poses optimized)
    - rtabmap_715mb_broken.db (BROKEN - fragmented graph)
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    TimerAction,
    LogInfo,
    SetEnvironmentVariable,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Default to the best database
    default_db = os.path.expanduser('~/.ros/rtabmap_final_401mb_backup.db')

    db_path = LaunchConfiguration('db_path', default=default_db)
    db_name = LaunchConfiguration('db_name', default='final_backup')

    return LaunchDescription([
        # Environment
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),

        # Arguments
        DeclareLaunchArgument(
            'db_path',
            default_value=default_db,
            description='Path to RTAB-Map database file'
        ),
        DeclareLaunchArgument(
            'db_name',
            default_value='final_backup',
            description='Short name for this database'
        ),

        # Database info
        LogInfo(msg='\n' + '='*60),
        LogInfo(msg='  RTAB-MAP DATABASE VIEWER'),
        LogInfo(msg='='*60),

        ExecuteProcess(
            cmd=['bash', '-c', f'''
                echo ""
                echo "Loading database: {default_db}"
                echo ""

                if [ -f "{default_db}" ]; then
                    SIZE=$(ls -lh "{default_db}" | awk '{{print $5}}')
                    echo "[OK] Database found: $SIZE"

                    echo ""
                    echo "Getting database info..."
                    source /opt/ros/humble/setup.bash
                    rtabmap-info "{default_db}" 2>&1 | grep -E "^(Path|Version|LTM|WM|Global graph|Optimized graph|Maps in graph|Links:)" | head -10
                    echo ""
                else
                    echo "[ERROR] Database not found: {default_db}"
                fi
            '''],
            output='screen'
        ),

        # Static TF for map frame
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_odom_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='odom_base_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link']
        ),

        # RTAB-Map in database viewer mode (publishes map without SLAM)
        TimerAction(
            period=2.0,
            actions=[
                LogInfo(msg='[LAUNCH] Starting RTAB-Map map publisher...'),
                Node(
                    package='rtabmap_slam',
                    executable='rtabmap',
                    name='rtabmap',
                    output='screen',
                    arguments=['--ros-args', '--log-level', 'warn'],
                    parameters=[{
                        'use_sim_time': False,

                        # Database
                        'database_path': default_db,

                        # Read-only mode
                        'Mem/IncrementalMemory': 'false',
                        'Mem/InitWMWithAllNodes': 'true',

                        # Frame config
                        'frame_id': 'base_link',
                        'odom_frame_id': 'odom',
                        'map_frame_id': 'map',

                        # Don't subscribe to sensors (just publish map)
                        'subscribe_depth': False,
                        'subscribe_rgb': False,
                        'subscribe_scan': False,
                        'subscribe_odom': False,

                        # Publish map
                        'publish_tf': False,  # We use static TF
                        'Grid/FromDepth': 'true',
                        'Grid/CellSize': '0.05',
                        'RGBD/CreateOccupancyGrid': 'true',
                    }]
                )
            ]
        ),

        # RViz
        TimerAction(
            period=5.0,
            actions=[
                LogInfo(msg='[LAUNCH] Starting RViz...'),
                ExecuteProcess(
                    cmd=['bash', '-c', '''
                        export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr ":" "\\n" | grep -v snap | tr "\\n" ":")
                        unset GTK_PATH
                        rviz2 -d /home/mmf/Documents/GitHub/hws_repo/src/robot_project/rviz/map_view.rviz
                    '''],
                    output='screen'
                )
            ]
        ),

        # Map info display
        TimerAction(
            period=10.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c', '''
                        echo ""
                        echo "========================================"
                        echo "  CHECKING MAP TOPIC..."
                        echo "========================================"

                        # Check map topic
                        MAP_INFO=$(timeout 5 ros2 topic echo /map --once 2>/dev/null | grep -E "width|height|resolution" | head -3)
                        if [ -n "$MAP_INFO" ]; then
                            echo "[OK] Map is published:"
                            echo "$MAP_INFO" | sed 's/^/    /'
                        else
                            echo "[WAIT] Map not yet published, waiting for RTAB-Map to load database..."
                            echo "       Large databases (400MB+) may take 30-60 seconds."
                        fi
                        echo "========================================"
                    '''],
                    output='screen'
                )
            ]
        ),
    ])
