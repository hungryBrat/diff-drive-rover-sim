import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
import xacro

def generate_launch_description():

    # name to match robot name in xacro file
    robotXacroName='differential_drive_robot'

    # name of the package and the name of the folder used to define the path is same in this case
    namePackage = 'mobile_robot' 

    # relative path to the xacro file
    modelFileRelativePath = 'model/robot.xacro'

    # relative path to the custom world SDF
    worldFileRelativePath = 'worlds/empty_with_sensors.sdf'

    # abs path to the world file
    pathWorldFile = os.path.join(get_package_share_directory(namePackage), worldFileRelativePath)

    # abs path to the model
    pathModelFile = os.path.join(get_package_share_directory(namePackage), modelFileRelativePath)

    # get the robot description from the xacro model file
    robotDescription = xacro.process_file(pathModelFile).toxml()

    # launch file from the gazebo pkg
    gazebo_rosPackageLaunch = PythonLaunchDescriptionSource(
        os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    )

    # Use custom world SDF so gz-sim-sensors-system is declared at world level.
    # gpu_lidar requires the sensors system to be a world plugin — NOT a robot plugin.
    # NOTE: gz_args must be passed as a list when the world path is absolute,
    # otherwise gz_sim.launch.py misparses it as a Fuel URI and tries to download it.
    gazeboLaunch = IncludeLaunchDescription(
        gazebo_rosPackageLaunch,
        launch_arguments={
            'gz_args': ['-r -v4 ', pathWorldFile],
            'on_exit_shutdown': 'true'
        }.items()
    )

    # Gazebo spawn node
    spawnModelNodeGazebo = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', robotXacroName,
            '-topic', '/robot_description'
        ],
        output='screen',
    )

    # Robot state publisher node
    nodeRobotStatePublisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robotDescription,
            'use_sim_time': True
        }]
    )

    # ROS <-> Gazebo bridge
    bridge_params = os.path.join(
        get_package_share_directory(namePackage),
        'parameters',
        'bridge_parameters.yaml'
    )

    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ],
        output='screen',
    )

    diff_cont_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller'],
        output='screen',
    )

    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen',

    )


    # Using handlers because need to add time delays before
    # spawning joint_state_broadcaster and diff_controller

    handlerA = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawnModelNodeGazebo,
            on_exit=[joint_broad_spawner],
        )
    )

    handlerB = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_broad_spawner,
            on_exit=[diff_cont_spawner],
        )
    )

    # defining the time-stamper as the interface between
    # teleop-twist messages and the TwistStamped /cmd_vel of ros2_control
    time_stamp_teleop = Node(
        package='twist_stamper',
        executable='twist_stamper',
        parameters=[{'use_sim_time': True}],
        remappings=[
            ('cmd_vel_in', '/cmd_vel'),
            ('cmd_vel_out', '/diff_drive_controller/cmd_vel')
        ],
        output='screen',

    )


    LaunchDescriptionObject = LaunchDescription()
    LaunchDescriptionObject.add_action(gazeboLaunch)
    LaunchDescriptionObject.add_action(nodeRobotStatePublisher)
    LaunchDescriptionObject.add_action(start_gazebo_ros_bridge_cmd)
    LaunchDescriptionObject.add_action(spawnModelNodeGazebo)
    LaunchDescriptionObject.add_action(time_stamp_teleop)
    LaunchDescriptionObject.add_action(handlerA)
    LaunchDescriptionObject.add_action(handlerB)


    return LaunchDescriptionObject
