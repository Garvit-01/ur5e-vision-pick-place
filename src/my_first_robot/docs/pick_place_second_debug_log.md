# Debug Log: pick_place_second.py — Full Pick Sequence

## Challenge 1: Racing action goals on startup

**Symptom:** Robot behavior looked inconsistent between runs; gripper appeared
to open twice.

**Root cause:** `__init__` called `self.open_gripper()` and `self.move_to_home()`
back-to-back. Both use `send_goal_async`, which returns immediately without
waiting for the motion to finish — so both fired as competing goals at once.
The arm could receive a "move to cube" goal while still mid-way through homing.

**Fix:** Removed the direct `open_gripper()` call from `__init__`. Now only
`move_to_home()` is called, and its own action-result callback triggers
`open_gripper()` — enforcing strict sequencing: home finishes **then** gripper
opens **then** the rest of the chain runs.

## Challenge 2: Cube didn't move with the gripper at all

**Symptom:** After "picking up" the cube, it stayed exactly where it was
originally placed — the arm moved, the cube didn't.

**Root cause:** A `CollisionObject` published to the planning scene is just a
static "world" object. Closing the gripper only commands joint positions; MoveIt
has no concept of "contact" or "grasp" here (no physics engine in this RViz
demo). Nothing tells the scene that the cube should now move with the hand.

**Fix:** Added `attach_cube()` — publishes an `AttachedCollisionObject` to
`/attached_collision_object` with `link_name="panda_hand"` and the same object
`id` as the world cube, plus `touch_links` for the hand/fingers (to allow
expected contact without flagging a collision). Wired it in right after
`close_gripper()`'s goal completes.

## Challenge 3: Cube attached, but looked "stuck to the back" of the gripper

**Symptom:** The attach worked (confirmed via RViz's Scene Objects tab showing
`target_cube` attached to `panda_hand`), and it did travel with the arm — but
visually it looked wrong, offset behind/beside the gripper instead of nested
between the fingers.

**Root cause:** `send_cartesian_goal()` still used the identity orientation
(`w=1.0`) with a loose ±0.5 rad tolerance — the same bug fixed earlier in
`pick_place.py` but never applied here. The planner was free to approach at any
tilted angle within tolerance, so whatever angle it happened to grasp at got
"frozen" into the attach transform.

**Fix:** Applied the same downward-facing quaternion fix
(`x=1, y=0, z=0, w=0`) and tightened tolerance to ±0.3 rad, so every approach
consistently points straight down.

## Challenge 4: Re-running left a stale cube attached from the previous run

**Symptom:** Running the node again didn't spawn a fresh cube on the ground —
the cube from the previous run, still attached to the gripper, just kept
riding along.

**Root cause:** No detach step existed anywhere. Re-publishing a `CollisionObject`
with `operation=ADD` and the same `id` doesn't override an object that's
currently *attached* to a link — attached and world objects are tracked
separately in the planning scene.

**Fix:** Added `detach_cube()` (publishes an `AttachedCollisionObject` with
`operation=REMOVE`), called once at the very start of `__init__`, before
`add_cube()`. Every run now starts by clearing any leftover attachment.

## Challenge 5: Gripper closed past the cube instead of around it

**Symptom:** Even with correct downward orientation, the cube still wasn't
sitting cleanly between the fingers — looked slightly too low / off-center.

**Root cause:** The code was commanding a position for `panda_hand`, which is
the wrist flange, not the actual pinch point between the fingers. Franka's own
description package defines a separate `hand_tcp` frame offset **0.1034m**
further along the gripper's approach axis specifically because of this
distinction (found by grepping `tcp_xyz` in `franka_description`'s xacro
files). At the old target height (`z=0.26`), the real fingertip position was
`0.26 - 0.1034 ≈ 0.157` — below the cube's bottom face (`0.175`) — so the
gripper was already reaching past the cube, not around it.

**Fix:** Raised the grasp target height to `0.303` (`cube center 0.2 +
tcp offset 0.1034`), so the *fingertips*, not the wrist, land at the cube's
actual height.

## Takeaways

- When a MoveIt goal plans/executes fine but the *visual result* looks wrong,
  suspect the constraint reference frame or the target link before assuming
  the planner did something wrong.
- "Attaching" an object in MoveIt is purely a bookkeeping operation (parent
  link + relative transform) — it says nothing about whether the geometry is
  physically correct at attach time. Garbage in (wrong orientation/height),
  garbage out (wrong-looking attach).
- Always check whether you're commanding a mounting/flange frame vs. the
  actual functional frame (fingertip, TCP, sensor origin) — this class of bug
  shows up constantly in manipulation and perception work.
- Async action chains need explicit sequencing (`callback → next call`), never
  "fire both and hope" — a recurring theme in this debugging session (see
  Challenge 1).
