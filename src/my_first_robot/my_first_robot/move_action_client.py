import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory

class MoveActionClient(Node):
    def __init__(self):
        super().__init__('move_action_client')
        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            'move_arm'
        )

    def send_goal(self):
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()
        
        goal = FollowJointTrajectory.Goal()
        
        self.get_logger().info('Sending goal...')
        future = self._action_client.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )
        future.add_done_callback(self.goal_response_callback)

    def feedback_callback(self, feedback):
        self.get_logger().info('Received feedback')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        self.get_logger().info('Goal accepted, moving...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        self.get_logger().info('Movement complete!')
        rclpy.shutdown()

def main():
    rclpy.init()
    node = MoveActionClient()
    node.send_goal()
    rclpy.spin(node)

if __name__ == '__main__':
    main()