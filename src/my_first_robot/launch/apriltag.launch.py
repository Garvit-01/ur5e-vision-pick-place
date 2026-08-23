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
        # Fixed camera mount pose, measured from the Isaac Sim scene
        # (see docs_local/UR5e_AprilTag_Perception_Integration.md).
        # Rotation is the raw USD camera orientation composed with the
        # fixed 180-deg-about-X correction between USD's camera
        # convention (looks down local -Z) and ROS's optical convention
        # (looks down local +Z) - it works out to essentially the same
        # "point straight down" quaternion used for the gripper elsewhere
        # in this project.
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_mount_tf',
            output='screen',
            arguments=[
                '--x', '0.4',
                '--y', '-0.3',
                '--z', '0.853848890170154',
                '--qx', '0.9999613451273703',
                '--qy', '-0.005076354639781767',
                '--qz', '0.005076354639757502',
                '--qw', '0.005076366633993716',
                '--frame-id', 'base_link',
                '--child-frame-id', 'camera_link',
            ],
        ),
    ])
