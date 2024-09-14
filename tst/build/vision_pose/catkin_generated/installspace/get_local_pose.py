import rospy
import tf
import numpy as np
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu

local_x =0
local_y = 0
local_z =0

def loc_pose_callback(msg):
    global local_x, local_y,local_z
    local_x = msg.pose.pose.position.x
    local_y = msg.pose.pose.position.y
    local_z = msg.pose.pose.position.z
    euler1 = tf.transformations.euler_from_quaternion([msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z, msg.pose.pose.orientation.w])
    rospy.loginfo("yaw in /global_positon/local topic: %f", np.rad2deg(euler1[2]))

def odom_out_callback(msg):
    euler2 = tf.transformations.euler_from_quaternion([msg.pose.pose.orientation.x, msg.pose.pose.orientation.y, msg.pose.pose.orientation.z, msg.pose.pose.orientation.w])
    rospy.loginfo("yaw in /odometry/out topic: %f", np.rad2deg(euler2[2]))

def imu_callback(msg):
    euler3 = tf.transformations.euler_from_quaternion([msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w])
    rospy.loginfo("yaw in /imu/data topic: %f", np.rad2deg(euler3[2]))

if __name__ == "__main__":
    rospy.init_node("loc_pose_node")
    local_pos_sub = rospy.Subscriber("/uav1/mavros/global_position/local", Odometry, loc_pose_callback, queue_size=10)
    local_qua_sub = rospy.Subscriber("/uav1/mavros/odometry/out", Odometry, odom_out_callback, queue_size=10)
    local_imu_sub = rospy.Subscriber("/uav1/mavros/imu/data", Imu, imu_callback, queue_size=10)
    rospy.spin()