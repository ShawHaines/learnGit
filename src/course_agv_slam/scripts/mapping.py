import math
import numpy as np


class Mapping():
    def __init__(self,xw,yw,resolution):
        self.width_x = xw*resolution
        self.width_y = yw*resolution
        self.resolution = resolution
        self.xw = xw
        self.yw = yw
        self.pmap = np.ones((self.xw, self.yw))*0.5 # default 0.5 -- [[0.5 for i in range(yw)] for i in range(xw)] 
        self.minx = -self.width_x/2.0
        self.maxx =  self.width_x/2.0
        self.miny = -self.width_y/2.0
        self.maxy =  self.width_y/2.0
        self.origin=np.array([self.xw/2,self.yw/2])
        self.weight=0.02

    def update(self, laserPC, center):
        """
        laserPC is pointcloud as always, (x,y)=center tuple denotes the robot's position.
        """
        # change the points into integers
        start=list(np.round(np.array(center)//self.resolution).astype(int))
        for point in laserPC.T:
            end=list(np.round(point//self.resolution).astype(int))
            pointList=self.line(start,end)
            # remove obstacle point.
            if list(pointList[0])==end:
                np.delete(pointList,0,axis=0)
            elif list(pointList[-1])==end:
                np.delete(pointList,-1,axis=0)
            # origin bias
            pointList+=self.origin
            # decrease possibility
            self.pmap[pointList[:,0],pointList[:,1]]-=self.weight

            # obstacle point more possibility, turns out it needs stronger weight.
            self.pmap[tuple(np.array(end)+self.origin)]+=self.weight*10

        self.pmap[self.pmap>1]=1
        self.pmap[self.pmap<0]=0
        
        return self.pmap

    def line(self,start,end):
        """
        returns an n*2 array, each row represents a point that needs to be updated.
        """
        (x1,y1)=start
        (x2,y2)=end
        if x1 == x2: # Special Case: Vertical Line
            if y1 <= y2:
                return np.array([[x1, y] for y in range(y1, y2 + 1)])
            else:
                return np.array([[x1, y] for y in range(y2, y1 + 1)])
        elif abs(y2 - y1) <= abs(x2 - x1): # abs(slope) <= 1
            return self.Bresenham(start,end)
        else: # abs(slope) > 1: Axis Reverse
            return np.fliplr(self.Bresenham((y1,x1), (y2,x2)))
    
    def Bresenham(self,start,end):
        # Parameter of Drawing
        (x1,y1)=start
        (x2,y2)=end        
        slope=float(y2-y1)/(x2 - x1)
        # Initialize
        p=2*slope-1
        [x, y] = [x1, y1]
        # adjust the cases to default situation.
        if x1 >= x2: # start-end Symmetry
            return self.Bresenham(end,start)
        if slope<0:
            pointList = self.Bresenham((x1,-y1), (x2,-y2))
            pointList[:,1]=-pointList[:,1]
            return pointList

        # Real Bresenham Algorithm. Default situation,x1<x2 and slope>=0
        pointList = []
        pointList.append([x, y])
        while x != x2:
            if p <= 0:
                [x, y, p] = [x + 1, y, p + 2 * slope]
            else:
                [x, y, p] = [x + 1, y + 1, p + 2 * slope - 2]
            pointList.append([x,y])
        return np.array(pointList)

def main():
    import rospy
    from nav_msgs.msg import OccupancyGrid
    """
    Example usage
    """
    print(__file__, "start")
    length = 20
    xyreso = 0.1  # x-y grid resolution
    xyw = int(round(length/xyreso))
    mapping = Mapping(xyw,xyw,xyreso)
    lidar_num = 200

    for i in range(10):
        center_x = 3 - i*0.3
        center_y = 3 - i*0.3
        ang = np.linspace(0,2*math.pi,lidar_num)
        dist = np.random.rand(lidar_num)*1+5
        ox = np.sin(ang) * dist # + center_x
        oy = np.cos(ang) * dist # + center_y
        pmap = mapping.update(ox, oy, center_x, center_y)

        rospy.init_node("map_pub")

        map_pub = rospy.Publisher('/slam_map',OccupancyGrid,queue_size=1)

        map_msg = OccupancyGrid()
        map_msg.header.seq = 1
        map_msg.header.stamp = rospy.Time().now()
        map_msg.header.frame_id = "map"

        map_msg.info.map_load_time = rospy.Time().now()
        map_msg.info.resolution = xyreso
        map_msg.info.width = xyw
        map_msg.info.height = xyw
        map_msg.info.origin.position.x = -xyw*xyreso/2.0
        map_msg.info.origin.position.y = -xyw*xyreso/2.0
        map_msg.info.origin.position.z = 0
        map_msg.info.origin.orientation.x = 0
        map_msg.info.origin.orientation.y = 0
        map_msg.info.origin.orientation.z = 0
        map_msg.info.origin.orientation.w = 1.0

        map_msg.data = list(pmap.reshape(-1)*100)
        
        map_pub.publish(map_msg)
        rospy.sleep(1)

if __name__ == '__main__':
    main()     
