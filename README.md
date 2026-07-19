# ROS 2 Jazzy & Gazebo Harmonic Differential Drive Rover

## Overview

A full-stack simulation of a custom differential-drive rover, built as a learning project on the way to autonomous navigation. The robot is described in `xacro`, actuated through **`ros2_control`** (`diff_drive_controller` hosted by `gz_ros2_control`), senses with a 2D **`gpu_lidar`**, maps its environment with **`slam_toolbox`**, localizes against the saved map with **`Nav2` + `AMCL`**, and now drives itself around a route of waypoints on its own.

Most of the package is description (xacro), launch, config (yaml), worlds (sdf), and a saved map. It also has its **first hand-written node** — a `FollowWaypoints` action client that sends the rover a list of goals and watches it tick through them.

**Status:** ros2_control ✅ · furnished obstacle world ✅ · SLAM ✅ · Nav2 + AMCL ✅ · autonomous multi-waypoint ✅ · camera + OpenCV next.

## Tech Stack

* **OS:** Ubuntu 24.04
* **ROS 2:** Jazzy Jalisco
* **Simulation:** Gazebo Harmonic (gz-sim 8)
* **Control:** `ros2_control`, `diff_drive_controller`, `gz_ros2_control`
* **Perception / SLAM:** `gpu_lidar`, `slam_toolbox` (online async), `nav2_map_server`
* **Navigation:** `Nav2` (`nav2_bringup`, MPPI controller), `AMCL` localization, `nav2_msgs` `FollowWaypoints`
* **Bridging:** `ros_gz_bridge`, `ros_gz_sim`, `twist_stamper`

## Rover Parameters

All physical constants are `xacro:property` values at the top of `model/robot.xacro`:

| Property | Symbol | Value |
| --- | --- | --- |
| Chassis length | `a` | 1.0 m |
| Chassis height | `b` | 0.3 m |
| Chassis breadth | `c` | 0.6 m |
| Wheel radius | `r` | 0.15 m |
| Wheel thickness | `d` | 0.1 m |
| Wheel separation | `2*s4` | 0.7 m (derived: `2*(c/2 + d/2)`) |
| Lidar radius / height | `r_lidar` / `d_lidar` | 0.1 m / 0.1 m |
| Material density | `d1..d3` | 2710 kg/m³ (aluminium) |

Masses and inertia tensors are computed in the xacro from density × geometry (chassis ≈ 488 kg, each wheel ≈ 19 kg, caster ≈ 38 kg).

> **Note:** `parameters/controllers.yaml` hardcodes `wheel_separation` and `wheel_radius` independently — xacro `${...}` substitution does **not** apply to yaml, so these must be kept in sync with the model **by hand**.

### LiDAR

360 samples over ±π, 15 Hz, range 0.1–12.0 m, Gaussian noise σ = 0.001. Publishes to `/scan` in frame `lidar_link`.

## Prerequisites

A working ROS 2 Jazzy + Gazebo Harmonic install. Since `package.xml` declares all runtime dependencies, the cleanest install is:

```bash
cd ~/everythingROS/firstProject_ws
rosdep install --from-paths src --ignore-src -r -y
```

Or install explicitly:

```bash
sudo apt install \
  ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-controller-manager ros-jazzy-diff-drive-controller \
  ros-jazzy-joint-state-broadcaster ros-jazzy-gz-ros2-control \
  ros-jazzy-twist-stamper ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server
```

## Build

```bash
cd ~/everythingROS/firstProject_ws
colcon build --symlink-install
source install/setup.bash   # required in every new terminal
```

`--symlink-install` lets edits to xacro / yaml / launch / world files take effect **without** a rebuild. (Newly *added* files still need one build to create their symlink.)

## Usage

**1. Launch the simulation**

Starts Gazebo with the furnished house world, spawns the rover from `/robot_description`, and brings up `robot_state_publisher`, the ROS↔Gazebo bridge, the controllers, and `twist_stamper`.

```bash
ros2 launch mobile_robot gazebo_model.launch.py
```

For a fast, physics-light test, point `worldFileRelativePath` in the launch file at `worlds/empty_with_sensors.sdf` instead of `worlds/obstacle_world.sdf`.

**2. Drive it** (new terminal, sourced)

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

teleop publishes `Twist` on `/cmd_vel`; `twist_stamper` restamps it to the `TwistStamped` that `diff_drive_controller` requires.

**3. Map it with SLAM** (new terminal, sourced)

```bash
ros2 launch mobile_robot slam.launch.py
rviz2 --ros-args -p use_sim_time:=true   # Fixed Frame = map; add Map, LaserScan, TF
```

Drive **slowly** — fast in-place rotation outruns the scan matcher and blooms the map (duplicated walls, scattered rooms).

**4. Save the map** (while SLAM is still running)

```bash
ros2 run nav2_map_server map_saver_cli -f src/mobile_robot/maps/small_house \
  --ros-args -p save_map_timeout:=10000
```

**5. Localize + navigate** (new terminal, sourced — needs the sim from step 1 running)

Brings up Nav2 and AMCL against the saved map. AMCL self-seeds at the origin (the rover spawns where the map was born), so you don't need to click a pose in RViz on a normal run.

