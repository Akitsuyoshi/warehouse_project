import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    def launch_setup(context, *args, **kwargs):
        is_sim = context.launch_configurations['use_sim_time'] == "True"

        pkg_dir = get_package_share_directory('path_planner_server')
        controller_yaml = os.path.join(pkg_dir, 'config', 'controller_sim.yaml' if is_sim else 'controller_real.yaml')
        planner_yaml = os.path.join(pkg_dir, 'config', 'planner_sim.yaml' if is_sim else 'planner_real.yaml')
        bt_navigator_yaml = os.path.join(pkg_dir, 'config', 'bt_navigator_sim.yaml' if is_sim else 'bt_navigator_real.yaml')
        recovery_yaml = os.path.join(pkg_dir, 'config', 'recoveries_sim.yaml' if is_sim else 'recoveries_real.yaml')
        rviz_file = os.path.join(pkg_dir, 'rviz', 'pathplanning.rviz')

        print(f"[Path Planner Launch] use_sim_time = {is_sim}")
        print(f"[Path Planner Launch] controller_yaml = {controller_yaml}")

        common_params = [{'use_sim_time': is_sim}]

        controller_node = Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[controller_yaml] + common_params,
            remappings=[('/cmd_vel', '/diffbot_base_controller/cmd_vel_unstamped')] if is_sim else []

        )

        planner_node = Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[planner_yaml] + common_params
        )

        recovery_node = Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='recoveries_server',
            parameters=[recovery_yaml] + common_params,
            output='screen'
        )

        bt_navigator_node = Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[bt_navigator_yaml] + common_params
        )

        lifecycle_manager_node = Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_pathplanner',
            output='screen',
            parameters=[{
                'use_sim_time': is_sim,
                'autostart': True,
                'node_names': [
                    'planner_server',
                    'controller_server',
                    'recoveries_server',
                    'bt_navigator'
                ]
            }]
        )

        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_file],
            parameters=common_params,
            output='screen'
        )

        return [
            controller_node,
            planner_node,
            recovery_node,
            bt_navigator_node,
            lifecycle_manager_node,
            rviz_node
        ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='True',
            description='use simulation time'
        ),
        OpaqueFunction(function=launch_setup)
    ])
