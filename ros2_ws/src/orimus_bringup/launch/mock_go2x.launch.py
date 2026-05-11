from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    robot_id = LaunchConfiguration("robot_id")
    max_linear_speed = LaunchConfiguration("max_linear_speed")
    max_yaw_rate = LaunchConfiguration("max_yaw_rate")
    mission_autostart = LaunchConfiguration("mission_autostart")
    mission_config_path = LaunchConfiguration("mission_config_path")
    completion_marker_path = LaunchConfiguration("completion_marker_path")
    report_path = LaunchConfiguration("report_path")
    artifact_root = LaunchConfiguration("artifact_root")
    mission_api_port = LaunchConfiguration("mission_api_port")

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
            DeclareLaunchArgument(
                "mission_autostart",
                default_value="false",
                description="Whether to start the demo mission automatically.",
            ),
            DeclareLaunchArgument(
                "mission_config_path",
                default_value="",
                description="Optional YAML mission configuration file.",
            ),
            DeclareLaunchArgument(
                "completion_marker_path",
                default_value="",
                description="Optional file path written when the demo mission completes.",
            ),
            DeclareLaunchArgument(
                "report_path",
                default_value="/workspace/reports/latest_mission_report.json",
                description="Mission report JSON output path.",
            ),
            DeclareLaunchArgument(
                "artifact_root",
                default_value="/workspace/data/artifacts",
                description="Directory where evidence artifact files are stored.",
            ),
            DeclareLaunchArgument(
                "mission_api_port",
                default_value="8010",
                description="HTTP port for the ROS-aware mission API bridge.",
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
            Node(
                package="payload_manager",
                executable="payload_manager_node",
                name="payload_manager",
                output="screen",
            ),
            Node(
                package="mock_payloads",
                executable="mock_inspection_camera_node",
                name="mock_inspection_camera",
                output="screen",
                parameters=[
                    {
                        "artifact_root": artifact_root,
                    }
                ],
            ),
            Node(
                package="report_manager",
                executable="report_manager_node",
                name="report_manager",
                output="screen",
                parameters=[
                    {
                        "report_path": report_path,
                        "artifact_root": artifact_root,
                    }
                ],
            ),
            Node(
                package="mission_manager",
                executable="mission_manager_node",
                name="mission_manager",
                output="screen",
                parameters=[
                    {
                        "autostart": mission_autostart,
                        "mission_config_path": mission_config_path,
                        "completion_marker_path": completion_marker_path,
                    }
                ],
            ),
            Node(
                package="mission_api_bridge",
                executable="mission_api_bridge_node",
                name="mission_api_bridge",
                output="screen",
                parameters=[
                    {
                        "port": mission_api_port,
                    }
                ],
            ),
        ]
    )
