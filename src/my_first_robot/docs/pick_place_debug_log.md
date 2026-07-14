# Debug Log: pick_place.py — PLANNING_FAILED (-2)

## Symptom
Running `ros2 run my_first_robot pick_place` added the cube successfully, but the
motion goal always returned `Error code: -2` (PLANNING_FAILED). In RViz, the arm
visibly contorted itself — twisting up and away — instead of reaching down toward
the cube.

## Root Cause
The goal pose set an **identity quaternion** for `panda_hand`:
```python
target.pose.orientation.w = 1.0   # x=y=z=0 (identity)
```
Identity orientation means "align the hand's local Z-axis with the world's Z-axis" —
i.e. the palm/fingers pointing straight **up**, away from the table. To satisfy a
position goal at `(0.4, 0.0, 0.35)` *with* that upward-facing orientation, the arm
had to twist into an awkward, largely unreachable configuration. Combined with a
fairly tight orientation tolerance (`0.1` rad ≈ 5.7°), the planner couldn't find a
valid collision-free IK solution within the allowed planning attempts.

## Fix
1. **Flip the target orientation 180° about X** so the hand points down at the cube
   instead of up:
   ```python
   target.pose.orientation.x = 1.0
   target.pose.orientation.y = 0.0
   target.pose.orientation.z = 0.0
   target.pose.orientation.w = 0.0
   ```
2. **Loosened the orientation tolerance** from `0.1` to `0.3` rad on all axes, since
   a perfectly flat top-down approach isn't required for a simple grasp.

## Result
`Error code: 1` (SUCCESS). The arm now moves cleanly above the cube with the hand
facing down, ready for a grasp approach.

## Takeaway
When a MoveIt goal fails to plan and the arm looks like it's fighting itself in
RViz, check the **orientation constraint** first — a wrong reference orientation
(especially identity/default quaternions) is a very common cause, more often than
tolerances or reachability being the true issue.

## Next Steps (pick_place pipeline)
- Add a pre-grasp approach waypoint (slightly above final grasp height) and a
  Cartesian descent onto the cube.
- Add gripper close/open calls (reuse `gripper_service`/`gripper_service_client`).
- Add a retreat/lift waypoint after grasping.
- Eventually replace the hardcoded cube pose with real perception input.