```bash
ros2 launch mobile_robot nav2.launch.py
rviz2 -d /opt/ros/jazzy/share/nav2_bringup/rviz/nav2_default_view.rviz
```

Confirm localization is live before sending goals: `ros2 run tf2_ros tf2_echo map odom` should stream a transform, and the laser scan should sit on the map walls in RViz. From here you can click **Nav2 Goal** to drive to a single point.

**6. Send it a route of waypoints** (new terminal, sourced)

The one Python node — a `FollowWaypoints` action client. It hands Nav2 an ordered list of map-frame poses and prints each one as the rover reaches it.

```bash
ros2 run mobile_robot waypoint_client.py
```

Edit the `waypoints` list at the top of `scripts/waypoint_client.py` to change the route (`(x, y, yaw)` in the map frame — grab real coordinates with RViz's *Publish Point* tool and `ros2 topic echo /clicked_point`).

## Architecture

**TF tree**

```
map → odom → base_footprint → body_link → {wheel1_link, wheel2_link, caster_link, lidar_link}
```

Ownership of that chain is split deliberately:

* `odom → base_footprint` — published by **`diff_drive_controller`** at 50 Hz from wheel encoders. Smooth and locally accurate, but drifts without bound.
* `map → odom` — the slowly-updating *correction* for that drift. Published by **`slam_toolbox`** while you're mapping, and by **`AMCL`** once you're navigating against the saved map — same transform, two different phases, never both at once. Two publishers can never own the same transform, which is why the correction lands on `odom` rather than the robot directly.

**ROS ↔ Gazebo bridging** (`parameters/bridge_parameters.yaml`) maps only `/clock` and `/scan`. `/cmd_vel`, `/odom`, `/tf`, and `joint_states` are deliberately **not** bridged — `diff_drive_controller` owns those on the ROS side, so bridging them would double-publish.

## Project Structure

```
src/mobile_robot/
├── model/        # robot.xacro (links, joints, inertia, <ros2_control>) + robot.gazebo (sensors, plugins)
├── launch/       # gazebo_model.launch.py (full sim), slam.launch.py, nav2.launch.py
├── parameters/   # controllers.yaml, bridge_parameters.yaml, mapper_params_online_async.yaml, nav2_params.yaml
├── scripts/      # waypoint_client.py — the FollowWaypoints action client (the one Python node)
├── worlds/       # obstacle_world.sdf (AWS Small House, vendored) + empty_with_sensors.sdf
└── maps/         # small_house.pgm / .yaml — saved occupancy grid, localized against by AMCL
```

## Troubleshooting

**Rover doesn't move.** Controllers do not auto-start — confirm both spawned: `ros2 control list_controllers` should show `joint_state_broadcaster` and `diff_drive_controller` as `active`. Also confirm `twist_stamper` is running; without it, `diff_drive_controller` never receives a `TwistStamped`.

**SLAM produces no map.** Check in this order:

1. `ros2 topic echo /scan --field header.frame_id --once` → must print `lidar_link`. If it prints a scoped Gazebo name, the `<gz_frame_id>` tag in `robot.gazebo` is missing.
2. `ros2 topic info /scan --verbose` → `Subscription count` must be 1. If 0, slam_toolbox never activated (it is a **lifecycle node** — launch it via the shipped `online_async_launch.py`, not a raw `Node`).
3. `ros2 run tf2_ros tf2_echo map odom` → must resolve once the first scan is processed.

**RViz shows nothing.** Launch it with `use_sim_time:=true`, or TF lookups run against wall-clock while everything else is stamped with sim time. Check each display's Topic field is actually set, and set the Map display's Durability to *Transient Local* (the map is latched, republished only every 5 s).

**Nav2 says "active" but the rover won't move.** The velocity commands aren't reaching the wheels. Jazzy's `diff_drive_controller` only accepts `TwistStamped`, so the whole Nav2 velocity chain (`controller_server`, `velocity_smoother`, `collision_monitor`, `behavior_server`) needs `enable_stamped_cmd_vel: true` — otherwise it publishes plain `Twist` and DDS silently drops every message. `ros2 topic info /diff_drive_controller/cmd_vel --verbose` should show a single `TwistStamped` publisher.

**`navigate_to_pose action server is not available` in RViz.** `bt_navigator` never reached `active`, usually because one node failed to configure and took the whole lifecycle group down with it. Watch the `nav2.launch.py` terminal on startup for an `ERROR ... during the transition: configure` — a common cause is a bare integer where a `double` is expected (e.g. `wz_max: 3` instead of `3.0`); ROS 2 param typing is strict and will abort the node.

**Weird, stale behaviour after relaunching** (rover respawns where you left it, actions won't connect). Gazebo's server and Nav2's nodes often survive a Ctrl+C. Before relaunching, confirm a clean slate with `ros2 node list` and `pgrep -f "gz sim"`; force-kill survivors with `kill -9` (they ignore a plain kill).

**Sim time freezes / RTF collapses.** Non-static mesh furniture destabilises the solver and starves both the controllers and the sensor pipeline at once. Keep world furniture `<static>`.
