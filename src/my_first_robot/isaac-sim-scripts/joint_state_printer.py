import asyncio
import omni.kit.app
import numpy as np
from isaacsim.core.api.world import World
from isaacsim.core.prims import SingleArticulation

async def publish_joint_states():
    world = World()
    await world.initialize_simulation_context_async()
    
    robot = SingleArticulation(prim_path="/World/franka", name="franka")
    world.scene.add(robot)
    await world.reset_async()
    robot.initialize()
    await world.play_async()

    print("Publishing joint states...")
    
    for _ in range(500):
        positions = robot.get_joint_positions()
        print(f"Joints: {np.round(positions, 3)}")
        await omni.kit.app.get_app().next_update_async()

asyncio.ensure_future(publish_joint_states())