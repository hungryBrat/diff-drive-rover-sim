#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import FollowWaypoints

waypoints = [(1.0,0.5,0.0), (2.0,-1.0,1.57), (1.0, 1.57, 2.0)]

def make_pose(x,y,yaw):
    p = PoseStamped()
    p.header.frame_id = 'map'
    p.pose.position.x = x
    p.pose.position.y = y
    p.pose.orientation.z = math.sin(yaw/2.0)
    p.pose.orientation.w = math.cos(yaw/2.0)
    return p

class WaypointClient(Node):
    def __init__(self):
        super().__init__('waypoint_client')
        self._client = ActionClient(self, FollowWaypoints, '/follow_waypoints')

    def send(self):
        self._client.wait_for_server()
        goal_msg = FollowWaypoints.Goal()  
        goal_msg.poses = [make_pose(*wp) for wp in waypoints]

        send_future = self._client.send_goal_async(goal_msg, feedback_callback=self.feedback_cb)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error('goal rejected')
            return
        
        result_future=goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        self.get_logger().info(f'done: {result_future.result().result}')

    def feedback_cb(self, msg):
        self.get_logger().info(f'heading to waypoint {msg.feedback.current_waypoint}')

def main():
    rclpy.init()
    node = WaypointClient()
    node.send()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
