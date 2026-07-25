import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
from moveit_msgs.msg import CollisionObject, AttachedCollisionObject
from geometry_msgs.msg import PoseStamped, Pose
from shape_msgs.msg import SolidPrimitive
from control_msgs.action import GripperCommand
from tf2_ros import Buffer, TransformListener
from rclpy.time import Time
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
        self._attach_pub = self.create_publisher(
            AttachedCollisionObject, 'attached_collision_object', 10
        )
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        self.get_logger().info('Waiting for MoveGroup...')
        self._action_client.wait_for_server()
        self.get_logger().info('Connected!')

        self.detach_cube()
        time.sleep(0.5)
        self.wait_for_cube_detection()
        self.add_cube()
        time.sleep(1.0)
        self.move_to_home()

    def wait_for_cube_detection(self, timeout_sec=10.0):
        self.get_logger().info(
            'Waiting for cube detection (TF: panda_link0 -> target_cube)...'
        )
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                t = self._tf_buffer.lookup_transform(
                    'panda_link0', 'target_cube', Time()
                )
                self.cube_x = t.transform.translation.x
                self.cube_y = t.transform.translation.y
                self.cube_z = t.transform.translation.z
                self.get_logger().info(
                    f'Detected cube at ({self.cube_x:.3f}, '
                    f'{self.cube_y:.3f}, {self.cube_z:.3f})'
                )
                return
            except Exception:
                rclpy.spin_once(self, timeout_sec=0.2)
        raise RuntimeError(
            'Timed out waiting for cube detection TF (panda_link0 -> target_cube)'
        )
        
    def move_to_home(self):
        self.get_logger().info('Moving to home position...')
        goal = MoveGroup.Goal()
        goal.request.group_name = "panda_arm"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2

        from moveit_msgs.msg import RobotState
        from sensor_msgs.msg import JointState

        joint_state = JointState()
        joint_state.name = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        joint_state.position = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]

        robot_state = RobotState()
        robot_state.joint_state = joint_state

        goal.request.goal_constraints.append(
            self.joint_state_to_constraints(joint_state)
        )
        goal.planning_options.plan_only = False

        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(
                lambda r: self.open_gripper(self.move_above_cube)
            )
        )

    def joint_state_to_constraints(self, joint_state):
        from moveit_msgs.msg import Constraints, JointConstraint
        constraints = Constraints()
        for name, position in zip(joint_state.name, joint_state.position):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = position
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        return constraints

    def detach_cube(self):
        detached = AttachedCollisionObject()
        detached.link_name = "panda_hand"
        detached.object.id = "target_cube"
        detached.object.operation = CollisionObject.REMOVE
        self._attach_pub.publish(detached)
        self.get_logger().info('Detached any previously-attached cube')

    def add_cube(self):
        cube = CollisionObject()
        cube.header.frame_id = "panda_link0"
        cube.id = "target_cube"
        shape = SolidPrimitive()
        shape.type = SolidPrimitive.BOX
        shape.dimensions = [0.05, 0.05, 0.05]
        pose = Pose()
        pose.position.x = self.cube_x
        pose.position.y = self.cube_y
        pose.position.z = self.cube_z
        pose.orientation.w = 1.0
        cube.primitives.append(shape)
        cube.primitive_poses.append(pose)
        cube.operation = CollisionObject.ADD
        self._scene_pub.publish(cube)
        self.get_logger().info(
            f'Cube added at ({self.cube_x:.3f}, {self.cube_y:.3f}, {self.cube_z:.3f})'
        )

    def open_gripper(self, callback):
        self.get_logger().info('Opening gripper...')
        goal = GripperCommand.Goal()
        goal.command.position = 0.08  # fully open
        goal.command.max_effort = 10.0
        future = self._gripper_client.send_goal_async(goal)
        future.add_done_callback(lambda f: callback())

    def close_gripper(self):
        self.get_logger().info('Closing gripper...')
        goal = GripperCommand.Goal()
        goal.command.position = 0.02  # closed
        goal.command.max_effort = 10.0
        future = self._gripper_client.send_goal_async(goal)
        future.add_done_callback(lambda f: self.attach_cube())

    def attach_cube(self):
        self.get_logger().info('Attaching cube to gripper...')
        attached = AttachedCollisionObject()
        attached.link_name = "panda_hand"
        attached.object.header.frame_id = "panda_link0"
        attached.object.id = "target_cube"
        attached.object.operation = CollisionObject.ADD
        attached.touch_links = ["panda_hand", "panda_leftfinger", "panda_rightfinger"]
        self._attach_pub.publish(attached)
        time.sleep(0.5)  # let the planning scene monitor process the attach
        self.move_up()

    def move_above_cube(self):
        self.get_logger().info('Moving above cube...')
        self.send_cartesian_goal(self.cube_x, self.cube_y, self.cube_z + 0.15, self.move_to_cube)

    def move_to_cube(self):
        self.get_logger().info('Moving to cube...')
        # panda_hand is the wrist flange, not the fingertips — hand_tcp sits
        # ~0.1034m further along the approach axis, so offset the target to
        # land the fingertips at the cube's center
        self.send_cartesian_goal(self.cube_x, self.cube_y, self.cube_z + 0.103, self.close_gripper)

    def move_up(self):
        self.get_logger().info('Moving up with cube...')
        self.send_cartesian_goal(self.cube_x, self.cube_y, 0.5, self.move_to_place_above)

    def move_to_place_above(self):
        self.get_logger().info('Moving to place location...')
        self.send_cartesian_goal(0.4, 0.3, 0.5, self.move_to_place)

    def move_to_place(self):
        self.get_logger().info('Lowering to place location...')
        # Same fingertip-height offset as the grasp descent
        self.send_cartesian_goal(0.4, 0.3, 0.303, self.release_cube)

    def release_cube(self):
        self.detach_cube()
        time.sleep(0.5)  # let the planning scene monitor process the detach
        self.open_gripper(self.retreat)

    def retreat(self):
        self.get_logger().info('Retreating...')
        self.send_cartesian_goal(0.4, 0.3, 0.5, self.done)

    def done(self):
        self.get_logger().info('Pick and place complete!')
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
        # Point the gripper straight down (180 deg flip about X)
        target.pose.orientation.x = 1.0
        target.pose.orientation.y = 0.0
        target.pose.orientation.z = 0.0
        target.pose.orientation.w = 0.0

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
        oc.absolute_x_axis_tolerance = 0.3
        oc.absolute_y_axis_tolerance = 0.3
        oc.absolute_z_axis_tolerance = 0.3
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