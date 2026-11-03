"""Real-hardware launch: wraps zed-ros2-wrapper for one ZED 2i.

Needs the zed_wrapper package (and the ZED SDK) installed where this runs, i.e. inside
the Jetson/ZED Box container, never in the simulation workspace.

Example, two cameras in the same container:
  ros2 launch caddy_ai2_ros2_camera_zed_2i zed_2i.launch.py camera_name:=zed_2i_left  serial_number:=<SN1>
  ros2 launch caddy_ai2_ros2_camera_zed_2i zed_2i.launch.py camera_name:=zed_2i_right serial_number:=<SN2>

camera_name matches the sensor key in robot_params.yaml, so the topics keep the same
names as in simulation: /<camera_name>/zed_node/...
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    zed_share = get_package_share_directory('zed_wrapper')

    zed = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(zed_share, 'launch', 'zed_camera.launch.py')
        ),
        launch_arguments={
            'camera_name': LaunchConfiguration('camera_name'),
            'camera_model': 'zed2i',
            'serial_number': LaunchConfiguration('serial_number'),
            # The robot URDF and TF tree come from caddy_ai2_ros2_description.
            'publish_urdf': 'false',
            'publish_tf': 'false',
            'publish_map_tf': 'false',
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument('camera_name', default_value='zed_2i_front',
                              description='Sensor key in robot_params.yaml; also the topic namespace'),
        DeclareLaunchArgument('serial_number', default_value='0',
                              description='ZED serial number. Required with two cameras (0 = first found)'),
        zed,
    ])
