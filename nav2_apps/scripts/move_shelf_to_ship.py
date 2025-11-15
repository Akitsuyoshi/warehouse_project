#! /usr/bin/env python3

import time
from copy import deepcopy

from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
import rclpy

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

positions = {
    "init": [-0.10, -0.015, 0.0, 0.0],
    "loading": [5.5, -0.015, -0.7071, 0.7071],
    "shipping": [2.4, 1.15, 0.7071, 0.7071],
}

def create_pose(position, navigator):
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = positions[position][0]
    pose.pose.position.y = positions[position][1]
    pose.pose.orientation.z = positions[position][2]
    pose.pose.orientation.w = positions[position][3]
    return pose

def move_to_pose(pose, navigator, position):
    navigator.goToPose(pose)
    result = navigator.getResult()

    if result == TaskResult.SUCCEEDED:
        print(f"Arrived {position}")
    elif result == TaskResult.CANCELED:
        print(f"Canceled to {position}")
        return False
    elif result == TaskResult.FAILED:
        print(f"Failed to {position}")
        return False
    return True

def main():
    rclpy.init()
    navigator = BasicNavigator()

    # Set init pose
    init_pose = create_pose("init", navigator)
    navigator.setInitialPose(init_pose)

    navigator.waitUntilNav2Active()

    stages = ["loading", "shipping", "init"]
    for stage in stages:
        print(f"Moving to {stage}")
        pose = create_pose(stage, navigator)
        if not move_to_pose(pose, navigator, stage):
            print("Error moving to the next stage. Exiting.")
            exit(-1)
        while not navigator.isTaskComplete():
            pass
    print("Completed all stages. Exiting")
    exit(0)


if __name__ == "__main__":
    main()