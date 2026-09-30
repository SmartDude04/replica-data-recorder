import cv2
from rclpy import Node
from rcl_interfaces.msg import ParameterDescriptor
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion
import numpy as np
import os
from realsense_recorder import RealsenseRecorder
from scipy.spatial.transform import Rotation

class TrajectoryNode(Node):
    def __init__(self) -> None:
        super().__init__("trajectory_node")

        self.get_logger().info("Started trajectory node")

        self.realsense_recorder = RealsenseRecorder(30, 50)
        self.odom_subscription = self.create_subscription(msg_type=Odometry, topic="/tb27/odom", callback=self.odom_callback, qos_profile=5)

        self.declare_parameter("main_directory", "data", descriptor=ParameterDescriptor(description="Path to the directory where a turtlebot folder will be created for data logging"))
        main_directory = self.get_parameter("main_directory")

        # Make a new directory inside saving_directory for files. Call it turtlebot## where ## is the
        # next number not already a folder name
        directory_num = 0
        while os.path.exists(f"{main_directory}/turtlebot{directory_num:02d}"):
            directory_num += 1
        self.save_directory = f"{main_directory}/turtlebot{directory_num:02d}"

        os.makedirs(self.save_directory)
        os.mkdir(os.path.join(self.save_directory, "results"))
        os.mkdir(os.path.join(self.save_directory, "semantic_class"))

        self.saving_num = 0


    def odom_callback(self, msg: Odometry) -> None:
        color_image, depth_image = self.realsense_recorder.get_frame()

        # Construct the homogeneous matrix from the Odometry message
        cur_pose = msg.pose.pose

        homogeneous_matrix = np.zeros(shape=(4, 4), dtype=np.float32)
        homogeneous_matrix[3, 3] = 1.0
        homogeneous_matrix[:3, :3] = Rotation([cur_pose.orientation.x, cur_pose.orientation.y, cur_pose.orientation.z, cur_pose.orientation.w]).as_matrix()
        homogeneous_matrix[0, 3] = cur_pose.position.x
        homogeneous_matrix[1, 3] = cur_pose.position.y
        homogeneous_matrix[2, 3] = cur_pose.position.z

        # Save the data
        cv2.imwrite(os.path.join(self.save_directory, "results", f"frame{(self.saving_num):06d}.jpg"), color_image)
        cv2.imwrite(os.path.join(self.save_directory, "results", f"depth{(self.saving_num):06d}.png"), depth_image)
        with open(os.path.join(self.save_directory, "traj.txt"), "a") as f:
            f.write(f"{[f"{num:020e} " for num in homogeneous_matrix.flatten()]}")

        self.saving_num += 1

        