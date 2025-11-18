import os
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node

def generate_launch_description():

    def launch_setup(context, *args, **kwargs):
        map_file = context.launch_configurations['map_file']
        map_path = os.path.join(get_package_share_directory('map_server'), 'config', map_file)
        is_sim = 'sim' in os.path.basename(map_file).lower()

        pkg_localization = get_package_share_directory('localization_server')
        amcl_config_file = 'amcl_config_sim.yaml' if is_sim else 'amcl_config_real.yaml'
        amcl_config = os.path.join(pkg_localization, 'config', amcl_config_file)
        rviz_file = os.path.join(pkg_localization, 'rviz', 'localization.rviz')
        filter_config_file = 'filters_sim.yaml' if is_sim else 'filters_real.yaml'
        filters_yaml = os.path.join(get_package_share_directory('path_planner_server'), 'config', filter_config_file)

        print(f"[Localization Launch] map_path = {map_path}")
        print(f"[Localization Launch] use_sim_time = {is_sim}")
        print(f"[Localization Launch] amcl_config_file = {amcl_config_file}")

        map_server_node = Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[
                {'use_sim_time': is_sim},
                {'yaml_filename': map_path}
            ]
        )

        amcl_node = Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[amcl_config, {'use_sim_time': is_sim}]
        )

        filter_server_node = Node(
            package='nav2_map_server',
            executable='map_server',
            name='filter_mask_server',
            output='screen',
            emulate_tty=True,
            parameters=[filters_yaml, {'use_sim_time': is_sim}]
        )

        costmap_filter_server_node = Node(
            package='nav2_map_server',
            executable='costmap_filter_info_server',
            name='costmap_filter_info_server',
            output='screen',
            emulate_tty=True,
            parameters=[filters_yaml, {'use_sim_time': is_sim}]
        )

        lifecycle_manager_node = Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[
                {'use_sim_time': is_sim},
                {'autostart': True},
                {'node_names': ['map_server', 'amcl', 'filter_mask_server', 'costmap_filter_info_server']}
            ]
        )

        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_file],
            parameters=[{'use_sim_time': is_sim}],
            output='screen'
        )

        return [map_server_node, amcl_node, filter_server_node, costmap_filter_server_node, lifecycle_manager_node, rviz_node]
        

    return LaunchDescription([
        DeclareLaunchArgument(
            'map_file',
            default_value='warehouse_map_sim.yaml',
            description='Map yaml file name'
        ),
        OpaqueFunction(function=launch_setup)
    ])
