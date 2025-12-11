import os
import json
import csv
import math
import numpy as np
from PIL import Image

class DataSaver:
    def save_results(self, res_dir, img_name, labels, details, bubbles, metric):
        """
        Orchestrates saving all results for a single image.
        """
        img_result_folder = os.path.join(res_dir, img_name)
        os.makedirs(img_result_folder, exist_ok=True)
        
        # Paths
        sd_mask_dir = os.path.join(os.path.dirname(res_dir), 'SDmask')
        js_mask_dir = os.path.join(os.path.dirname(res_dir), 'JSMask')
        os.makedirs(sd_mask_dir, exist_ok=True)
        os.makedirs(js_mask_dir, exist_ok=True)
        
        sd_mask_path = os.path.join(sd_mask_dir, f"{img_name}.png")
        js_mask_path = os.path.join(js_mask_dir, f"{img_name}.json")
        pixel_csv = os.path.join(img_result_folder, f"{img_name}_pixel.csv")
        mm_csv = os.path.join(img_result_folder, f"{img_name}_mm.csv")
        
        # Save Components
        self._save_mask(labels, sd_mask_path)
        self._save_json(details, js_mask_path)
        self._save_csv(bubbles, pixel_csv, mm_csv, metric)
        
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

    def _save_csv(self, Bubbles, pixel_path, mm_path, Metric):
        ray_headers = [f"Ray_{i+1}" for i in range(64)]
        headers = ["STT", "Center_X", "Center_Y", "Axis_1", "Axis_2", "Area", "Type"] + ray_headers
        
        try:
            with open(pixel_path, 'w', newline='') as f_pix, \
                 open(mm_path, 'w', newline='') as f_mm:
                
                wr_pix = csv.writer(f_pix)
                wr_mm = csv.writer(f_mm)
                
                wr_pix.writerow(headers)
                wr_mm.writerow(headers)
                
                for i, bub in enumerate(Bubbles):
                    stt = i + 1
                    cx = bub.Position[1]
                    cy = bub.Position[0]
                    
                    # MM Units
                    major_mm = bub.Major * 2
                    minor_mm = bub.Minor * 2
                    area_mm = math.pi * bub.Major * bub.Minor
                    
                    # Pixel Units
                    major_pix = major_mm / Metric
                    minor_pix = minor_mm / Metric
                    area_pix = math.pi * (bub.Major / Metric) * (bub.Minor / Metric)
                    
                    # Rays
                    if bub.Rays is not None:
                        rays_pix = bub.Rays
                        rays_mm = bub.Rays * Metric
                    else:
                        rays_pix = [0] * 64
                        rays_mm = [0] * 64
                    
                    # Type (is_solitary)
                    # 1 = Overlapping, 0 = Single
                    b_type = getattr(bub, 'is_solitary', 0)
                        
                    # Write rows
                    row_pix = [stt, cx, cy, major_pix, minor_pix, area_pix, b_type] + list(rays_pix)
                    wr_pix.writerow(row_pix)
                    
                    row_mm = [stt, cx, cy, major_mm, minor_mm, area_mm, b_type] + list(rays_mm)
                    wr_mm.writerow(row_mm)
                    
        except Exception as e:
            print(f"Error saving CSV: {e}")
