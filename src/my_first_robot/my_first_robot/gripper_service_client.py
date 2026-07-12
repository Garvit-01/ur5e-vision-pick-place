import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class GripperClinet(Node):
    def __init__(self):
        super().__init__('gripper_client')
        self.client = self.create_client(SetBool,'gripper_control')

        # wait service to become available

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for the gripper service....")

        
        self.get_logger().info("Service Found!")


    def send_request(self,close_gripper:bool):
        request = SetBool.Request()
        request.data = close_gripper
        future = self.client.call_async(request)
        return future
    

def main():
    rclpy.init()
    node = GripperClinet()

    future = node.send_request(False)
    rclpy.spin_until_future_complete(node,future)
    print(f"Response: {future.result().message}")
    rclpy.shutdown()

if __name__ == '__main__':
    main()
