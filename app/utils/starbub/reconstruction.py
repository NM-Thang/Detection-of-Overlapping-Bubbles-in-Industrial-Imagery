import numpy as np
import math
from scipy.ndimage import uniform_filter1d

from .rd_obj import RDObj
from .bubble import Bubble


def HiddenReco(labels, metric, timestep=0, model=None):
    """
    Reconstruct bubbles from StarDist labels using RDC.
    
    Args:
        labels: StarDist label array
        metric: Pixel to mm conversion factor
        timestep: Timestamp for tracking
        model: RDC model instance
    """
    n_rays = 64
    Bubbles = []
    
    for i in range(1, np.max(labels) + 1):
        # RDObj calculates center from mask pixels (same as training data gen)
        Rdc = RDObj(i, n_rays)
        Rdc.generateRD_manual(labels)
        
        if Rdc.center is None:
            continue
            
        # Apply RDC model for collision rays
        if model is not None and np.count_nonzero(Rdc.points[:,2] == 1) > 1:
            RDArray = Rdc.transformRDToArray(metric)
            yhat = model.predict(np.asarray([RDArray]))
            stretch = yhat[0] / metric
            #stretch = np.where(stretch * Rdc.points[:,2] > Rdc.dists, stretch, Rdc.dists)
            stretch = uniform_filter1d(stretch, size=3)
            Rdc.stretchPoints(stretch)
            Rdc.dists = stretch

        # Determine Solitary status: 1 = Overlapping, 0 = Single
        is_overlapped = 1 if np.count_nonzero(Rdc.points[:,2] == 1) > 1 else 0
        
        Bub = Bubble(Rdc.points, metric, Timestep=timestep, ID=i, Rays=Rdc.dists, is_solitary=is_overlapped)
        if Bub.Diameter is not None:
            Bubbles.append(Bub)

    return Bubbles