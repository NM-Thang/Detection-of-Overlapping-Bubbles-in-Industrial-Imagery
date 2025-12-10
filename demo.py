#!/usr/bin/env python3
"""
Demo script to run bubble detection on a single image
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'

import numpy as np
from PIL import Image

def load_img(path):
    x = np.array(Image.open(path).convert('L'))
    return x
from csbdeep.utils import normalize

from stardist.models import StarDist2D
import matplotlib.pyplot as plt
import pathlib
import tensorflow as tf
from utils_StarBub import HiddenReco, SaveCSV_List, BubbleStepper
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
model = tf.keras.models.load_model(Model_dir + 'RDC/rdc_model_mm.h5')

print("Models loaded successfully!")

# Prediction configuration
Metric = 5.2E-2  # Pixel size in mm
useRDC = True    # Use RDC method
boolplot = True  # Show results

# Image path
ImgDir = base_dir + '/Examples/img/frame_0180.png'

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
VisualItems = []
Bubbles = []

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
    
    # Reconstruct bubbles (Get Data ONLY, do not plot yet)
    # Note: We pass return_visuals=True to prevent blocking and get visual data back
    Bubbles, VisualItems = HiddenReco(labels, Metric, useRDC=useRDC, model=model, boolPlot=boolplot, ax=ax2, step_plot=True, return_visuals=True)
    
    # plt.tight_layout() # Move this to end
    
    print(f"Detected {len(Bubbles)} bubbles")

else:
    Bubbles = HiddenReco(labels, Metric, useRDC=useRDC, model=model, boolPlot=False)
    print(f"Detected {len(Bubbles)} bubbles")

# --- CSV Export ---
print("Exporting results to CSV...")

# 1. Create output directory
# Folder path: Examples/Results/<ImageName>/
img_name = os.path.splitext(os.path.basename(ImgDir))[0] # e.g., 'frame_0180'
output_dir = os.path.join(base_dir, 'Examples', 'Results', img_name)
os.makedirs(output_dir, exist_ok=True)

pixel_csv_path = os.path.join(output_dir, f"{img_name}_pixel.csv")
mm_csv_path = os.path.join(output_dir, f"{img_name}_mm.csv")

import csv 
import math

try:
    # Prepare headers
    # Col 1: STT, 2-3: Center(X,Y), 4-5: Major/Minor(Axes), 6: Area, 7-70: 64 Rays
    ray_headers = [f"Ray_{i+1}" for i in range(64)]
    headers = ["STT", "Center_X", "Center_Y", "Axis_1", "Axis_2", "Area"] + ray_headers
    
    with open(pixel_csv_path, 'w', newline='') as f_pix, \
            open(mm_csv_path, 'w', newline='') as f_mm:
        
        wr_pix = csv.writer(f_pix)
        wr_mm = csv.writer(f_mm)
        
        wr_pix.writerow(headers)
        wr_mm.writerow(headers)
        
        for i, bub in enumerate(Bubbles):
            stt = i + 1
            
            # --- Coordinates (Center) ---
            # Position is [y, x], so X=Position[1], Y=Position[0]
            # User requested "Center Pixel Coordinates" for both files.
            cx = bub.Position[1]
            cy = bub.Position[0]
            
            # --- Axes (Major/Minor) ---
            # Metric = Pixel size in mm
            
            # MM Units
            major_mm = bub.Major * 2
            minor_mm = bub.Minor * 2
            
            # Pixel Units
            major_pix = major_mm / Metric
            minor_pix = minor_mm / Metric
            
            # --- Area ---
            area_mm = math.pi * bub.Major * bub.Minor
            area_pix = math.pi * (bub.Major / Metric) * (bub.Minor / Metric)
            
            # --- Rays ---
            # bub.Rays are the distances (dists) in PIXELS
            if bub.Rays is not None:
                rays_pix = bub.Rays
                rays_mm = bub.Rays * Metric
            else:
                rays_pix = [0] * 64
                rays_mm = [0] * 64
            
            # Write rows
            # Pixel CSV
            row_pix = [stt, cx, cy, major_pix, minor_pix, area_pix] + list(rays_pix)
            wr_pix.writerow(row_pix)
            
            # MM CSV
            row_mm = [stt, cx, cy, major_mm, minor_mm, area_mm] + list(rays_mm)
            wr_mm.writerow(row_mm)
            
    print(f"Saved results to:\n  {pixel_csv_path}\n  {mm_csv_path}")

except Exception as e:
    print(f"Error exporting CSV: {e}")

# --- Visualization (Launching GUI) ---
if boolplot and VisualItems:
    print("Launching interactive viewer...")
    plt.tight_layout()
    # Manually start the stepper with the retrieved VisualItems
    # Note: ax2 was passed to HiddenReco, but HiddenReco didn't plot anything because return_visuals=True
    # So we used ax2 to set up structure, now we pass it to BubbleStepper
    
    # We need to make sure 'ax2' is passed correctly if HiddenReco didn't use it.
    # Actually, BubbleStepper takes 'ax' as argument.
    BubbleStepper(ax2, VisualItems)
    # plt.show() is called inside BubbleStepper(block=True), so we don't strictly need it here,
    # but BubbleStepper calls plt.show(block=True).

print("Done!")
