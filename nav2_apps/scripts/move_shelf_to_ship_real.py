#! /usr/bin/env python3

import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from custom_interfaces.srv import GoToLoading
from rcl_interfaces.msg import Parameter, ParameterValue
from rcl_interfaces.msg import ParameterType
from rcl_interfaces.srv import SetParameters
from tf_transformations import euler_from_quaternion
from geometry_msgs.msg import Twist




positions = {
    "init": [-0.1, 0.0, 0.0, 1.0],
    "loading": [4.1, -0.9, -0.7071, 0.7071],
    "loading_2": [4.1, -0.9, 1.0, 0.0],
    "shipping": [1.6, 1.2, 0.7071, 0.7071],
    "shipping_2": [1.6, 0.0, 1.0, 0.0],
}

def create_pose(position, navigator, backward=0.0):
    x, y, z, w = positions[position]
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.orientation.x = 0.0
    pose.pose.orientation.y = 0.0
    pose.pose.orientation.z = z
    pose.pose.orientation.w = w

    _, _, yaw = euler_from_quaternion([0.0, 0.0, z, w])
    pose.pose.position.x = x - backward * math.cos(yaw)
    pose.pose.position.y = y - backward * math.sin(yaw)
    pose.pose.position.z = 0.0
    return pose

def move_to_pose(position, navigator, node, backward=0.0):
    pose = create_pose(position, navigator, backward)
    navigator.goToPose(pose)
    while not navigator.isTaskComplete():
        rclpy.spin_once(node, timeout_sec=0.1)

    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        node.get_logger().info(f"Arrived at {position}")
        return True
    node.get_logger().info(f"Failed to reach {position}")
    return False

def call_service(node, service_n):
    client = node.create_client(GoToLoading, service_n)
    node.get_logger().info("Waiting for /approach_shelf service...")

    if not client.wait_for_service(timeout_sec=5.0):
        node.get_logger().error("Service unavailable.")
        return False

    req = GoToLoading.Request()
    req.attach_to_shelf = True
    future = client.call_async(req)
    rclpy.spin_until_future_complete(node, future, timeout_sec=30.0)
    if not future.done():
        node.get_logger().error("Service timed out")
        return False
    if future.result():
        return future.result().complete
    return False


def update_float_parameters(node, params_dict, target_nodes=None):
    if target_nodes is None:
        target_nodes = [
            "/local_costmap/local_costmap",
            "/global_costmap/global_costmap",
        ]

    param_list = []
    for name, value in params_dict.items():
        param_list.append(
            Parameter(
                name=name,
                value=ParameterValue(
                    type=ParameterType.PARAMETER_DOUBLE,
                    double_value=float(value)
                )
            )
        )

    for target in target_nodes:
        client = node.create_client(SetParameters, f"{target}/set_parameters")

        if not client.wait_for_service(timeout_sec=5.0):
            node.get_logger().error(f"Cannot reach {target}/set_parameters")
            return False

        req = SetParameters.Request(parameters=param_list)
        future = client.call_async(req)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)

        if future.done():
            node.get_logger().info(f"Updated float params on {target}")
        else:
            node.get_logger().warn(f"Timeout updating {target}")

    return True


def drive_backward(node, duration=1.0, speed=-0.1):
    cmd_pub = node.create_publisher(Twist, "/cmd_vel", 10)
    twist = Twist()
    twist.linear.x = speed     # negative = backward

    end_time = node.get_clock().now().nanoseconds + duration * 1e9
    while node.get_clock().now().nanoseconds < end_time:
        cmd_pub.publish(twist)
        time.sleep(0.05)

    # stop
    cmd_pub.publish(Twist())

    
def main():
    rclpy.init()
    node = rclpy.create_node("robot_move_manager")
    navigator = BasicNavigator()

    # Set init pose
    navigator.setInitialPose(create_pose("init", navigator))
    navigator.waitUntilNav2Active()

    # init to loading
    if not move_to_pose("loading", navigator, node):
        sys.exit(1)
    
    # loading to under shelf
    if not call_service(node, "/approach_shelf"):
        sys.exit(1)
    
    # publish /elevator_up
    elevator_pub = node.create_publisher(String, "/elevator_up", 10)
    msg = String()
    msg.data = ""
    for _ in range(5):
        elevator_pub.publish(msg)
        time.sleep(0.1)
    node.get_logger().info("Published /elevator_up")
    time.sleep(3.0)

    # update controller server param, considering shelf size
    update_float_parameters(node, {
        "robot_radius": 0.55,
        "voxel_layer.obstacle_min_range": 0.55,
        "voxel_layer.raytrace_min_range": 0.55
    }, target_nodes=[
        "/local_costmap/local_costmap",
        "/global_costmap/global_costmap",
    ])

    drive_backward(node, duration=6.0, speed=-0.15)
    node.get_logger().info("Drive backward")

    # under shelf to loading
    if not move_to_pose("loading_2", navigator, node):
        sys.exit(1)
    
    # loading to shipping
    if not move_to_pose("shipping", navigator, node):
        sys.exit(1)
    
    # publish /elevator_down
    elevator_pub = node.create_publisher(String, "/elevator_down", 10)
    msg = String()
    msg.data = ""
    for _ in range(5):
        elevator_pub.publish(msg)
        time.sleep(0.1)
    node.get_logger().info("Published /elevator_down")
    time.sleep(3.0)

    # update controller server param to its original size
    update_float_parameters(node, {
        "robot_radius": 0.30,
        "voxel_layer.obstacle_min_range": 0.00,
        "voxel_layer.raytrace_min_range": 0.00
    }, target_nodes=[
        "/local_costmap/local_costmap",
        "/global_costmap/global_costmap",
    ])

    # shipping to shipping_2
    if not move_to_pose("shipping_2", navigator, node):
        sys.exit(1)

    # to init
    if not move_to_pose("init", navigator, node):
        sys.exit(1)
    
    navigator.lifecycleShutdown()
    node.destroy_node()
    rclpy.shutdown()    



if __name__ == "__main__":
    main()