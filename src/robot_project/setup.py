from setuptools import setup
from glob import glob
import os

package_name = 'robot_project'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        (f'share/{package_name}', ['package.xml']),
        (f'share/{package_name}/launch', glob('launch/*.launch.py')),
        (f'share/{package_name}/config', glob('config/*.yaml')),
        (f'share/{package_name}/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Team 14',
    maintainer_email='team14@itu.edu.tr',
    description='KON414E Final Project: 3D SLAM and Autonomous Navigation',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'evaluation_node = robot_project.evaluation_node:main',
            'waypoint_navigator = robot_project.waypoint_navigator:main',
            'map_metrics = robot_project.map_metrics:main',
            'autonomous_explorer = robot_project.autonomous_explorer:main',
            'slam_comparison = robot_project.slam_comparison:main',
            'random_waypoint_nav = robot_project.random_waypoint_nav:main',
            'simple_goal_nav = robot_project.simple_goal_nav:main',
            'stop_robot = robot_project.stop_robot:main',
            'hybrid_slam_controller = robot_project.hybrid_slam_controller:main',
        ],
    },
)
