import rclpy
from rclpy.node import Node
from moveit.planning import MoveItPy

def main():
    rclpy.init()
    
    # Initialize MoveIt2
    moveit = MoveItPy(node_name="moveit_commander")
    arm = moveit.get_planning_component("panda_arm")
    
    print("MoveIt2 ready")
    
    # Set goal to named position "ready"
    arm.set_goal_state(configuration_name="ready")
    
    # Plan
    plan = arm.plan()
    
    if plan:
        print("Plan found — executing...")
        moveit.execute(plan.trajectory, controllers=[])
        print("Done!")
    else:
        print("Planning failed")
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()