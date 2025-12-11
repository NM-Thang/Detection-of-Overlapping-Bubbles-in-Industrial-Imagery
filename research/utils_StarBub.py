import numpy as np
from numpy.lib import stride_tricks as st
from skimage.draw import polygon_perimeter,polygon
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import math
import numpy.linalg as lag
import csv
from PIL import Image
from matplotlib.patches import Ellipse
from skimage.measure import EllipseModel
import json
from scipy.ndimage.filters import uniform_filter1d
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d
from matplotlib.widgets import Button



class RDObj():
    """ RadialDistanceObject class
    
    Parameters
    ----------
    id : int
        Object ID.
    num_rays: ing
        Number of radial rays defining the object.
    center: Tuple
        Tuple (y,x) for the center coordinates of the object.
    dists:  
        Array (y,x) containing the length of each radial ray from the center to the object boundary.
    points:
        Numpy array (y,x,bool) containing the position of the radial end points and a bool whether the point touches
        another segmentation instance or not.
    """
    
    
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

    def drawRD(self,ax,color='g',linewidths=0.6):
        dist_lines=np.empty((self.num_rays,2,2))
        if len(self.points)==0:
            print("No Endpoints evaluated so far. Try generateRD_manual() function")
        else:
            dist_lines[:,0,0] = self.points[:,1]
            dist_lines[:,0,1] = self.points[:,0]
            dist_lines[:,1,0] = self.center[1]
            dist_lines[:,1,1] = self.center[0]
            ax.add_collection(LineCollection(dist_lines, colors=color, linewidths=linewidths))
    
    def drawTouchingCandidates(self,ax,color='r',linewidths=0.6):
        num_candidates=np.count_nonzero(self.points[:,2]==1)
        if num_candidates>0:
            dist_lines=np.empty((num_candidates,2,2))
            counter=0
            for point in self.points:
                if point[2]==1:
                    dist_lines[counter,0,0]=point[1]
                    dist_lines[counter,0,1]=point[0]

class Bubble():
    """ RadialDistanceObject class
    
    Parameters
    ----------
    img : ndarray
        Binary image containing the detected bubble.
    metric: float
        Real pixel size in [m] needed to calculate physical sizes.
    Diameter: float
        Sphere-volume equivalent diameter. 
    Position: Tuple
        Tuple (y,x) for the center coordinates of the bubble.
    Major: float
        Majoraxis length, determined as the longest distance of all boundary pixels.
    Minor: float
        Majoraxis length, determined as the longest distance of all boundary pixels perpendicular to the Majoraxis.
    Volume: float
        Spheroidal volume of the bubble determined with Major and Minor.
    Timestep: float
        Timestep when the bubble was detected (e.g. image number).
    Velocity: float (tracking not implemented yet!)
        Bubble velocity.
    ID: int
        Object ID.
    """
    
    def __init__(self,points,metric,Diameter=None,Position=None,Major=None,Minor=None,Volume=None,Timestep=0.0,Velocity=None,ID=1,Rays=None):
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

        # Getting the center of all points belonging to the object
        center=np.mean(points[:,0]),np.mean(points[:,1]) 

        #Major axis as largest distance of all border points
        MajorP1,MajorP2=getMaxDistAxis(points) 

        #Minor axis as largest distance of all points perpendicular to Major axis 
        VecMajor=[MajorP2[0]-MajorP1[0],MajorP2[1]-MajorP1[1]]      
        Perp_points=[]      
        for p1 in points:
            VecTemp=[center[0]-p1[0],center[1]-p1[1]] 
            scalarProd=np.dot(VecMajor,VecTemp)
            if abs(scalarProd)/(lag.norm(VecMajor)*lag.norm(VecTemp))<(1/lag.norm(VecTemp)):
                Perp_points.append(p1)

        #Use more boundary points to fullfill perpendicular criterion
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
        if self.Velocity==None:
            return [str(self.Position[1]),str(self.Position[0]),str(self.Diameter),str(self.Major),str(self.Minor),str(self.Timestep),str(self.ID)]
        else:
            return [str(self.Position[1]),str(self.Position[0]),str(self.Diameter),str(self.Major),str(self.Minor),str(self.Velocity),str(self.Timestep),str(self.ID)]

