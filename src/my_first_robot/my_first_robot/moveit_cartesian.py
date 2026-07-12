import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
from geometry_msgs.msg import PoseStamped
from shape_msgs.msg import SolidPrimitive

class CartesianCommander(Node):
    def __init__(self):
        super().__init__('cartesian_commander')
        self._action_client = ActionClient(self, MoveGroup, 'move_action')
        self.get_logger().info('Waiting for MoveGroup...')
        self._action_client.wait_for_server()
        self.get_logger().info('Connected!')
        self.send_goal()

    def send_goal(self):
        goal = MoveGroup.Goal()
        goal.request.group_name = "panda_arm"
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.1
        goal.request.max_acceleration_scaling_factor = 0.1

        target = PoseStamped()
        target.header.frame_id = "panda_link0"
        target.pose.position.x = 0.4
        target.pose.position.y = 0.1
        target.pose.position.z = 0.5
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
        oc.absolute_x_axis_tolerance = 0.1
        oc.absolute_y_axis_tolerance = 0.1
        oc.absolute_z_axis_tolerance = 0.1
        oc.weight = 1.0

        constraints = Constraints()
        constraints.position_constraints.append(pc)
        constraints.orientation_constraints.append(oc)
        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = False

        self.get_logger().info('Sending Cartesian goal (0.4, 0.1, 0.5)...')
        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        self.get_logger().info('Goal accepted — planning and executing...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Done! Error code: {result.error_code.val}')
        rclpy.shutdown()

def main():
    rclpy.init()
    node = CartesianCommander()
    rclpy.spin(node)

if __name__ == '__main__':
    main()