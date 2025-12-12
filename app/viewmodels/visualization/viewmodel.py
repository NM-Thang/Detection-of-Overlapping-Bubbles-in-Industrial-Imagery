import tkinter as tk
import os
import threading
import numpy as np
from tkinter import filedialog, messagebox

from .loader import DataLoader
from .stats import StatsCalculator

class VisualizationViewModel:
    def __init__(self, root):
        self.root = root
        
        # Paths
        self.metadata_path = tk.StringVar(value="")
        self.current_root_path = None
        self.image_list = []
        
        # State
        self.control_mode = tk.StringVar(value="Normal") # Normal, Zoom, Pan
        self.show_result = tk.BooleanVar(value=True)
        self.show_mask = tk.BooleanVar(value=False)
        self.show_original = tk.BooleanVar(value=True)
        
        # Data Cache
        self.current_image_idx = -1
        self.current_data = {
            'original_img': None,
            'mask_img': None,
            'json_details': None,
            'bubble_list_rdc': [],
            'result_items': []
        }

        # UI Bindings - Image List
        self.on_image_list_update = None
        
        # UI Bindings - Bubble List
        self.on_bubble_list_update = None
        
        # UI Bindings - Visualization Update
        self.on_view_update = None
        self.on_control_mode_update = None
        
        # Stats Variables
        self.stat_img_size = tk.StringVar(value="N/A")
        self.stat_bubble_count = tk.StringVar(value="0")
        self.stat_bub_area_mm = tk.StringVar(value="0.0")
        self.stat_bub_area_px = tk.StringVar(value="0")
        self.stat_img_area = tk.StringVar(value="0.0")
        self.stat_ratio_mm = tk.StringVar(value="0.0 %")
        
        self.stat_sd_count = tk.StringVar(value="0")
        self.stat_sd_prob = tk.StringVar(value="0.0")
        self.stat_sd_area_px = tk.StringVar(value="0")
        self.stat_sd_area_mm = tk.StringVar(value="0.0")
        self.stat_sd_ratio = tk.StringVar(value="0.0 %")
    
    @property
    def current_original_img(self):
        return self.current_data['original_img']

    @property
    def current_mask_img(self):
        return self.current_data['mask_img']

    @property
    def current_json_details(self):
        return self.current_data['json_details']
        
    @property
    def current_result_items(self):
        return self.current_data['result_items']

    @property
    def bubble_list(self):
        return self.current_data['bubble_list_rdc']
        

        
    def select_metadata(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            self.load_metadata_from_path(path)
            
    def load_metadata_from_path(self, path):
        self.metadata_path.set(path)
        self.current_root_path = os.path.dirname(path)
        self.image_list = DataLoader.load_metadata(path)
        
        if self.on_image_list_update:
            self.on_image_list_update()
            
        if self.image_list:
            self.select_image(0)
            


    def get_rdc_bubbles(self):
        return self.current_data['bubble_list_rdc']
        


    # Fixing select_image to cache sd_list
    def select_image(self, idx):
        if idx < 0 or idx >= len(self.image_list):
            return
            
        self.current_image_idx = idx
        filename = self.image_list[idx]
        
        self.current_data = DataLoader.load_image_data(self.current_root_path, filename)
        
        stats = StatsCalculator.calc_img_stats(
            self.current_data['original_img'], 
            self.current_data['bubble_list_rdc']
        )
        
        self.stat_img_size.set(stats['size'])
        self.stat_bubble_count.set(stats['count'])
        self.stat_bub_area_mm.set(stats['total_bub_mm'])
        self.stat_bub_area_px.set(stats['total_bub_px'])
        self.stat_img_area.set(stats['img_area_mm'])
        self.stat_ratio_mm.set(stats['ratio_mm'])
        
        ratio_factor = stats.get('ratio_factor', 0)
        img_area_px = stats.get('img_area_px', 0)
        
        sd_stats = StatsCalculator.calc_stardist_stats(
            self.current_data['json_details'],
            ratio_factor,
            img_area_px
        )
        self.stat_sd_count.set(sd_stats['count'])
        self.stat_sd_prob.set(sd_stats['prob'])
        self.stat_sd_area_px.set(sd_stats['area_px'])
        self.stat_sd_area_mm.set(sd_stats['area_mm'])
        self.stat_sd_ratio.set(sd_stats['ratio'])
        
        self._cached_sd_list = sd_stats['list'] # Cache here
        
        if self.on_bubble_list_update:
            self.on_bubble_list_update()
            
        if self.on_view_update:
            self.on_view_update()

    def get_sd_bubbles(self):
        return getattr(self, '_cached_sd_list', [])

    def get_visual_items(self):
        return self.current_data['result_items']
        
    def get_stardist_visual_items(self):
        # Convert raw JSON details into list of visual items for BubbleStepper
        details = self.current_data['json_details']
        if not details or 'coord' not in details:
            return []
            
        coords = details.get('coord', [])
        curr_probs = details.get('prob', [])
        centers = details.get('points', [])
        
        items = []
        for i, poly in enumerate(coords):
            try:
                # Normalize polygon shape to (N, 2) -> [[y, x], ...]
                poly_arr = np.array(poly)
                if poly_arr.shape[0] == 2 and poly_arr.shape[1] > 2:
                    # (2, N) -> Transpose to (N, 2)
                    pts = poly_arr.T
                elif poly_arr.shape[1] == 2 and poly_arr.shape[0] > 2:
                    pts = poly_arr
                else:
                    continue
                    
                prob = curr_probs[i] if i < len(curr_probs) else 0
                center = centers[i] if i < len(centers) else None
                
                # Create item dict compatible with BubbleStepper (mimicking 'rdc' type)
                item = {
                    'type': 'rdc', # Reuse 'rdc' type for polygon drawing
                    'points': pts, # Expects (N, 2) [y, x]
                    'center': center, # Needed for drawing rays
                    'color': 'lime',
                    'prob': prob,
                    'stt': i + 1,
                    'pixel_count': 'N/A' # Optional
                }
                items.append(item)
            except Exception as e:
                print(f"Error converting StarDist item {i}: {e}")
                
        return items

    def toggle_view(self):
        if self.on_view_update:
            self.on_view_update()
            
    def set_control_mode(self, mode):
        self.control_mode.set(mode)
        if self.on_control_mode_update:
            self.on_control_mode_update()
