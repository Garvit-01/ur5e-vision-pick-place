from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('my_first_robot'),
        'config',
        'tags_36h11_target_cube.yaml'
    )

    return LaunchDescription([
        Node(
            package='apriltag_ros',
            executable='apriltag_node',
            name='apriltag_node',
            output='screen',
            parameters=[config],
            remappings=[
                ('/camera_info', '/camera/camera_info'),
                ('/image_rect', '/camera/image_raw'),
            ],
        ),
    ])
