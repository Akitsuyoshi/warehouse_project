import os
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node

def generate_launch_description():
    
    def launch_setup(context, *args, **kwargs):
        map_path = os.path.join(get_package_share_directory('map_server'), 'config', context.launch_configurations['map_file'])
        is_sim = 'sim' in os.path.basename(context.launch_configurations['map_file']).lower()
        rviz_file = os.path.join(get_package_share_directory('map_server'), 'rviz', 'map_display.rviz')

        print(f"[Cartographer Launch] map_path = {map_path}")
        print(f"[Cartographer Launch] is_sim: {is_sim}")

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

        lifecycle_manager_node = Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_mapper',
            output='screen',
            parameters=[
                {'use_sim_time': is_sim},
                {'autostart': True},
                {'node_names': ['map_server']}
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

        return [map_server_node, lifecycle_manager_node, rviz_node]


    return LaunchDescription([
       DeclareLaunchArgument(
            'map_file',
            default_value=os.path.join(
                get_package_share_directory('map_server'),
                'config',
                'warehouse_map_sim.yaml'
            ),
            description='map yaml file name'
        ),
        OpaqueFunction(function=launch_setup)
        ])