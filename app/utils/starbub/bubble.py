import numpy as np
import math
import numpy.linalg as lag
from .geometry import getMaxDistAxis, polygon_peri

class Bubble():
    """ RadialDistanceObject class """
    def __init__(self,points,metric,Diameter=None,Position=None,Major=None,Minor=None,Volume=None,Timestep=0.0,Velocity=None,ID=1,Rays=None,is_solitary=0):
        if Diameter==None:
            Major,Minor,Volume,Diameter,Position=self.getBubbleProps(points,metric)
        self.Diameter=Diameter
        self.Position=Position
        self.Major=Major
        self.Minor=Minor
        self.Volume=Volume
        self.Timestep=Timestep
        self.Velocity=Velocity
        self.ID=ID
        self.Rays=Rays
        self.is_solitary=is_solitary
        
        # Calculate Area using Shoelace formula (more accurate than ellipse approximation)
        self.Area_px = self._polygon_area(points[:, 1], points[:, 0]) if points is not None else 0.0
        self.Area_mm = self.Area_px * (metric ** 2)  # Convert to mm²

    @staticmethod
    def _polygon_area(x, y):
        """Calculate polygon area using Shoelace formula."""
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def getBubbleProps(self,points,metric):
        MajorP,MinorP,center=self.getMajorMinor(points)
        if (MinorP[0] is None):
            return None,None,None,None,None
        Major=math.sqrt((MajorP[0][0]-MajorP[1][0])**2+(MajorP[0][1]-MajorP[1][1])**2)/2*metric
        Minor=math.sqrt((MinorP[0][0]-MinorP[1][0])**2+(MinorP[0][1]-MinorP[1][1])**2)/2*metric
        V_Ellipsoid=math.pi*4/3*Major**2*Minor
        d_Sphere=(6*V_Ellipsoid/math.pi)**(1/3)
        return Major,Minor,V_Ellipsoid,d_Sphere,center

    def getMajorMinor(self,points):
        center=np.mean(points[:,0]),np.mean(points[:,1]) 
        MajorP1,MajorP2=getMaxDistAxis(points) 
        VecMajor=[MajorP2[0]-MajorP1[0],MajorP2[1]-MajorP1[1]]      
        Perp_points=[]      
        for p1 in points:
            VecTemp=[center[0]-p1[0],center[1]-p1[1]] 
            scalarProd=np.dot(VecMajor,VecTemp)
            if abs(scalarProd)/(lag.norm(VecMajor)*lag.norm(VecTemp))<(1/lag.norm(VecTemp)):
                Perp_points.append(p1)

        if len(Perp_points)<2:
            allpoints=polygon_peri(points)
            Perp_points=[]      
            for p1 in allpoints:
                VecTemp=[center[0]-p1[0],center[1]-p1[1]] 
                scalarProd=np.dot(VecMajor,VecTemp)
                if abs(scalarProd)/(lag.norm(VecMajor)*lag.norm(VecTemp))<(1/lag.norm(VecTemp)):
                    Perp_points.append(p1)
        MinorP1,MinorP2=getMaxDistAxis(np.array(Perp_points))
        return ([MajorP1,MajorP2],[MinorP1,MinorP2],center)

    def ValuesToString(self):
        base = [str(self.Position[1]),str(self.Position[0]),str(self.Diameter),str(self.Major),str(self.Minor)]
        if self.Velocity is not None:
             base.append(str(self.Velocity))
        base.extend([str(self.Timestep), str(self.ID), str(self.is_solitary)])
        return base
