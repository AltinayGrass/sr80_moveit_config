import os
import yaml
from launch import LaunchDescription
from launch import substitutions
from launch import actions
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


    # Launch a standalone Servo node.
    # As opposed to a node component, this may be necessary (for example) if Servo is running on a different PC 
        # This sets the update rate and planning group name for the acceleration limiting filter.
def generate_launch_description():
        # moveit_config = MoveItConfigsBuilder("SR80", package_name="sr80_moveit_config").to_moveit_configs()
 
    joint_limits_file_path = 'config/joint_limits.yaml'
    moveit_config = (
    MoveItConfigsBuilder("SR80" , package_name="sr80_moveit_config")
    .planning_scene_monitor(
        publish_robot_description=True, publish_robot_description_semantic=True
    )
    .joint_limits(file_path=joint_limits_file_path)
    .planning_pipelines(
        pipelines=["ompl", "chomp", "pilz_industrial_motion_planner"]
    )
    .to_moveit_configs()
)
        # Get parameters for the Servo node
    servo_yaml = load_yaml("sr80_moveit_config", "config/sr80_simulated_config.yaml")
    servo_params = {"moveit_servo": servo_yaml}
    
    acceleration_filter_update_period = {"update_period": 0.034}
    planning_group_name = {"planning_group_name": "arm"}
      
    servo_node = Node(
        package="moveit_servo",
        executable="servo_node",
        parameters=[
            servo_params,
            acceleration_filter_update_period,
            planning_group_name,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
        ],
        output="screen",
    )    

    config_filepath = substitutions.LaunchConfiguration('config_filepath')
    joy_config = substitutions.LaunchConfiguration('joy_config')
    actions.DeclareLaunchArgument('joy_config', default_value='joyfox'),
    actions.DeclareLaunchArgument('config_filepath', default_value=[
            substitutions.TextSubstitution(text=os.path.join(
                get_package_share_directory('sr80_moveit_config'), 'config', '')),
            joy_config, substitutions.TextSubstitution(text='.config.yaml')]),
    
    teleop_twist_joy_node = Node (
        package='teleop_twist_joy', 
        executable='teleop_node',
        parameters=[config_filepath],
        remappings={(('/cmd_vel','/servo_node/delta_twist_cmds'))},
        output="screen",
    )
    
    spacenav_node = Node (
        package='spacenav',
        executable='spacenav_node',
        remappings={(('/spacenav/joy','/joy'))},
        output='screen',
    )
    
    return LaunchDescription(
        [
            actions.DeclareLaunchArgument('joy_config', default_value='joyfox'),
            actions.DeclareLaunchArgument('config_filepath', default_value=[
                substitutions.TextSubstitution(text=os.path.join(
                get_package_share_directory('sr80_moveit_config'), 'config', '')),
                joy_config, substitutions.TextSubstitution(text='.config.yaml')]),
            
            #servo_node,
            teleop_twist_joy_node,
            spacenav_node,
        ]
    )
