import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():

    namePackage = 'mobile_robot'

    navParams = os.path.join(
        get_package_share_directory(namePackage),
        'parameters',
        'nav2_params.yaml'
    )

    mapParams = os.path.join(
        get_package_share_directory(namePackage),
        'maps',
        'small_house.yaml'
    )

    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'localization_launch.py'
            )
        ),
        launch_arguments={
            'params_file': navParams,
            'use_sim_time': 'true',
            'map' : mapParams,
        }.items()
    )

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            )
        ),
        launch_arguments={
            'params_file': navParams,
            'use_sim_time': 'true',
        }.items()
    )


    NavLaunchDescription = LaunchDescription()
    NavLaunchDescription.add_action(localization_launch)
    NavLaunchDescription.add_action(navigation_launch)
    return NavLaunchDescription