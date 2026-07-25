import random

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformBroadcaster, TransformListener, StaticTransformBroadcaster
from tf2_geometry_msgs import do_transform_pose
from geometry_msgs.msg import TransformStamped, Pose


class MockTagDetector(Node):
    """
    Stands in for apriltag_ros until a real camera is wired up.

    Publishes the same TF structure a real detection would:
    a fixed panda_link0 -> camera_link mount transform, and a live
    camera_link -> target_cube transform (the "detection"). Downstream
    code only ever does a TF lookup for target_cube, so swapping this
    node for the real apriltag_ros node later requires no other changes.
    """

    def __init__(self):
        super().__init__('mock_tag_detector')

        self._static_broadcaster = StaticTransformBroadcaster(self)
        self._broadcaster = TransformBroadcaster(self)
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        # Ground-truth cube pose in panda_link0 - what a real camera would see
        self.cube_pose = Pose()
        self.cube_pose.position.x = 0.4
        self.cube_pose.position.y = 0.0
        self.cube_pose.position.z = 0.2
        self.cube_pose.orientation.w = 1.0

        self.publish_static_camera_transform()
        self.timer = self.create_timer(0.1, self.publish_mock_detection)

    def publish_static_camera_transform(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'panda_link0'
        t.child_frame_id = 'camera_link'
        # Fixed overhead mount, 1m above the workspace center
        t.transform.translation.x = 0.4
        t.transform.translation.y = 0.0
        t.transform.translation.z = 1.0
        # Looking straight down (180 deg flip about X, same convention as
        # the gripper's downward-facing grasp orientation)
        t.transform.rotation.x = 1.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 0.0
        self._static_broadcaster.sendTransform(t)
        self.get_logger().info('Published static camera mount transform')

    def publish_mock_detection(self):
        try:
            base_to_camera = self._tf_buffer.lookup_transform(
                'camera_link', 'panda_link0', Time()
            )
        except Exception:
            self.get_logger().warn('Waiting for TF...', throttle_duration_sec=2.0)
            return

        noisy_pose = Pose()
        noisy_pose.position.x = self.cube_pose.position.x + random.gauss(0, 0.002)
        noisy_pose.position.y = self.cube_pose.position.y + random.gauss(0, 0.002)
        noisy_pose.position.z = self.cube_pose.position.z + random.gauss(0, 0.002)
        noisy_pose.orientation = self.cube_pose.orientation

        pose_in_camera = do_transform_pose(noisy_pose, base_to_camera)

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'camera_link'
        t.child_frame_id = 'target_cube'
        t.transform.translation.x = pose_in_camera.position.x
        t.transform.translation.y = pose_in_camera.position.y
        t.transform.translation.z = pose_in_camera.position.z
        t.transform.rotation = pose_in_camera.orientation
        self._broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = MockTagDetector()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
