from setuptools import setup
from glob import glob

package_name = 'robot_hw1'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
        (f'share/{package_name}/launch', glob('launch/*.launch.py')),
        (f'share/{package_name}/urdf', glob('urdf/*.xacro')),
        (f'share/{package_name}/rviz', glob('rviz/*.rviz')),
        (f'share/{package_name}/config', glob('config/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mmf',
    maintainer_email='mmf@example.com',
    description='Minimal ROS 2 homework package with cmd_vel and noisy odom nodes',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'cmd_vel_publisher = robot_hw1.cmd_vel_publisher:main',
            'noisy_odom_publisher = robot_hw1.noisy_odom_publisher:main',
        ],
    },
)

