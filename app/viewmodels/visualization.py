import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import json
from PIL import Image
from app.utils.config import AppConfig
from app.utils.visualizer import Visualizer
import csv

class VisualizationViewModel:
    def __init__(self, root):
        self.root = root
        
        # Paths
        self.metadata_path = tk.StringVar()
        self.output_root_path = None # Parent of metadata.txt
        
        # Data
        self.image_list = [] # List of filenames
        self.current_img_idx = -1
        

        
        # Display Options
        self.show_original = tk.BooleanVar(value=False)
        self.show_mask = tk.BooleanVar(value=False)
        self.show_result = tk.BooleanVar(value=True) # Default on
        
        # Current Loaded Data
        self.current_original_img = None
        self.current_mask_img = None
        self.current_json_details = None
        self.current_result_items = None
        self.current_img_name = ""
        
        # Statistics
        self.stat_img_size = tk.StringVar(value="N/A")
        self.stat_bubble_count = tk.StringVar(value="0")
        self.stat_bub_area_mm = tk.StringVar(value="0.0")
        self.stat_bub_area_px = tk.StringVar(value="0.0")
        self.stat_img_area_mm = tk.StringVar(value="0.0")
        self.stat_ratio_mm = tk.StringVar(value="0.0 %")
        
        # StarDist Stats
        self.stat_sd_count = tk.StringVar(value="0")
        self.stat_sd_prob = tk.StringVar(value="0.0")
        self.stat_sd_area_px = tk.StringVar(value="0.0")
        self.stat_sd_area_mm = tk.StringVar(value="0.0")
        self.stat_sd_ratio = tk.StringVar(value="0.0 %")
        
        # Callbacks
        self.on_image_list_update = None
        self.on_bubble_list_update = None
        self.on_view_update = None
        self.on_control_mode_update = None

        # Control Mode
        self.control_mode = tk.StringVar(value="RDC") # "RDC" or "SD"
        
        # Internal storage for lists
        self.bubble_list_rdc = []
        self.bubble_list_sd = []
        
        # Shared Ratio
        self.ratio_factor = 0.0

    @property
    def bubble_list(self):
        if self.control_mode.get() == "SD":
             return self.bubble_list_sd
        return self.bubble_list_rdc

    def get_stardist_visual_items(self):
        """Convert current JSON details to BubbleStepper items."""
        if not self.current_json_details:
            return []
            
        items = []
        details = self.current_json_details
        
        # We need 'dist' (raw rays) for best visualization, fallback to 'coord'
        has_dist = 'dist' in details
        has_coord = 'coord' in details
        
        if not has_dist and not has_coord:
            return []
            
        # Lists
        dists = details.get('dist') if has_dist else []
        coords = details.get('coord') if has_coord else []
        points = details.get('points', [])
        
        # Determine count (max of lists)
        count = 0
        if dists is not None: count = max(count, len(dists))
        if coords is not None: count = max(count, len(coords))
        
        # Helper for potentially non-array lists
        def _get(arr, i):
           if arr is None: return None
           if i >= len(arr): return None
           if isinstance(arr, list): return np.array(arr[i])
           return arr[i]

        for i in range(count):
             # 1. Center
             pt = _get(points, i)
             cy, cx = 0, 0
             if pt is not None:
                 cy, cx = pt[0], pt[1]
             
             # 2. Reconstruct Points
             poly_points = None
             raw_dists = None
             
             if has_dist:
                 d = _get(dists, i)
                 if d is not None:
                     raw_dists = d
                     # Reconstruct Rays
                     n_rays = len(d)
                     phis = np.linspace(0, 2*np.pi, n_rays, endpoint=False)
                     rays_x = cx + d * np.cos(phis)
                     rays_y = cy + d * np.sin(phis)
                     # Stack as (y, x) for consistency with RDC expectations if stepping
                     # RDC Points usually (Y, X)? CHECK Stepper.
                     # Stepper: a, b = list(points[:, 1]), list(points[:, 0]) -> a=x, b=y.
                     # So points column 0 is Y, column 1 is X.
                     poly_points = np.column_stack([rays_y, rays_x])
             
             if poly_points is None and has_coord:
                  # Fallback to coords
                  c = _get(coords, i)
                  if c is not None:
                      # Parse coord
                      arr = np.array(c)
                      if arr.ndim == 2:
                         if arr.shape[0] == 2 and arr.shape[1] > 2: # (2, N)
                             poly_points = arr.T # (N, 2) -> (y, x)
                         elif arr.shape[1] == 2: # (N, 2)
                             poly_points = arr # (y, x)

             if poly_points is not None:
                 items.append({
                     'type': 'rdc', # Reuse RDC renderer (Polygon + Rays)
                     'points': poly_points, # (N, 2) -> (Y, X)
                     'center': np.array([cy, cx]),
                     'dists': raw_dists, 
                     'color': 'lime', # Green for StarDist
                     'stt': i + 1,
                     'pixel_count': 'N/A' # Could calc area
                 })
                 
        return items

    def select_metadata(self):
        path = filedialog.askopenfilename(title="Select metadata.txt", filetypes=[("Text Files", "*.txt")])
        if path:
            self.load_metadata_from_path(path)
            
    def load_metadata_from_path(self, path):
        if path and os.path.exists(path):
            self.metadata_path.set(path)
            self.load_metadata(path)

    def load_metadata(self, path):
        try:
            self.output_root_path = os.path.dirname(path)
            with open(path, 'r') as f:
                lines = f.readlines()
            
            self.image_list = [line.strip() for line in lines if line.strip()]
            
            if self.on_image_list_update:
                self.on_image_list_update()
                
            # Auto-select first if available
            if self.image_list:
                self.select_image(0)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load metadata: {e}")

    def select_image(self, index):
        if 0 <= index < len(self.image_list):
            self.current_img_idx = index
            img_filename = self.image_list[index]
            self.current_img_name = img_filename
            self._load_image_data(img_filename)
            
    def _load_image_data(self, img_filename):
        # Infer paths
        # root/imgs/filename
        # root/SDmask/filename (maybe png?)
        # root/results/name_no_ext/name_pixel.csv
        
        root = self.output_root_path
        name_no_ext = os.path.splitext(img_filename)[0]
        
        img_path = os.path.join(root, 'imgs', img_filename)
        # Try finding mask with same name but potentially png extension if generated as .png
        # The InferenceEngine saves as .png
        mask_path = os.path.join(root, 'SDmask', f"{name_no_ext}.png") 
        
        csv_path = os.path.join(root, 'results', name_no_ext, f"{name_no_ext}_pixel.csv") # Use pixel for rays? 
        # Actually user wants Area mm^2. We might need mm csv too or just convert if we know metric?
        # InferenceEngine saves both. Let's load MM csv for table data, Pixel csv for rendering?
        # Visualizer uses Pixel csv to draw on image.
        
        csv_mm_path = os.path.join(root, 'results', name_no_ext, f"{name_no_ext}_mm.csv")
        
        try:
            # 1. Load Original
            if os.path.exists(img_path):
                self.current_original_img = np.array(Image.open(img_path).convert('L'))
            else:
                self.current_original_img = None
                
            # 2. Load Mask
            if os.path.exists(mask_path):
                self.current_mask_img = np.array(Image.open(mask_path)) # Keep labels
            else:
                self.current_mask_img = None
                
            # 2b. Load JSON Details (JSMask)
            json_path = os.path.join(root, 'JSMask', f"{name_no_ext}.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        self.current_json_details = json.load(f)
                        
                    # Calculate StarDist Stats immediately
                    if self.current_json_details:
                         # Count
                         pts = self.current_json_details.get('points', [])
                         self.stat_sd_count.set(str(len(pts)))
                         
                         # Prob
                         probs = self.current_json_details.get('prob', [])
                         if probs:
                             avg_prob = np.mean(probs)
                             self.stat_sd_prob.set(f"{avg_prob:.4f}")
                         else:
                             self.stat_sd_prob.set("N/A")
                    else:
                         self.stat_sd_count.set("0")
                         self.stat_sd_prob.set("0.0")
                         
                except Exception as e:
                    print(f"Error loading JSON: {e}")
                    self.current_json_details = None
                    self.stat_sd_count.set("Error")
            else:
                self.current_json_details = None
                self.stat_sd_count.set("Not Found")
                self.stat_sd_prob.set("N/A")
                
            # 3. Load Results (CSV) & Parse Bubble List (RDC)
            self.bubble_list_rdc = []
            
            # We use mm csv for the List details (Area mm^2)
            if os.path.exists(csv_mm_path):
                try:
                    with open(csv_mm_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Headers: STT, Center_X, Center_Y, Axis_1, Axis_2, Area, Type, Ray_...
                            self.bubble_list_rdc.append({
                                'stt': row.get('STT'),
                                'cx': row.get('Center_X'),
                                'cy': row.get('Center_Y'),
                                'area_mm': row.get('Area'),
                                'pixels': "N/A" # Count from mask? Or Pixel CSV Area?
                            })
                except Exception as e:
                     print(f"Error reading MM CSV: {e}")
            
            # If we want pixel area, we could read pixel csv too.
            if os.path.exists(csv_path):
                 try:
                     with open(csv_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for i, row in enumerate(reader):
                            if i < len(self.bubble_list_rdc):
                                self.bubble_list_rdc[i]['area_px'] = row.get('Area')
                 except Exception as e:
                      print(f"Error reading Pixel CSV: {e}")
            
            # Prepare Visualizer Items (Using Visualizer util or custom)
            # The Visualizer util does full reconstruction.
            # We need to retrieve the 'VisualItems' list for the Stepper.
            # Visualizer.load_and_visualize returns None, it launches plotting.
            # For now, let's use the Visualizer class to parse only.
            
            if os.path.exists(csv_path):
                self.current_result_items = Visualizer.get_visual_items(img_path, csv_path)
            else:
                self.current_result_items = []

            # --- Calculate Statistics ---
            img_h, img_w = self.current_original_img.shape
            img_area_px = img_h * img_w
            self.stat_img_size.set(f"{img_w} x {img_h}")
            self.stat_bubble_count.set(str(len(self.bubble_list_rdc)))
            
            total_bub_mm = 0.0
            total_bub_px = 0.0
            
            for b in self.bubble_list_rdc:
                try:
                    total_bub_mm += float(b.get('area_mm', 0))
                    # area_px might be N/A if csv missing, handle that
                    apx = b.get('area_px', 0)
                    if apx != 'N/A':
                         total_bub_px += float(apx)
                except:
                    pass
            
            self.stat_bub_area_mm.set(f"{total_bub_mm:.2f}")
            self.stat_bub_area_px.set(f"{total_bub_px:.0f}")
            
            # Ratios and Image Area MM
            # We need ratio mm^2/px to convert Image Area
            self.ratio_factor = 0.0
            if total_bub_px > 0:
                # ratio_factor = mm^2 per pixel
                self.ratio_factor = total_bub_mm / total_bub_px
                img_area_mm = img_area_px * self.ratio_factor
                self.stat_img_area_mm.set(f"{img_area_mm:.2f}")
                
                r_mm = (total_bub_mm / img_area_mm) * 100
                
                self.stat_ratio_mm.set(f"{r_mm:.2f} %")
            else:
                self.stat_img_area_mm.set("N/A")
                self.stat_ratio_mm.set("0.00 %")

            # --- Calculate StarDist List & Stats ---
            self.bubble_list_sd = []
            if self.current_json_details:
                self._generate_sd_list_and_stats(img_area_px)
            else:
                self.stat_sd_area_px.set("0")
                self.stat_sd_area_mm.set("0.0")
                self.stat_sd_ratio.set("0.00 %")

            # Triggers
            if self.on_bubble_list_update:
                self.on_bubble_list_update()
            
            if self.on_view_update:
                self.on_view_update()
                
        except Exception as e:
            print(f"Error loading data: {e}")

    def _calc_polygon_area(self, x, y):
        # Shoelace formula
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def _generate_sd_list_and_stats(self, img_area_px):
        try:
             # Reset list
            self.bubble_list_sd = []
            
            if not self.current_json_details:
                return

            points = self.current_json_details.get('points', [])
            coords = self.current_json_details.get('coord', [])
            
            total_sd_px = 0.0
            
            # Use max length of points or coords
            n_items = max(len(points) if points is not None else 0, len(coords) if coords is not None else 0)
            
            for i in range(n_items):
                 # 1. Center
                 cx, cy = 0, 0
                 if points is not None and i < len(points):
                     pt = points[i]
                     if pt is not None:
                         cy, cx = pt[0], pt[1] # JSON is usually [y, x]
                 
                 # 2. Area Px
                 area_px = 0.0
                 if coords is not None and i < len(coords):
                     c = coords[i]
                     # Parse coord (borrow logic)
                     arr = np.array(c)
                     poly = None
                     if arr.ndim == 2:
                         if arr.shape[0] == 2 and arr.shape[1] > 2: # (2, N) -> Transpose to (N, 2)
                             poly = arr.T
                         elif arr.shape[1] == 2: # (N, 2)
                             poly = arr
                     
                     if poly is not None:
                         # Poly is (Y, X) usually?
                         # _calc_polygon_area takes (x, y) arrays
                         # If poly is (y, x), pass (poly[:, 1], poly[:, 0])
                         area_px = self._calc_polygon_area(poly[:, 1], poly[:, 0])
                 
                 total_sd_px += area_px
                 
                 # 3. Area MM
                 area_mm = area_px * self.ratio_factor
                 
                 self.bubble_list_sd.append({
                     'stt': i + 1,
                     'cx': cx,
                     'cy': cy,
                     'area_px': area_px,
                     'area_mm': area_mm
                 })

            # Update Stats
            self.stat_sd_area_px.set(f"{total_sd_px:.0f}")
            
            if self.ratio_factor > 0:
                total_sd_mm = total_sd_px * self.ratio_factor
                self.stat_sd_area_mm.set(f"{total_sd_mm:.2f}")
                
                # StarDist Ratio
                sd_r_mm = (total_sd_mm / (img_area_px * self.ratio_factor)) * 100
                self.stat_sd_ratio.set(f"{sd_r_mm:.2f} %")
            else:
                self.stat_sd_area_mm.set("0.0")
                self.stat_sd_ratio.set("0.00 %")
                
        except Exception as e:
            print(f"Error generating SD list: {e}")

    def set_control_mode(self, mode):
        self.control_mode.set(mode)
        # Notify both control binding and bubble list update
        if self.on_control_mode_update:
            self.on_control_mode_update()
        if self.on_bubble_list_update:
            self.on_bubble_list_update()

    def toggle_view(self):
        if self.on_view_update:
            self.on_view_update()
