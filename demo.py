#!/usr/bin/env python3
"""
Demo script to run bubble detection on a single image
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'

from utils_Segmentation import load_img
from csbdeep.utils import normalize

from stardist.models import StarDist2D
import matplotlib.pyplot as plt
import pathlib
import tensorflow as tf
from utils_StarBub import HiddenReco, SaveCSV_List
from tqdm import tqdm
from stardist import random_label_cmap
import matplotlib
matplotlib.rcParams["image.interpolation"] = None

# Configuration
base_dir = os.path.abspath('')
Model_dir = base_dir + '/Models/'
use_gpu = False  # Set to False if no GPU

# Setup GPU/CPU
if use_gpu:
    physical_devices = tf.config.list_physical_devices('GPU')
    for device in physical_devices:
        tf.config.experimental.set_memory_growth(device, True)
else:
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

print("Loading models...")
# Load models
modelSD = StarDist2D(None, name='data_mix_64_400', basedir=Model_dir + 'SDmodel')

# model = tf.keras.models.load_model(Model_dir + 'RDC/rdc_model.h5')
model = tf.keras.models.load_model(Model_dir + 'RDC/RDC_PAPER')

print("Models loaded successfully!")

# Prediction configuration
Metric = 15E-2  # Pixel size in mm
useRDC = True    # Use RDC method
boolplot = True  # Show results

# Image path
ImgDir = base_dir + '/Examples/img/43.png'

print(f"Processing image: {ImgDir}")

# Load and normalize image
x = load_img(ImgDir)
X = normalize(x if x.ndim == 2 else x[..., 0], 1, 99.8, axis=(0, 1))

# Create mask with UNet
# imgMask, imgIntersec = createLabelUNet(X, 2, netMask, 512, 300, ctxMask=ctx)

# StarDist Prediction
# labels, _ = combinedPrediction(X, modelSD, imgMask, imgIntersec)
labels,_=modelSD.predict_instances(X,verbose=False)


# Display results
if boolplot:
    lbl_cmap = random_label_cmap()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    
    # Segmentation mask
    ax1.imshow(X, cmap='gray')
    ax1.imshow(labels, cmap=lbl_cmap, alpha=0.5)
    ax1.set_axis_off()
    ax1.set_title('Segmentation mask')
    
    # Hidden part reconstruction
    ax2.imshow(X, cmap='gray')
    ax2.set_axis_off() 
    ax2.set_title('Hidden part reconstruction')   
    
    # Reconstruct bubbles
    Bubbles = HiddenReco(labels, Metric, useRDC=useRDC, model=model, boolPlot=boolplot, ax=ax2, step_plot=True)
    
    plt.tight_layout()
    # plt.savefig('demo_result_origin_0013.png.png')
    
    print(f"Detected {len(Bubbles)} bubbles")
    # if Bubbles:
    #     print("Bubble details:")
    #     for i, bubble in enumerate(Bubbles[:5]):  # Show first 5 bubbles
    #         print(f"Bubble {i+1}: {bubble}")
else:
    Bubbles = HiddenReco(labels, Metric, useRDC=useRDC, model=model, boolPlot=False)
    print(f"Detected {len(Bubbles)} bubbles")

print("Done!")
