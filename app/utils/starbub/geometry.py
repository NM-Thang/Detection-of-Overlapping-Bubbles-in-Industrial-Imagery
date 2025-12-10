import numpy as np
import math
from skimage.draw import polygon_perimeter

def polygon_peri(points):
    r = np.array(points[:,0])
    c = np.array(points[:,1])
    rr, cc = polygon_perimeter(r, c)
    ret_points=np.zeros((len(rr),2))
    ret_points[:,0]=rr
    ret_points[:,1]=cc
    return ret_points

def getMaxDistAxis(points):
    Max_dist=0.0
    MaxdistP1 = None
    MaxdistP2 = None
    
    for i in range(len(points)):
        for j in range(len(points)):
            p1 = points[i]
            p2 = points[j]
            dist = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            if dist > Max_dist:
                Max_dist = dist
                MaxdistP1 = p1.copy()
                MaxdistP2 = p2.copy()

    return MaxdistP1,MaxdistP2
