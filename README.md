# Robotics Learning Roadmap — ROS2 Pick & Place from Zero

This branch is my **fresh-start practice branch**: I rebuild the Franka
pick-and-place pipeline (ROS2 Jazzy · MoveIt2 · Isaac Sim · AprilTag
perception) from blank files, using the finished version on `master` only
as a last-resort reference. This README is both the **setup guide**
(rebuild the environment from a blank machine) and the **learning plan**
(rebuild the *skills* from scratch).

**The target:** be able to design, build, and debug a robot-arm
manipulation pipeline independently — and explain every layer of it in an
interview.

---

## Part 1 — Environment setup from a blank machine

Stack: Ubuntu 24.04 (Noble) · ROS2 **Jazzy** · MoveIt2 · apriltag_ros · Isaac Sim.

### 1. Install ROS2 Jazzy

Follow the official guide (deb packages): https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

```bash
# Enable required repos and keys (see the guide), then:
sudo apt install ros-jazzy-desktop        # ROS2 + RViz + demos
sudo apt install ros-dev-tools            # colcon, rosdep, vcstool

# Source it in every shell (add to ~/.bashrc):
source /opt/ros/jazzy/setup.bash
```

Verify: `ros2 run demo_nodes_cpp talker` in one terminal,
`ros2 run demo_nodes_py listener` in another. If the listener prints
messages, ROS2 works.

### 2. Install MoveIt2 and perception packages

```bash
sudo apt install ros-jazzy-moveit                 # MoveIt2 full stack
sudo apt install ros-jazzy-apriltag-ros           # AprilTag detector node
sudo apt install ros-jazzy-tf-transformations     # quaternion helpers (python)
```

### 3. Get the robot description

The Franka URDF/meshes come from the official repo (kept in `src/`,
untracked on this branch):

```bash
cd ~/ros2_ws/src
git clone https://github.com/frankaemika/franka_description.git
```

### 4. Create the workspace and build

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
# create packages inside src/, then:
rosdep install --from-paths src --ignore-src -r -y   # pull package deps
colcon build --symlink-install
source install/setup.bash                            # every new terminal
```

Key habit: **`source install/setup.bash` after every build, in every
terminal.** Half of all "node not found" errors are a missed source.

### 5. Isaac Sim (simulation)

Installed at `~/isaacsim` (with `~/IsaacLab`). Isaac Sim provides the
simulated Franka + camera and the ROS2 bridge.
Install guide: https://docs.isaacsim.omniverse.nvidia.com/latest/installation/

---

## Part 2 — The learning path (in dependency order)

Each stage lists the concept, where the finished reference lives on
`master`, and the "can I?" test. Don't move on until the test passes
**from a blank file**.

### Stage 1 — ROS2 communication primitives

| Concept | Reference on `master` | "Can I?" test |
|---|---|---|
| Publisher / Subscriber | `my_first_robot/publisher.py`, `subscriber.py` | Write a talker/listener pair from a blank file, no references |
| Services | `gripper_service.py`, `gripper_service_client.py` | Explain when to use a service vs a topic; why `call()` in a spinning node deadlocks |
| Actions | `move_action_server.py`, `move_action_client.py` | Name the 3 parts of an action definition; explain why MoveIt uses actions |

CLI fluency to drill alongside: `ros2 topic list/echo/info -v`,
`ros2 service call`, `ros2 action send_goal`, `ros2 node list/info`,
`rqt_graph`.

### Stage 2 — Robot description, TF, and launch

| Concept | Reference on `master` | "Can I?" test |
|---|---|---|
| URDF / Xacro | `src/franka_description/` | Sketch the link/joint tree; explain fixed vs revolute; what `robot_state_publisher` publishes |
| TF2 frames | (used throughout) | Run `ros2 run tf2_tools view_frames`; explain how a pose moves between frames |
| Launch files | `launch/robot.launch.py`, `launch/apriltag.launch.py` | Write a launch file starting 2 nodes with parameters, from blank |

### Stage 3 — MoveIt2 motion planning

| Concept | Reference on `master` | "Can I?" test |
|---|---|---|
| Joint & pose goals | `moveit_commander.py` | Explain what `move_group` does; planning group; goal tolerances |
| Cartesian paths | `moveit_cartesian.py` | Explain cartesian vs free-space planning; what "fraction" means |
| Planning scene | pick/place files below | Explain collision objects and why the cube must be attached, not just gripped |

### Stage 4 — The full pipeline

| Concept | Reference on `master` | "Can I?" test |
|---|---|---|
| Pick & place state machine | `pick_place.py`, `pick_place_second.py` | Whiteboard the full sequence approach→grasp→attach→lift→place→detach and every ROS interface it crosses |
| Perception → grasp target | `mock_tag_detector.py`, `subscriber_cube.py` | Trace a pose from detection frame to planning frame; explain the tilted-attach bug and its fix (commit `b5f4e81`) |

My own debugging history — the highest-value revision material, on the
feature branches: `docs/pick_place_debug_log.md`,
`docs/pick_place_second_debug_log.md`.

---

## Part 3 — How to revise (the method, not just the material)

The first build of this project was AI-assisted: I prompted, reviewed, and
applied. That builds **recognition** ("this looks right") but not
**recall** ("I can produce this on a blank line"). The fix is retrieval
practice:

1. **Produce first, ask second.** Attempt every exercise on a blank file
   before opening the old code or asking the AI. The struggle IS the
   learning; feedback afterwards is just error-correction.
2. **The hint ladder** when stuck: ask for the *concept* → the *rough
   shape* → *pseudocode* → a snippet only after a failed real attempt.
   Never copy-paste; read, close, retype from memory.
3. **20-minute rule.** Before asking anything: read the full error, guess
   which layer it's in (my code / topic wiring / MoveIt / sim), test the
   guess with CLI tools. Then ask "I think X because Y — am I right?"
4. **Predict before running.** Say out loud what a command will print
   before hitting enter. Wrong predictions are the best data.
5. **Explain after each milestone.** 2–3 written sentences: what I built,
   why this interface, what broke. Can't write it → that's the gap.

## Part 4 — The capstone: rebuild on this branch

Rebuild the whole pipeline here, in a **new package**, under these rules:

- Blank files. Official docs and Google fully allowed (that's real
  engineering). `master` only after a failed attempt — and copy nothing I
  can't explain.
- AI in tutor mode only: hints, code review of *my* attempts, error
  explanation. No generated implementations.
- Build order = Stage 1 → 4 above:
  1. pub/sub warm-up node
  2. gripper service + client
  3. launch file bringing up robot + MoveIt
  4. joint-space goal, then pose goal, then cartesian path
  5. full pick-and-place against a mock tag detector
  6. (stretch) swap the mock for real `apriltag_ros` detection from the
     Isaac Sim camera

**Done means:** the cube moves, and I can explain every file, every
interface choice, and reproduce the demo from a fresh terminal without
looking anything up except API signatures.

## Part 5 — Milestones toward the target

- [ ] Stage 1 tests pass from blank files
- [ ] Stage 2: launch + URDF understood, TF tree drawn from memory
- [ ] Stage 3: can command the arm to a pose goal written solo
- [ ] Capstone rebuild complete under the rules above
- [ ] README/docs polished — repo tells the story (great for interviews)
- [ ] Can whiteboard the full system + narrate 2 debugging war stories
      (tilted attach, and one from the debug logs) without notes
- [ ] Stretch: real AprilTag perception loop closed in Isaac Sim
