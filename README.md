# ROS 2 Jazzy & Gazebo Harmonic Differential Drive Rover

## Overview

This package contains a full-stack ROS 2 and Gazebo simulation for a custom differential drive rover. The project utilizes `xacro` for dynamic URDF generation and relies on the `ros_gz_bridge` to establish bidirectional communication between ROS 2 Jazzy and Gazebo Harmonic.

## Tech Stack

* **OS:** Ubuntu 24.04
* **ROS 2:** Jazzy Jalisco
* **Simulation:** Gazebo Harmonic
* **Key Packages:** `xacro`, `ros_gz_bridge`, `ros_gz_sim`, `teleop_twist_keyboard`

## Rover Parameters

* **Wheel Radius:** `r=`
* **Track Width (Wheel Separation):** 
* **Chassis Dimensions:** 
  * Length: `a=`
  * Breath: `c=`
  * height: `b=`
* **Total Mass:** 

## Prerequisites

Ensure you have a working installation of ROS 2 Jazzy and Gazebo Harmonic. You will also need to install the necessary integration and control packages:


    ```bash
    sudo apt update
    sudo apt install ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-xacro ros-jazzy-teleop-twist-keyboard
    ```

After you ensure that you have a working version of ROS2 and Gazebo, follow the given steps to launch the simulation

## Installation

1. Source your ROS 2 installation:
   
    Note that without sourcing your workspace, you will not be able to use any ROS2

    ```Bash
    source /opt/ros/jazzy/setup.bash
    ```

2. Navigate to your colcon workspace src directory:

    All the code that you write needs to go in the `/src` folder

    ```Bash
    cd ~/ros2_ws/src
    ```
    Clone this repository (or copy your package folder here).

3. Build the workspace:

    ```Bash
    cd ~/ros2_ws
    colcon build
    ```

4. Source the built workspace:

    ```Bash
    source install/setup.bash
    ```

## Usage
1. **Launching the Simulation**
   
    The main launch file will start Gazebo Harmonic, parse the URDF model via xacro, spawn the rover into the simulation, and start the necessary bridges for standard ROS 2 topics (/cmd_vel, /odom, /tf).

    ```Bash
    ros2 launch mobile_robot gazebo_model.launch.py
    ```


2. **Teleoperation**
   
    To drive the rover using your keyboard, open a new terminal, source the workspace, and run the teleop node:

    ```Bash
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
    ```

**Note: Ensure the teleop node is publishing to the correct /cmd_vel topic that the Gazebo differential drive plugin is subscribing to via the bridge.**


## Project Structure

   * `launch/`: Contains ROS 2 launch files (e.g., sim_launch.py).

   * `urdf/`: Contains the .xacro and .urdf files defining the rover's visual, collision, and inertial properties.

   * `worlds/`: Contains custom Gazebo Harmonic .sdf world files.

   * `config/`: Contains YAML configuration files mapping topics for the ros_gz_bridge.

   * `CMakeLists.txt` / `package.xml`: Standard ROS 2 package build configurations.

## Troubleshooting

If the rover is not moving when sending commands:

- Verify that the ros_gz_bridge is running correctly and successfully translating geometry_msgs/msg/Twist from ROS to the Gazebo equivalent.

- Double-check the Gazebo differential drive plugin parameters in your URDF to ensure the `<left_joint>` and `<right_joint>` names match your defined joints exactly.