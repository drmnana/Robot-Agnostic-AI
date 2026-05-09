from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    robot_id = LaunchConfiguration("robot_id")
    max_linear_speed = LaunchConfiguration("max_linear_speed")
    max_yaw_rate = LaunchConfiguration("max_yaw_rate")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "robot_id",
                default_value="go2x_mock_001",
                description="Identifier for the mock Unitree Go2X robot.",
            ),
            DeclareLaunchArgument(
                "max_linear_speed",
                default_value="0.5",
                description="Maximum allowed linear speed in meters per second.",
            ),
            DeclareLaunchArgument(
                "max_yaw_rate",
                default_value="1.0",
                description="Maximum allowed yaw rate in radians per second.",
            ),
            Node(
                package="mock_go2x_driver",
                executable="mock_go2x_node",
                name="mock_go2x_driver",
                output="screen",
                parameters=[
                    {
                        "robot_id": robot_id,
                    }
                ],
            ),
            Node(
                package="safety_manager",
                executable="safety_manager_node",
                name="safety_manager",
                output="screen",
                parameters=[
                    {
                        "max_linear_speed": max_linear_speed,
                        "max_yaw_rate": max_yaw_rate,
                    }
                ],
            ),
        ]
    )

