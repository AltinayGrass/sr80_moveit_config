import os
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
#from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
#from launch_ros.actions import ComposableNodeContainer
#from launch_ros.descriptions import ComposableNode
#from launch.actions import ExecuteProcess
#from launch.substitutions import LaunchConfiguration
import xacro
from moveit_configs_utils import MoveItConfigsBuilder
#from launch.substitutions import Command


def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return file.read()
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def generate_launch_description():
    
    moveit_config = MoveItConfigsBuilder("SR80", package_name="sr80_moveit_config").to_moveit_configs()
    
    #   .robot_description(file_path="config/SR80.urdf.xacro")
    #   .robot_description_semantic(file_path="config/SR80.srdf")
    #   .planning_pipelines(pipelines=["ompl", "chomp"])
    #moveit_config = MoveItConfigsBuilder("SR80", package_name="sr80_config").to_moveit_configs()

    # Get parameters for the Servo node
    servo_yaml = load_yaml("sr80_moveit_config", "config/sr80_simulated_config.yaml")
    servo_params = {"moveit_servo": servo_yaml}

    ##
    # Start the actual move_group node/action server
    
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        arguments=["--ros-args", "--log-level", "info"],
    )
    ##
    
    # RViz
    rviz_config_file = (
        get_package_share_directory("sr80_moveit_config") + "/config/moveit_servo.rviz"
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
        ],
    )

    # ros2_control using FakeSystem as hardware
    ros2_controllers_path = os.path.join(
        get_package_share_directory("sr80_moveit_config"),
        "config",
        "ros2_controllers.yaml",
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[moveit_config.robot_description, ros2_controllers_path],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            #"--controller-manager-timeout",
            #"300",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    sr80_arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["manipulator_controller", "-c", "/controller_manager"],
    )

   # Static TF
    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )
    
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        respawn=True,
        #name="robot_state_publisher",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            {
                "publish_frequency": 15.0,
            },
        ]
    )

    # Launch a standalone Servo node.
    # As opposed to a node component, this may be necessary (for example) if Servo is running on a different PC   
    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        parameters=[
            servo_params,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            rviz_node,
            move_group_node,
            static_tf_node,
            robot_state_publisher,
            joint_state_broadcaster_spawner,
            sr80_arm_controller_spawner,
            ros2_control_node,
            servo_node,
            #container,
        ]
    )
