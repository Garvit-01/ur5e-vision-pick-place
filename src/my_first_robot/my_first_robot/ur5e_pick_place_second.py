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
import time,math

class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place')
        
        self._action_client = ActionClient(self, MoveGroup, 'move_action')
        
        
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
        self.lookup_cube_pose()

    def lookup_cube_pose(self, timeout_sec=30.0):
        # The TF listener only receives data while the executor is spinning,
        # which hasn't started yet this early in __init__ — pump it manually.
        # spin_once() often returns almost instantly (e.g. if some unrelated
        # /tf message, like the robot's own joint-state-derived transforms,
        # is already queued), so track real elapsed wall-clock time instead
        # of counting retries - otherwise a fast-returning spin_once burns
        # through a fixed retry count in milliseconds without ever actually
        # waiting long enough for target_cube to show up.
        deadline = time.time() + timeout_sec
        t = None
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            try:
                t = self._tf_buffer.lookup_transform('base_link', 'target_cube', rclpy.time.Time())
                break
            except Exception:
                continue
        if t is None:
            self.get_logger().error(
                'Could not find target_cube TF after 30s — '
                'is apriltag_node running and actually detecting the tag?'
            )
            rclpy.shutdown()
            return
        self.cube_x = t.transform.translation.x
        self.cube_y = t.transform.translation.y
        # apriltag_ros reports the tag's flat plane (the cube's top face,
        # since that's what the overhead camera sees), not the cube's
        # volumetric center that the rest of this script assumes — correct
        # by half the known 5cm cube height.
        #
        # There's also a separate, unexplained ~0.167m systematic offset
        # between the detected height and the cube's known real height in
        # the Isaac Sim scene (possibly related to the camera_info fy/fx
        # mismatch Isaac Sim logs a warning about) - not root-caused yet,
        # compensated here empirically. Same spirit as the TCP-offset
        # estimate used elsewhere in this file: a placeholder to revisit,
        # not a measured/derived constant.
        CALIBRATION_OFFSET = 0.167
        self.cube_z = t.transform.translation.z - 0.025 + CALIBRATION_OFFSET
        self.get_logger().info(
            f'Detected cube at ({self.cube_x:.3f}, {self.cube_y:.3f}, {self.cube_z:.3f})'
        )
        self.add_cube()
        time.sleep(1.0)
        self.move_to_home()

    def move_to_home(self, retries_left=5):
        self.get_logger().info('Moving to home position...')
        goal = MoveGroup.Goal()
        goal.request.group_name = "ur_manipulator"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2

        from moveit_msgs.msg import RobotState
        from sensor_msgs.msg import JointState

        joint_state = JointState()
        joint_state.name = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']

        joint_position_max = [360,360,180,360,360,360]
                # since the values are in degress let's convert to radian
        
        for i,deg in enumerate(joint_position_max):
            joint_position_max[i] = deg*math.pi/180
                
        joint_position_min = [-1*i for i in joint_position_max]

        joint_positions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        joint_state.position = joint_positions

        robot_state = RobotState()
        robot_state.joint_state = joint_state

        goal.request.goal_constraints.append(
            self.joint_state_to_constraints(joint_state)
        )
        goal.planning_options.plan_only = False

        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(
                lambda r: self.on_goal_result(
                    r,
                    lambda n: self.move_to_home(n),
                    lambda: self.open_gripper(self.move_above_cube),
                    retries_left,
                )
            )
        )

    def open_gripper(self, callback, retries_left=5):
        self.get_logger().info('Opening gripper...')
        goal = MoveGroup.Goal()
        goal.request.group_name = "robotiq_gripper"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2

        from moveit_msgs.msg import RobotState
        from sensor_msgs.msg import JointState

        joint_state = JointState()
        joint_state.name = ['robotiq_85_left_knuckle_joint']



        joint_positions = [0.0]
        joint_state.position = joint_positions

        robot_state = RobotState()
        robot_state.joint_state = joint_state

        goal.request.goal_constraints.append(
            self.joint_state_to_constraints(joint_state)
        )
        goal.planning_options.plan_only = False

        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(
                lambda r: self.on_goal_result(
                    r,
                    lambda n: self.open_gripper(callback, n),
                    callback,
                    retries_left,
                )
            )
        )
    def close_gripper(self, callback, retries_left=5):
        self.get_logger().info('Closing gripper...')
        goal = MoveGroup.Goal()
        goal.request.group_name = "robotiq_gripper"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.2
        goal.request.max_acceleration_scaling_factor = 0.2

        from moveit_msgs.msg import RobotState
        from sensor_msgs.msg import JointState

        joint_state = JointState()
        joint_state.name = ['robotiq_85_left_knuckle_joint']

        joint_positions = [0.8]
        joint_state.position = joint_positions

        robot_state = RobotState()
        robot_state.joint_state = joint_state

        goal.request.goal_constraints.append(
            self.joint_state_to_constraints(joint_state)
        )
        goal.planning_options.plan_only = False

        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(
                lambda r: self.on_goal_result(
                    r,
                    lambda n: self.close_gripper(callback, n),
                    callback,
                    retries_left,
                )
            )
        )

    def on_goal_result(self, result_future, resend, callback, retries_left):
        error_code = result_future.result().result.error_code.val
        self.get_logger().info(f'Error code: {error_code}')
        if error_code == 1:
            callback()
            return
        if retries_left > 0:
            self.get_logger().info(f'Real failure (error {error_code}) — retrying ({retries_left} left)...')
            resend(retries_left - 1)
            return
        self.get_logger().error(f'Giving up after retries exhausted (last error {error_code}). Stopping.')
        rclpy.shutdown()

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
        detached.link_name = "tool0"
        detached.object.id = "target_cube"
        detached.object.operation = CollisionObject.REMOVE
        self._attach_pub.publish(detached)
        self.get_logger().info('Detached any previously-attached cube')

    def add_cube(self):
        cube = CollisionObject()
        cube.header.frame_id = "base_link"
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
        self.get_logger().info(f'Cube added at ({self.cube_x:.3f}, {self.cube_y:.3f}, {self.cube_z:.3f})')

    def attach_cube(self, callback):
        self.get_logger().info('Attaching cube to gripper...')
        attached = AttachedCollisionObject()
        attached.link_name = "tool0"
        attached.object.header.frame_id = "base_link"
        attached.object.id = "target_cube"
        attached.object.operation = CollisionObject.ADD
        attached.touch_links = [
            "tool0",
            "robotiq_85_left_finger_link", "robotiq_85_right_finger_link",
            "robotiq_85_left_finger_tip_link", "robotiq_85_right_finger_tip_link",
            "robotiq_85_left_knuckle_link", "robotiq_85_right_knuckle_link",
            "robotiq_85_left_inner_knuckle_link", "robotiq_85_right_inner_knuckle_link",
        ]
        self._attach_pub.publish(attached)
        # Attaching (with touch_links) is what tells the collision checker
        # to stop treating gripper-vs-cube contact as a collision, so this
        # must happen before closing the gripper, not after.
        time.sleep(0.5)  # let the planning scene monitor process the attach
        callback()

    def move_up(self):
        self.get_logger().info('Moving up with cube...')
        self.send_cartesian_goal(self.cube_x, self.cube_y, 0.5, self.move_to_place_above)

    def move_to_place_above(self):
        self.get_logger().info('Moving to place location...')
        self.send_cartesian_goal(0.4, 0.3, 0.5, self.move_to_place)

    def move_to_place(self):
        self.get_logger().info('Lowering to place location...')
        # Same fingertip-height offset as the grasp descent
        self.send_cartesian_goal(0.4, 0.3, 0.36, self.release_cube)

    def release_cube(self):
        self.get_logger().info('Releasing cube...')
        # Open first, while the cube is still attached (its touch_links
        # exception still applies) — the same reason attach happens before
        # close on the pick side. Detach only after the fingers have
        # cleared, so there's no gripper-vs-cube contact left to trip
        # CheckStartStateCollision.
        self.open_gripper(self.finish_release)

    def finish_release(self):
        self.detach_cube()
        time.sleep(0.5)  # let the planning scene monitor process the detach
        self.retreat()

    def retreat(self):
        self.get_logger().info('Retreating...')
        self.send_cartesian_goal(0.4, 0.3, 0.5, self.done)

    def move_above_cube(self):
        self.get_logger().info('Moving above cube...')
        self.send_cartesian_goal(self.cube_x, self.cube_y, self.cube_z + 0.15, self.move_to_cube)

    def move_to_cube(self):
        self.get_logger().info('Moving to cube...')
        # tool0 is the wrist flange, not the fingertips — the Robotiq
        # gripper's reach is estimated at ~0.16m beyond tool0 (spec-based
        # guess, not measured — tune empirically once tested), so offset
        # the target to land the fingertips at the cube's center
        self.send_cartesian_goal(self.cube_x, self.cube_y, self.cube_z + 0.16, lambda: self.attach_cube(lambda: self.close_gripper(self.move_up)))

    def done(self):
        self.get_logger().info('Pick and place complete!')
        rclpy.shutdown()

    def send_cartesian_goal(self, x, y, z, callback, retries_left=5):
        goal = MoveGroup.Goal()
        goal.request.group_name = "ur_manipulator"
        goal.request.num_planning_attempts = 20
        goal.request.allowed_planning_time = 10.0
        goal.request.max_velocity_scaling_factor = 0.1
        goal.request.max_acceleration_scaling_factor = 0.1

        target = PoseStamped()
        target.header.frame_id = "base_link"
        target.pose.position.x = x
        target.pose.position.y = y
        target.pose.position.z = z
        # Point the gripper straight down (180 deg flip about X)
        target.pose.orientation.x = 1.0
        target.pose.orientation.y = 0.0
        target.pose.orientation.z = 0.0
        target.pose.orientation.w = 0.0

        pc = PositionConstraint()
        pc.header.frame_id = "base_link"
        pc.link_name = "tool0"
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.SPHERE
        primitive.dimensions = [0.01]
        pc.constraint_region.primitives.append(primitive)
        pc.constraint_region.primitive_poses.append(target.pose)
        pc.weight = 1.0

        oc = OrientationConstraint()
        oc.header.frame_id = "base_link"
        oc.link_name = "tool0"
        oc.orientation = target.pose.orientation
        # Loose (0.3 rad ~ 17deg) tolerance lets the planner consider wrist
        # rotations that spin the gripper into upper_arm_link - tightened to
        # cut down on self-colliding candidate orientations (same fix
        # validated earlier in this project for the same collision pair).
        oc.absolute_x_axis_tolerance = 0.15
        oc.absolute_y_axis_tolerance = 0.15
        oc.absolute_z_axis_tolerance = 0.15
        oc.weight = 1.0

        constraints = Constraints()
        constraints.position_constraints.append(pc)
        constraints.orientation_constraints.append(oc)
        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = False

        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: f.result().get_result_async().add_done_callback(
                lambda r: self.on_goal_result(
                    r,
                    lambda n: self.send_cartesian_goal(x, y, z, callback, n),
                    callback,
                    retries_left,
                )
            )
        )

def main():
    rclpy.init()
    node = PickPlace()
    if rclpy.ok():
        rclpy.spin(node)

if __name__ == '__main__':
    main()