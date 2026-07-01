import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class HelloPublisher(Node):

    def __init__(self):
        super().__init__('hello_publisher')

        self.publisher_ = self.create_publisher(
            String,
            'greetings',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_message
        )

    def publish_message(self):

        msg = String()
        msg.data = "Robot is alive"

        self.publisher_.publish(msg)

        self.get_logger().info(
            f"Publishing: {msg.data}"
        )


def main():

    rclpy.init()

    node = HelloPublisher()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()