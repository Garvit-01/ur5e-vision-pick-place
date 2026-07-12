import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, WorkspaceParameters, Constraints, JointConstraint
from shape_msgs.msg import SolidPrimitive

class MoveItCommander(Node):
    def __init__(self):
        super().__init__('moveit_commander')
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

        # Set joint target (ready position)
        joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        joint_positions = [1.0, -0.5, 0.0, -2.0, 0.0, 1.5, 0.0]



        constraints = Constraints()
        for name, position in zip(joint_names, joint_positions):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = position
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        goal.request.goal_constraints.append(constraints)

        self.get_logger().info('Sending motion goal...')
        goal.planning_options.plan_only = False
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
    node = MoveItCommander()
    rclpy.spin(node)

if __name__ == '__main__':
    main()