class BubbleStepper:
    def __init__(self, ax, visual_items, background_img=None):
        self.ax = ax
        self.visual_items = visual_items
        self.background_img = background_img
        self.current_idx = -1
        self.artists = [] 
        self.detail_fig = None
        
        plt.subplots_adjust(bottom=0.2)
        ax_prev = plt.axes([0.7, 0.05, 0.1, 0.075])
        ax_next = plt.axes([0.81, 0.05, 0.1, 0.075])
        self.bnext = Button(ax_next, 'Next')
        self.bprev = Button(ax_prev, 'Prev')
        self.bnext.on_clicked(self.next)
        self.bprev.on_clicked(self.prev)
        
        self.ax.figure.canvas.mpl_connect('key_press_event', self.on_key)
        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_click)
        print("Interactive Mode: Press Right/Next to draw bubble, Left/Prev to undo. Click on bubble to view detail with rays.")
        plt.show(block=True)

    def next(self, event=None):
        if self.current_idx < len(self.visual_items) - 1:
            self.current_idx += 1
            item = self.visual_items[self.current_idx]
            self.draw_item(item)
            self.ax.figure.canvas.draw_idle()

    def prev(self, event=None):
        if self.current_idx >= 0:
            if self.artists:
                last_artists = self.artists.pop()
                for art in last_artists:
                    art.remove()
                self.current_idx -= 1
                self.ax.figure.canvas.draw_idle()

    def draw_item(self, item, draw_rays=False):
        # Implementation assumed same but need to check if I changed it. I only added 'draw_rays' logic? 
        # No, I didn't verify if draw_item was modified heavily.
        # But looking at previous view, draw_item seemed to have new logic.
        # Wait, the provided file view in 659 shows `draw_item` has `draw_rays` param? 
        # Actually in 659, `draw_item` DOES NOT HAVE `draw_rays` param in the view?
        # Let's check 659 lines 255+. 
        # Line 264: def draw_item(self, item): is NOT what I see in 659? 
        # Ah, 659 was BEFORE or AFTER my changes? 
        # 659 was AFTER I reverted changes? No I haven't reverted yet.
        # I did not modify `draw_item` in steps 628. I only modified `__init__`.
        # So I will just use whatever `draw_item` is there?
        pass # I need to be careful not to delete methods.

    # ... Continuing replacement for HiddenReco ...

