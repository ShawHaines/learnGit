#!/usr/bin/env python
import rospy
import tf
import math
from nav_msgs.srv import GetMap
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
# from visualization_msgs.msg import MarkerArray,Marker
from nav_msgs.msg import OccupancyGrid
import numpy as np
from icp import LandmarkICP,SubICP,NeighBor
from localization_lm import LandmarkLocalization
from ekf_lm import EKF_SLAM,STATE_SIZE,LM_SIZE,Cx,INF
from extraction import Extraction
from mapping import Mapping
# import scipy.linalg as scilinalg
from slam_ekf import SLAM_Localization
# import sys

MAX_LASER_RANGE = 30

class SLAM_Mapping(SLAM_Localization):
    def __init__(self,nodeName="slam_ekf"):
        super(SLAM_Mapping,self).__init__(nodeName)
        # ros parameters
        self.robot_x = float(rospy.get_param('/slam/robot_x',0))
        self.robot_y = float(rospy.get_param('/slam/robot_y',0))
        self.robot_theta = float(rospy.get_param('/slam/robot_theta',0))
        self.mapping = Mapping()

    # feed icp landmark instead of laser.
    def laserCallback(self,msg):
        print('------seq:  ',msg.header.seq)
        if self.isFirstScan:
            # feed in landmarks.
            # self.icp.tar_pc=self.extraction.process(msg)
            self.icp.tar_pc=self.icp.laserToNumpy(msg)
            self.isFirstScan = False
            return
        
        # Update once every 5 laser scan because the we cannot distinguish rotation if interval is too small.
        self.laser_count += 1
        if self.laser_count < self.laser_interval:
            return

        # Updating process
        self.laser_count = 0
        # z is the landmarks in self frame as a 2*n array.
        z=self.extraction.process(msg,True)
        self.publishLandMark(z,"b")
        # relative displacement
        u=self.calc_odometry(msg)
        
        # xEst,lEst,PEst is both predicted and updated in the ekf.
        self.xEst,self.lEst,self.PEst=self.estimate(self.xEst,self.lEst,self.PEst,z,u)

        self.publishResult()

        # np_msg = self.laserToNumpy(msg)
        # lm = self.extraction.process(np_msg)
        # # u = self.calc_odometry(self.lm2pc(lm))
        # u = self.calc_odometry(np_msg)
        # z = self.observation(lm)
        # self.xEst,self.PEst = self.ekf.estimate(self.xEst,self.PEst,z,u)

        # # FIXME
        # pointCloud = self.u2T(self.xEst[0:3]).dot(np_msg)
        pointCloud=np.dot(tf.transformations.euler_matrix(0,0,self.xEst[2,0])[0:2,0:2],self.icp.laserToNumpy(msg))+self.xEst[0:2]
        
        self.mapping.update(pointCloud, self.xEst[0:2].reshape(-1))
        self.mapping.publishMap()
        return
    
def main():
    rospy.init_node('slam_node')
    s = SLAM_Mapping()
    rospy.spin()
    pass

def test():
    pass

if __name__ == '__main__':
    main()
    # test()
