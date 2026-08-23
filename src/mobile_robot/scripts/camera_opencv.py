#!/usr/bin/env python3


from message_filters import Subscriber, ApproximateTimeSynchronizer
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
import cv2
import rclpy
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2
from sensor_msgs_py.point_cloud2 import read_points_numpy, create_cloud_xyz32


   
lower_hsv=(13,50,50)
upper_hsv=(17,255,255)

class CameraOpenCV(Node):
    def __init__(self):
        super().__init__('camera_opencv')
        self.bridge = CvBridge()
        self.img_sub = Subscriber(self, Image, '/camera/image', qos_profile=qos_profile_sensor_data)
        self.pc_sub  = Subscriber(self, PointCloud2, '/camera/points', qos_profile=qos_profile_sensor_data)
        self.ats = ApproximateTimeSynchronizer([self.img_sub, self.pc_sub], queue_size=10, slop=0.05)
        self.ats.registerCallback(self.on_pair)
        self.mask_pub    = self.create_publisher(Image, '/camera/mask_debug', 10)
        self.overlay_pub = self.create_publisher(Image, '/camera/mask_overlay', 10)
        self.pub = self.create_publisher(PointCloud2, '/detected_obstacle_points', 10)

        

        
    def on_pair(self, img_msg, cloud_msg):
        img = self.bridge.imgmsg_to_cv2(img_msg, desired_encoding='bgr8')  # forces BGR for OpenCV
        hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv) 
        pts = read_points_numpy(cloud_msg, field_names=('x','y','z'), skip_nans=False)  
        pts = pts.reshape(cloud_msg.height, cloud_msg.width, 3)               # organized: pixel (v,u) -> pts[v,u]
        sel = pts[mask.astype(bool)]                 
        sel = sel[np.isfinite(sel).all(axis=1)]        
        px = cv2.countNonZero(mask)
        self.get_logger().info(
            f'mask {px:6d} px ({100.0 * px / mask.size:4.1f}%) -> {len(sel)} pts'
            + (f'  x_med {np.median(sel[:, 0]):.2f} m' if len(sel) else ''),
            throttle_duration_sec=1.0)

        out = create_cloud_xyz32(cloud_msg.header, sel)   
        self.pub.publish(out)

        
        self.mask_pub.publish(
            self.bridge.cv2_to_imgmsg(mask, encoding='mono8', header=img_msg.header))
        overlay = cv2.bitwise_and(img, img, mask=mask)
        self.overlay_pub.publish(
            self.bridge.cv2_to_imgmsg(overlay, encoding='bgr8', header=img_msg.header))
        
        # self.get_logger().info(f'{mask.sum()}')


def main():
    rclpy.init()
    node = CameraOpenCV()
    rclpy.spin(node)
    rclpy.shutdown()
    

if __name__ == '__main__':
    main()