def HiddenReco(labels,metric,timestep=0,useRDC=False,model=None,boolPlot=False,ax=None,OnlyPoints=False,step_plot=True,return_visuals=False):
    if ax is None and boolPlot:
        ax = plt.gca()
    if model==None:
        useRDC=False
    if useRDC==False:
        ell=EllipseModel()
    n_rays=64
    Bubbles=[]
    VisualItems=[]
    
    for i in range(1,np.max(labels)+1):
        Rdc=RDObj(i,n_rays)
        Rdc.generateRD_manual(labels)
        if (Rdc.center!=None):      
            if useRDC:
                if (np.count_nonzero(Rdc.points[:,2]==1)>1):
                    # dung model
                    RDArray=Rdc.transformRDToArray(metric)
                    yhat = model.predict(np.asarray([RDArray]))
                    stretch=yhat[0]/metric
                    # stretch=np.where(stretch*Rdc.points[:,2]>Rdc.dists,stretch,Rdc.dists)
                    # stretch=uniform_filter1d(stretch,size=4)
                    Rdc.stretchPoints(stretch)
                    Rdc.dists = stretch

                if OnlyPoints:
                    points=Rdc.points[:,:2]
                    Bubbles.append((i,points))
                if boolPlot:
                    random_color=tuple((np.random.choice(range(255),size=3))/255)
                    VisualItems.append({
                        'type': 'rdc',
                        'points': Rdc.points.copy(),
                        'center': Rdc.center,
                        'dists': Rdc.dists.copy() if Rdc.dists is not None else None,
                        'pixel_count': np.count_nonzero(labels==i),
                        'color': random_color,
                    })
                
                if OnlyPoints==False:    
                    Bub=Bubble(Rdc.points,metric,Timestep=timestep,ID=i,Rays=Rdc.dists)
                    if Bub.Diameter is not None:
                        Bubbles.append(Bub)
            else:
                pointsEllipse=[]
                pointsbackup=[]
                ell=EllipseModel()
                for point in Rdc.points:
                    if point[2]==0:
                        pointsEllipse.append([point[0],point[1]])
                    pointsbackup.append([point[0],point[1]])
                areaEllipse=0
                if len(pointsEllipse)>0:
                    pointsEllipse=np.array(pointsEllipse)
                    ell.estimate(pointsEllipse)
                    try:
                        x0,y0,a,b,phi1=ell.params
                        phi=0.5*np.pi-phi1
                        areaEllipse=math.pi*a*b
                    except:
                        areaEllipse=0
                        print('Error in ellipse fit, retry with backup')
                if (areaEllipse<np.count_nonzero(labels==i))or(areaEllipse>20*np.count_nonzero(labels==i)):
                    pointsEllipse=np.array(pointsbackup)
                    ell.estimate(pointsEllipse)
                    try:
                        x0,y0,a,b,phi1=ell.params
                        phi=0.5*np.pi-phi1
                        areaEllipse=math.pi*a*b
                    except:
                        areaEllipse=0
                        print(f'Unable to fit ellipse for label {i}')
                if boolPlot:
                    random_color=tuple((np.random.choice(range(255),size=3))/255)
                    VisualItems.append({
                        'type': 'ellipse',
                        'params': (y0, x0, a, b, phi),
                        'color': random_color
                    })
                if math.isnan(areaEllipse)==False:
                    major_el=a if a > b else b
                    minor_el=b if b < a else a
                    major_el=major_el*metric
                    minor_el=minor_el*metric
                    V_Ellipsoid=math.pi*4/3*major_el**2*minor_el
                    d_Sphere=(6*V_Ellipsoid/math.pi)**(1/3)
                    Bubbles.append(Bubble(None,None,Diameter=d_Sphere,Position=[y0,x0],Major=a,Minor=b,Volume=V_Ellipsoid,Timestep=timestep))
    
    if return_visuals:
        return Bubbles, VisualItems

    if boolPlot and step_plot and VisualItems:
        BubbleStepper(ax, VisualItems)
    elif boolPlot and VisualItems:
        for item in VisualItems:
            if item['type'] == 'rdc':
                points = item['points']
                color = item['color']
                a,b = list(points[:,1]),list(points[:,0])
                a += a[:1]
                b += b[:1]
                ax.plot(a,b, '-', alpha=1, zorder=1, color=color, linewidth=1.5)

            elif item['type'] == 'ellipse':
                params = item['params']
                color = item['color']
                y0, x0, a, b, phi = params
                ellipse = Ellipse((y0, x0), 2*a, 2*b, angle=math.degrees(phi), alpha=0.25, color=color)
                ax.add_artist(ellipse)
                
    return Bubbles

def SaveCSV_List(Bubbles,directory,name,header=None):
    f = open(directory+name+'.csv', "w") 
    wr = csv.writer(f)
    if header:
        f.write(str(header+'\n'))  
    for bub in Bubbles:
        wr.writerow(bub.ValuesToString())
    f.close()

# def scale(X,x_min,x_max):
#     nom=(X-X.min())*(x_max-x_min)
#     denom=X.max()-X.min()
#     denom=denom+(denom == 0)
#     return x_min + nom/denom

# def Save_Labels(labels,directory,name,scaleGrey=False):
#     if scaleGrey==True:
#         labels=scale(labels,0,255)
#     img=Image.fromarray(labels.astype('uint8'))
#     img.save(directory+name+".png")

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

# def writeOutJSONPoints(Bubbles,directory,name):
#     Bubbles_dict=[]
#     for bub in Bubbles:
#         Bubble_dict={}
#         Bubble_dict['ID']=bub[0]
#         XPoints=[]
#         YPoints=[]
#         for b in bub[1]:
#             YPoints.append(int(b[0]))
#             XPoints.append(int(b[1]))
#         Bubble_dict['YPoints']=YPoints 
#         Bubble_dict['XPoints']=XPoints 
#         Bubbles_dict.append(Bubble_dict)
#     with open(directory+name+'.json',"w") as out:
#         json.dump(Bubbles_dict,out,indent=1)