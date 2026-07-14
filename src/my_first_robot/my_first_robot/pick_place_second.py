import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
from moveit_msgs.msg import CollisionObject
from geometry_msgs.msg import PoseStamped, Pose
from shape_msgs.msg import SolidPrimitive
from control_msgs.action import GripperCommand
import time

class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place')
        
        self._action_client = ActionClient(self, MoveGroup, 'move_action')
        self._gripper_client = ActionClient(
            self, GripperCommand, 
            '/panda_hand_controller/gripper_cmd'
        )
        
        self._scene_pub = self.create_publisher(
            CollisionObject, 'collision_object', 10
        )
        
        self.get_logger().info('Waiting for MoveGroup...')
        self._action_client.wait_for_server()
        self.get_logger().info('Connected!')
        
        self.add_cube()
        time.sleep(1.0)
        self.open_gripper()

    def add_cube(self):
        cube = CollisionObject()
        cube.header.frame_id = "panda_link0"
        cube.id = "target_cube"
        shape = SolidPrimitive()
        shape.type = SolidPrimitive.BOX
        shape.dimensions = [0.05, 0.05, 0.05]
        pose = Pose()
        pose.position.x = 0.4
        pose.position.y = 0.0
        pose.position.z = 0.2
        pose.orientation.w = 1.0
        cube.primitives.append(shape)
        cube.primitive_poses.append(pose)
        cube.operation = CollisionObject.ADD
        self._scene_pub.publish(cube)
        self.get_logger().info('Cube added at (0.4, 0.0, 0.2)')

    def open_gripper(self):
        self.get_logger().info('Opening gripper...')
        goal = GripperCommand.Goal()
        goal.command.position = 0.08  # fully open
        goal.command.max_effort = 10.0
        future = self._gripper_client.send_goal_async(goal)
        future.add_done_callback(lambda f: self.move_above_cube())

    def close_gripper(self):
        self.get_logger().info('Closing gripper...')
        goal = GripperCommand.Goal()
        goal.command.position = 0.02  # closed
        goal.command.max_effort = 10.0
        future = self._gripper_client.send_goal_async(goal)
        future.add_done_callback(lambda f: self.move_up())

    def move_above_cube(self):
        self.get_logger().info('Moving above cube...')
        self.send_cartesian_goal(0.4, 0.0, 0.35, self.move_to_cube)

    def move_to_cube(self):
        self.get_logger().info('Moving to cube...')
        self.send_cartesian_goal(0.4, 0.0, 0.26, self.close_gripper)

    def move_up(self):
        self.get_logger().info('Moving up with cube...')
        self.send_cartesian_goal(0.4, 0.0, 0.5, self.done)

    def done(self):
        self.get_logger().info('Pick complete!')
        rclpy.shutdown()

    def send_cartesian_goal(self, x, y, z, callback):
        goal = MoveGroup.Goal()
        goal.request.group_name = "panda_arm"
        goal.request.num_planning_attempts = 20
        goal.request.allowed_planning_time = 10.0
        goal.request.max_velocity_scaling_factor = 0.1
        goal.request.max_acceleration_scaling_factor = 0.1

        target = PoseStamped()
        target.header.frame_id = "panda_link0"
        target.pose.position.x = x
        target.pose.position.y = y
        target.pose.position.z = z
        target.pose.orientation.w = 1.0

        pc = PositionConstraint()
        pc.header.frame_id = "panda_link0"
        pc.link_name = "panda_hand"
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.SPHERE
        primitive.dimensions = [0.01]
        pc.constraint_region.primitives.append(primitive)
        pc.constraint_region.primitive_poses.append(target.pose)
        pc.weight = 1.0

        oc = OrientationConstraint()
        oc.header.frame_id = "panda_link0"
        oc.link_name = "panda_hand"
        oc.orientation = target.pose.orientation
        oc.absolute_x_axis_tolerance = 0.5
        oc.absolute_y_axis_tolerance = 0.5
        oc.absolute_z_axis_tolerance = 0.5
        oc.weight = 1.0

        constraints = Constraints()
        constraints.position_constraints.append(pc)
        constraints.orientation_constraints.append(oc)
        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = False

        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(
                lambda r: callback()
            )
        )

def main():
    rclpy.init()
    node = PickPlace()
    rclpy.spin(node)

if __name__ == '__main__':
    main()