import numpy as np
from numpy.lib import stride_tricks as st
import math
import numpy.linalg as lag
from matplotlib.collections import LineCollection
from .geometry import getMaxDistAxis, polygon_peri

class RDObj():
    """ RadialDistanceObject class """
    def __init__(self,id,num_rays,center=None,dists=None,points=None):
        self.id = id
        self.num_rays = num_rays
        self.center = center
        self.dists = dists
        self.points=points

    def getCenter(self,img):
        points=np.argwhere(img==self.id)
        if len(points)>0:
            self.center=(np.mean(points[:,0]),np.mean(points[:,1]))

    def touchImgBorder(self,img,i,j):
        if (i>=len(img))or(i<=0)or(j>=len(img[0]))or(j<=0):
            return True
        return False

    def generateRD_manual(self,img):
        phis = np.linspace(0,2*np.pi,self.num_rays,endpoint=False)
        if (self.center is None):
            self.getCenter(img)   
        if (self.center is None):
            return   
        distx=np.ones(phis.shape)*np.cos(phis)
        disty=np.ones(phis.shape)*np.sin(phis)
        stretch=5
        points=np.zeros((len(phis),3))
        StretchBool=True
        mask=img!=self.id
        mask[:,0]=1
        mask[:,len(mask[0])-1]=1
        mask[0,:]=1
        mask[len(mask)-1,:]=1
        while StretchBool:
            points_strechted=[(self.center[0]+disty*stretch),(self.center[1]+distx*stretch)] 
            points_strechted[0]=np.where(points_strechted[0]<0,0,points_strechted[0])
            points_strechted[1]=np.where(points_strechted[1]<0,0,points_strechted[1])
            points_strechted[0]=np.where(points_strechted[0]>=len(img)-1,len(img)-1,points_strechted[0])
            points_strechted[1]=np.where(points_strechted[1]>=len(img[0])-1,len(img[0])-1,points_strechted[1])
            touch_mask=mask[points_strechted[0].astype(int),points_strechted[1].astype(int)]
            compare=((points[:,2]!=1)&(touch_mask==1))
            points[:,0]+=(self.center[0]+disty*(stretch-1))*compare
            points[:,1]+=(self.center[1]+distx*(stretch-1))*compare
            points[:,2]=np.where(compare==1,1,points[:,2])
            stretch+=1
            if (np.count_nonzero(points[:,2]==0)==0):
                StretchBool=False  

        self.dists=np.sqrt(np.square(self.center[0]-points[:,0])+np.square(self.center[1]-points[:,1]))       
        points[:,2]=0
        self.points=points.astype(int)
        self.getTouchingCandidates(img)

    def getTouchingCandidates(self,img):
        LabelNeighbors = st.sliding_window_view(np.pad(img, 1), (3, 3))    
        for point in self.points:
            if (point[0]<len(img))and(point[1]<len(img[0]))and(point[0]>=0)and(point[1]>=0):
                if (np.count_nonzero(LabelNeighbors[int(point[0]),int(point[1])]==0)==0)or(self.touchImgBorder(img,int(point[0]),int(point[1]))==True):
                    point[2]=1
            else:
                point[2]=1

    def transformRDToArray(self,metric):
        RDArray=self.dists*metric
        return RDArray

    def stretchPoints(self,stretch):
        phis = np.linspace(0,2*np.pi,self.num_rays,endpoint=False) 
        distx=np.ones(phis.shape)*np.cos(phis)
        disty=np.ones(phis.shape)*np.sin(phis)
        self.points[:,0]=(self.center[0]+disty*stretch).astype(int) 
        self.points[:,1]=(self.center[1]+distx*stretch).astype(int) 

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
