import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
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

    # skipping making our own empty world

    # abs path to the model
    pathModelFile = os.path.joint(get_package_share_directory(namePackage),modelFileRelativePath)

    # get the robot description from the xacro model file
    robotDescription = xacro.process_file(pathModelFile).toxml()

    #this is the launch file from tje gazebo pkg
    gazebo_rosPackageLaunch = PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('ros_gz_sim'), 'launch','gz_sim.launch.py'))

    # now tp ythe launch description

    # as we are using a predetermined empty world
    gazeboLaunch=IncludeLaunchDescription(gazebo_rosPackageLaunch, launch_arguments={'gz_args': [ '-r -v -v4 empty.sdf'], 'on_exit_shutdown': 'true' }.items())


    # Gazebo Node
    spawnModelNodeGazebo = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', robotXacroName,
            '-topic', 'robot_description'
        ],
        output='screen',
    )

    # Robot state publisher NOde
    nodeRobotStatePublisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen'
        parameters=[{'robot_description': robotDescription,
                    'use_sim_time':True}]
    )

    # next is important to control robot from ROS2
    bridge_params = os.path.join(
        get_package_share_directory(namePackage), # type: ignore
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

    # creating an empty launch description object
    LaunchDescriptionObject = LaunchDescription()

    # adding gazeboLuanch
    LaunchDescriptionObject.add_action(gazeboLaunch)

    # adding the teo nopdes
    LaunchDescriptionObject.add_action(spawnModelNodeGazebo)
    LaunchDescriptionObject.add_action(nodeRobotStatePublisher)
    LaunchDescriptionObject.add_action(start_gazebo_ros_bridge_cmd)

    return LaunchDescriptionObject





