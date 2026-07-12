import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import String


class HelloPublisher(Node):

    def __init__(self):
        super().__init__('hello_publisher')

        self.publisher_ = self.create_publisher(
            Point,
            'cube_pose',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_message
        )

    def publish_message(self):

        msg = Point()
        msg.x = 1.2
        msg.y = 0.2
        msg.z = 0.3

        self.publisher_.publish(msg)

        self.get_logger().info(
            f"Publishing: {msg}"
        )


def main():

    rclpy.init()

    node = HelloPublisher()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()