import asyncio
import omni.kit.app
import numpy as np
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.types import ArticulationAction

async def move():
    robot = SingleArticulation(prim_path="/World/franka", name="franka_move")
    robot.initialize()
    
    start = robot.get_joint_positions()
    target = start.copy()
    target[0] = 0.8
    target[1] = -0.8
    target[2] = -0.6

    steps = 100
    for i in range(steps):
        alpha = i / (steps - 1)
        alpha_smooth = 0.5 * (1 - np.cos(np.pi * alpha))
        q = start + alpha_smooth * (target - start)
        robot.apply_action(ArticulationAction(joint_positions=q))
        await omni.kit.app.get_app().next_update_async()

    print("Done moving!")

asyncio.ensure_future(move())