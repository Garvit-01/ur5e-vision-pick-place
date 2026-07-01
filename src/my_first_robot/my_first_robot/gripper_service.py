import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class GripperService(Node):
    def __init__(self):
        super().__init__('gripper_service')
        self.serv = self.create_service(SetBool,'gripper_control',self.handle_gripper)
        self.get_logger().info('Gripper service is ready')

    
    def handle_gripper(self,request,response):
        if request.data:
            self.get_logger().info('Gripper:Closing')
            response.success = True
            response.message = 'Gripper closed'
        
        else:
            self.get_logger().info('Gripper:Opening')
            response.success = True
            response.message = 'Gripper Opened'

        return response
    
def main():
    rclpy.init()
    node = GripperService()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
