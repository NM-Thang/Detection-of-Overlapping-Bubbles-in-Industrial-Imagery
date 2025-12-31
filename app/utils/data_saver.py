import os
import json
import csv
import math
import numpy as np
from PIL import Image

from .json_collision import analyze_collisions, resolve_collisions

class DataSaver:
    def save_results(self, base_dir, img_name, labels, details, bubbles, metric):
        """
        Orchestrates saving all results for a single image.
        """
        # Paths - base_dir is now passed directly
        
        sd_mask_dir = os.path.join(base_dir, 'SDmask')
        js_mask_dir = os.path.join(base_dir, 'JSMask')
        csv_dir = os.path.join(base_dir, 'csv')
        
        os.makedirs(sd_mask_dir, exist_ok=True)
        os.makedirs(js_mask_dir, exist_ok=True)
        os.makedirs(csv_dir, exist_ok=True)
        
        sd_mask_path = os.path.join(sd_mask_dir, f"{img_name}.png")
        js_mask_path = os.path.join(js_mask_dir, f"{img_name}.json")
        csv_path = os.path.join(csv_dir, f"{img_name}.csv")  # Simplified: no subfolder, no _pixel suffix
        
        # Calculate & Merge Collision Details
        if labels is not None:
             img_shape = labels.shape
             
             # 1. Analyze flags for visualization (Red/Green)
             if 'rays_collision' not in details:
                 collision_matrix = analyze_collisions(details, img_shape)
                 details['rays_collision'] = collision_matrix
             
             # 2. Resolve geometry for visualization (Clipping)
             if 'coord_resolved' not in details:
                 resolved_coords = resolve_collisions(details, img_shape)
                 details['coord_resolved'] = resolved_coords

        # Save Components
        self._save_mask(labels, sd_mask_path)
        self._save_json(details, js_mask_path)
        self._save_csv(bubbles, csv_path, metric)

        
    def _save_mask(self, labels, path):
        try:
            Image.fromarray(labels.astype(np.int32), mode='I').save(path)
        except:
            Image.fromarray(labels.astype(np.uint8)).save(path)

    def _save_json(self, details, path):
        def _default_serializer(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            if isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            return str(obj)

        with open(path, 'w') as f:
            json.dump(details, f, default=_default_serializer, indent=2)

    def _save_csv(self, Bubbles, pixel_path, Metric):
        """Save bubble data to single CSV file with both pixel and mm area."""
        ray_headers = [f"Ray_{i+1}" for i in range(64)]
        # Added Area_mm column next to Area_px
        headers = ["STT", "Center_X", "Center_Y", "Axis_1", "Axis_2", "Area_px", "Area_mm", "Type"] + ray_headers
        
        try:
            with open(pixel_path, 'w', newline='') as f_pix:
                wr_pix = csv.writer(f_pix)
                wr_pix.writerow(headers)
                
                for i, bub in enumerate(Bubbles):
                    stt = i + 1
                    cx = bub.Position[1]
                    cy = bub.Position[0]
                    
                    # Axes (pixel units)
                    major_pix = (bub.Major * 2) / Metric if bub.Major else 0
                    minor_pix = (bub.Minor * 2) / Metric if bub.Minor else 0
                    
                    # Area using Shoelace formula
                    area_px = getattr(bub, 'Area_px', 0)
                    area_mm = getattr(bub, 'Area_mm', 0)
                    
                    # Rays (pixel units)
                    if bub.Rays is not None:
                        rays_pix = bub.Rays
                    else:
                        rays_pix = [0] * 64
                    
                    # Type (is_solitary): 1 = Overlapping, 0 = Single
                    b_type = getattr(bub, 'is_solitary', 0)
                        
                    # Write row
                    row_pix = [stt, cx, cy, major_pix, minor_pix, area_px, area_mm, b_type] + list(rays_pix)
                    wr_pix.writerow(row_pix)
                    
        except Exception as e:
            print(f"Error saving CSV: {e}")

