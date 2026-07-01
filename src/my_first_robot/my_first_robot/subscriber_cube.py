import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Point

class HelloSubscriber(Node):

    def __init__(self):
        super().__init__('hello_subscriber')

        self.subscription = self.create_subscription(
            Point,
            'cube_pose',
            self.listener_callback,
            10
        )

    def listener_callback(self, msg):
        self.get_logger().info(f"Cube is at the position x = {msg.x}, y = {msg.y}, z = {msg.z}")


def main():
    rclpy.init()

    node = HelloSubscriber()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()