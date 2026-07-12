import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from control_msgs.action import FollowJointTrajectory
import time

class MoveActionServer(Node):
    def __init__(self):
        super().__init__('move_action_server')
        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            'move_arm',
            self.execute_callback
        )
        self.get_logger().info('Move action server ready')

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Moving arm...')
        
        # Send feedback every 0.5 seconds (simulating arm movement)
        for i in range(5):
            feedback = FollowJointTrajectory.Feedback()
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(f'Progress: {(i+1)*20}%')
            time.sleep(0.5)
        
        goal_handle.succeed()
        result = FollowJointTrajectory.Result()
        return result

def main():
    rclpy.init()
    node = MoveActionServer()
    rclpy.spin(node)

if __name__ == '__main__':
    main()