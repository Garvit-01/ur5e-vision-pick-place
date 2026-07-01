from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_first_robot',
            executable='gripper_service',
            name='gripper_service',
            output='screen'
        ),
        Node(
            package='my_first_robot',
            executable='move_action_server',
            name='move_action_server',
            output='screen'
        ),
    ])