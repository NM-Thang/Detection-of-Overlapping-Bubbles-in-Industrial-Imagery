import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from skimage.measure import EllipseModel
import math
import csv
from scipy.ndimage import uniform_filter1d

from .structures import RDObj, Bubble
from .stepper import BubbleStepper

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
                    stretch=uniform_filter1d(stretch,size=4)
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
                    # Determine Solitary status
                    # User Logic: Overlapping/Touching = 1, Single = 0
                    is_overlapped = 1 if np.count_nonzero(Rdc.points[:,2]==1)>1 else 0
                    
                    Bub=Bubble(Rdc.points,metric,Timestep=timestep,ID=i,Rays=Rdc.dists,is_solitary=is_overlapped)
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
                    Bubbles.append(Bubble(None,None,Diameter=d_Sphere,Position=[y0,x0],Major=a,Minor=b,Volume=V_Ellipsoid,Timestep=timestep,is_solitary=0))
    
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
