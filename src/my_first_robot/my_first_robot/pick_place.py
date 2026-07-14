import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
from moveit_msgs.msg import CollisionObject
from geometry_msgs.msg import PoseStamped, Pose
from shape_msgs.msg import SolidPrimitive
from std_msgs.msg import Header

class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place')
        
        # Action client for motion planning
        self._action_client = ActionClient(self, MoveGroup, 'move_action')
        
        # Publisher to add objects to planning scene
        self._scene_pub = self.create_publisher(
            CollisionObject, 
            'collision_object', 
            10
        )
        
        self.get_logger().info('Waiting for MoveGroup...')
        self._action_client.wait_for_server()
        self.get_logger().info('Connected!')
        
        # Step 1: Add cube to scene
        self.add_cube()
        
        # Wait for scene to update
        import time
        time.sleep(1.0)
        
        # Step 2: Move to cube
        self.move_to_cube()

    def add_cube(self):
        cube = CollisionObject()
        cube.header.frame_id = "panda_link0"
        cube.id = "target_cube"
        
        shape = SolidPrimitive()
        shape.type = SolidPrimitive.BOX
        shape.dimensions = [0.05, 0.05, 0.05]  # 5cm cube
        
        pose = Pose()
        pose.position.x = 0.4
        pose.position.y = 0.0
        pose.position.z = 0.2
        pose.orientation.w = 1.0
        
        cube.primitives.append(shape)
        cube.primitive_poses.append(pose)
        cube.operation = CollisionObject.ADD
        
        self._scene_pub.publish(cube)
        self.get_logger().info('Cube added to scene at (0.4, 0.0, 0.2)')

    def move_to_cube(self):
        goal = MoveGroup.Goal()
        goal.request.group_name = "panda_arm"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.1
        goal.request.max_acceleration_scaling_factor = 0.1

        # Move to position above cube
        target = PoseStamped()
        target.header.frame_id = "panda_link0"
        target.pose.position.x = 0.4
        target.pose.position.y = 0.0
        target.pose.position.z = 0.35  # Above the cube
        # Point the gripper straight down at the cube (180 deg flip about X)
        target.pose.orientation.x = 1.0
        target.pose.orientation.y = 0.0
        target.pose.orientation.z = 0.0
        target.pose.orientation.w = 0.0

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
        oc.absolute_x_axis_tolerance = 0.3
        oc.absolute_y_axis_tolerance = 0.3
        oc.absolute_z_axis_tolerance = 0.3
        oc.weight = 1.0

        constraints = Constraints()
        constraints.position_constraints.append(pc)
        constraints.orientation_constraints.append(oc)
        goal.request.goal_constraints.append(constraints)
        goal.planning_options.plan_only = False

        self.get_logger().info('Moving to cube position...')
        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        self.get_logger().info('Goal accepted — moving...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Done! Error code: {result.error_code.val}')
        rclpy.shutdown()

def main():
    rclpy.init()
    node = PickPlace()
    rclpy.spin(node)

if __name__ == '__main__':
    main()