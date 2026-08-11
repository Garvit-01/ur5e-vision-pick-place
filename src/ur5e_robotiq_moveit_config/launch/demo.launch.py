from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launch_utils import DeclareBooleanLaunchArg


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder(
        "ur5e_robotiq", package_name="ur5e_robotiq_moveit_config"
    ).to_moveit_configs()
    launch_package_path = moveit_config.package_path

    ld = LaunchDescription()
    ld.add_action(DeclareBooleanLaunchArg("db", default_value=False))
    ld.add_action(DeclareBooleanLaunchArg("debug", default_value=False))
    ld.add_action(DeclareBooleanLaunchArg("use_rviz", default_value=True))

    virtual_joints_launch = launch_package_path / "launch/static_virtual_joint_tfs.launch.py"
    if virtual_joints_launch.exists():
        ld.add_action(
            IncludeLaunchDescription(PythonLaunchDescriptionSource(str(virtual_joints_launch)))
        )

    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(launch_package_path / "launch/rsp.launch.py"))
        )
    )

    # --- Controllers first: ros2_control_node + spawners ---
    # move_group does its controller discovery once, at its own startup, and
    # never retries. If it starts before these controllers are fully active
    # (they take several seconds), it permanently caches "0 controllers" for
    # its whole lifetime. Fix: bring these up first, then delay move_group.
    ld.add_action(
        Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[str(moveit_config.package_path / "config/ros2_controllers.yaml")],
            remappings=[("/controller_manager/robot_description", "/robot_description")],
        )
    )
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(launch_package_path / "launch/spawn_controllers.launch.py")
            )
        )
    )

    # --- move_group, delayed so controllers are already active ---
    ld.add_action(
        TimerAction(
            period=8.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        str(launch_package_path / "launch/move_group.launch.py")
                    )
                )
            ],
        )
    )

    # RViz can come up whenever; delay slightly so it doesn't race move_group either
    ld.add_action(
        TimerAction(
            period=9.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        str(launch_package_path / "launch/moveit_rviz.launch.py")
                    ),
                    condition=IfCondition(LaunchConfiguration("use_rviz")),
                )
            ],
        )
    )

    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(launch_package_path / "launch/warehouse_db.launch.py")
            ),
            condition=IfCondition(LaunchConfiguration("db")),
        )
    )

    return ld
