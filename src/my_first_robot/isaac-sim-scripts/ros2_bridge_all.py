import omni.graph.core as og

FRANKA_PRIM_PATH = "/World/franka"
keys = og.Controller.Keys

# Joint states
og.Controller.edit(
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

# TF
og.Controller.edit(
    {"graph_path": "/World/ROS2TFGraph", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("OnTick", "omni.graph.action.OnPlaybackTick"),
            ("PublishTF", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),
        ],
        keys.CONNECT: [
            ("OnTick.outputs:tick", "PublishTF.inputs:execIn"),
        ],
        keys.SET_VALUES: [
            ("PublishTF.inputs:targetPrims", [FRANKA_PRIM_PATH]),
        ],
    },
)

# Clock
og.Controller.edit(
    {"graph_path": "/World/ROS2ClockGraph", "evaluator_name": "execution"},
    {
        keys.CREATE_NODES: [
            ("OnTick", "omni.graph.action.OnPlaybackTick"),
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
        ],
        keys.CONNECT: [
            ("OnTick.outputs:tick", "PublishClock.inputs:execIn"),
        ],
    },
)

print("All ROS2 graphs created successfully")