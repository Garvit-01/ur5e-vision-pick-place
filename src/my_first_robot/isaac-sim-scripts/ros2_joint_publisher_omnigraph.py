import omni.graph.core as og

FRANKA_PRIM_PATH = "/World/franka"

keys = og.Controller.Keys
(graph, nodes, _, _) = og.Controller.edit(
    {"graph_path": "/World/ROS2JointStateGraph", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("OnTick", "omni.graph.action.OnPlaybackTick"),
            ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
        ],
        keys.CONNECT: [
            ("OnTick.outputs:tick", "PublishJointState.inputs:execIn"),
        ],
        keys.SET_VALUES: [
            ("PublishJointState.inputs:targetPrim", FRANKA_PRIM_PATH),
            ("PublishJointState.inputs:topicName", "joint_states"),
        ],
    },
)
print("ROS2 bridge graph created:", graph)