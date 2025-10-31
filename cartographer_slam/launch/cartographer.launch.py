import os
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction


def generate_launch_description():

    def launch_setup(context, *args, **kwargs):
        is_sim = context.launch_configurations['use_sim_time'] == "True"
        cartographer_config_dir = os.path.join(get_package_share_directory('cartographer_slam'), 'config')
        configuration_basename = 'cartographer_sim.lua' if is_sim else 'cartographer_real.lua'
        rviz_file = os.path.join(get_package_share_directory('cartographer_slam'), 'rviz', 'mapping.rviz')

        print(f"[Cartographer Launch] use_sim_time = {is_sim}")
        print(f"[Cartographer Launch] Using config file: {configuration_basename}")

        cartographer_node = Node(
            package='cartographer_ros', 
            executable='cartographer_node', 
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': is_sim}],
            arguments=[
                '-configuration_directory', cartographer_config_dir,
                '-configuration_basename', configuration_basename
            ]
        )

        occupancy_grid_node = Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            output='screen',
            name='occupancy_grid_node',
            parameters=[{'use_sim_time': is_sim}],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0']
        )

        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_file],
            parameters=[{'use_sim_time': is_sim}],
            output='screen'
        )

        return [cartographer_node, occupancy_grid_node, rviz_node]


    return LaunchDescription([
         DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        OpaqueFunction(function=launch_setup)
    ]) 