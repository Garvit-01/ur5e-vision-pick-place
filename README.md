# ros2_ws

ROS2 Jazzy workspace for a robotics portfolio: pick-and-place manipulation
on two different robots, progressing from hardcoded object positions to
real camera-based perception.

## Packages

- **`my_first_robot`** — the main package. Contains all pick-and-place
  scripts, the combined UR5e+Robotiq URDF, and the real-perception
  launch/config files.
- **`ur5e_robotiq_moveit_config`** — MoveIt2 configuration (SRDF,
  controllers, kinematics) for the custom UR5e + Robotiq 2F-85 gripper
  robot, generated via MoveIt Setup Assistant and hand-tuned. No
  ready-made package for this exact robot combination exists upstream —
  this was built from scratch (see `docs_local/UR5e_Robotiq_Integration.md`
  for the full build log, local-only, not pushed to GitHub).
- **`franka_description`** — upstream Franka Emika package, used by the
  earlier Panda pick-and-place work (see `pick_place.py`,
  `pick_place_second.py` — not part of the UR5e demo below).

## This branch: UR5e + Robotiq with real camera perception

The pick-and-place script (`ur5e_pick_place_second.py`) picks up a cube
using a position computed by a real camera and real AprilTag detection
software — not a hardcoded coordinate. The camera is simulated in Isaac
Sim, but the detection software (`apriltag_ros`) and the actual robot
motion planning (MoveIt/RViz) are the same as they'd be with real
hardware.

### Key files

| File | What it does |
|---|---|
| `my_first_robot/my_first_robot/ur5e_pick_place_second.py` | The pick-and-place script. Looks up the cube's real position via TF (`lookup_cube_pose`), then runs home → open gripper → approach → grasp → lift → place → release → retreat. |
| `my_first_robot/launch/apriltag.launch.py` | Launches `apriltag_ros`'s detector node (configured for our camera topics) plus a static transform publishing the camera's fixed mount pose (`base_link → camera_link`). |
| `my_first_robot/config/tags_36h11_target_cube.yaml` | Tells `apriltag_ros` which tag to look for (family `36h11`, ID `0`), its real physical size (5cm), and to publish the detected frame as `target_cube` directly. |
| `my_first_robot/urdf/ur5e_robotiq.urdf.xacro` | The combined UR5e arm + Robotiq gripper robot description. |
| `my_first_robot/isaac-sim-scripts/` | OmniGraph setup scripts, pasted into Isaac Sim's own Script Editor (not run as ROS nodes) to wire up ROS2 publishing for the camera. |
| `ur5e_robotiq_moveit_config/launch/demo.launch.py` | Brings up `move_group`, RViz, and the controllers for the combined robot. |

### How to run the full demo

Needs **four** things running at once — Isaac Sim, plus three terminals.

**1. Isaac Sim** (GUI app, `~/isaacsim/isaac-sim.sh`):
- Open the scene with the camera and tagged cube.
- Press **Play** on the timeline — the camera only publishes while playing.

**2. Terminal 1 — MoveIt/RViz for the robot:**
```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch ur5e_robotiq_moveit_config demo.launch.py
```
Wait for RViz to fully load before continuing.

**3. Terminal 2 — real AprilTag detector + camera mount transform:**
```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch my_first_robot apriltag.launch.py
```

**4. Terminal 3 — the pick-and-place script:**
```bash
cd ~/ros2_ws
source install/setup.bash
ros2 run my_first_robot ur5e_pick_place_second
```

Watch RViz — the script logs `Detected cube at (x, y, z)` with the real
computed position, then runs the full pick-and-place sequence.

### Rebuilding after any code change
```bash
cd ~/ros2_ws
colcon build --packages-select my_first_robot
```
(swap the package name if editing `ur5e_robotiq_moveit_config` instead —
config-only packages rebuild in under a second).

## Other scripts in `my_first_robot` (not part of the UR5e demo)

Earlier/exploratory work, kept for reference:
- `pick_place.py`, `pick_place_second.py` — Franka Panda pick-and-place
  (the `feature/apriltag-perception` branch extends this with a *mocked*
  camera detector, `mock_tag_detector.py`, predating the real perception
  work on this branch).
- `ur5e_moveit_commander.py`, `ur5e_moveit_cartesian.py` — early UR5e
  arm-only motion tests (joint-space and Cartesian), before the Robotiq
  gripper was added.
- `publisher.py`, `subscriber.py`, `publisher_cube.py`, `subscriber_cube.py`,
  `gripper_service.py`, `gripper_service_client.py`, `move_action_server.py`,
  `move_action_client.py` — ROS2 fundamentals practice (topics, services,
  actions), not part of any pick-and-place pipeline.
