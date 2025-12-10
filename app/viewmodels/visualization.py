import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
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
        
        self.bubble_list = [] # List of dicts: {stt, x, y, area_px, area_mm}
        
        # Display Options
        self.show_original = tk.BooleanVar(value=False)
        self.show_mask = tk.BooleanVar(value=False)
        self.show_result = tk.BooleanVar(value=True) # Default on
        
        # Current Loaded Data
        self.current_original_img = None
        self.current_mask_img = None
        self.current_result_items = None
        self.current_img_name = ""
        
        # Statistics
        self.stat_img_size = tk.StringVar(value="N/A")
        self.stat_bubble_count = tk.StringVar(value="0")
        self.stat_bub_area_mm = tk.StringVar(value="0.0")
        self.stat_bub_area_px = tk.StringVar(value="0.0")
        self.stat_img_area_mm = tk.StringVar(value="0.0")
        self.stat_ratio_mm = tk.StringVar(value="0.0 %")
        
        # Callbacks
        self.on_image_list_update = None
        self.on_bubble_list_update = None
        self.on_view_update = None

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
                
            # 3. Load Results (CSV) & Parse Bubble List
            self.bubble_list = []
            
            # We use mm csv for the List details (Area mm^2)
            if os.path.exists(csv_mm_path):
                with open(csv_mm_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Headers: STT, Center_X, Center_Y, Axis_1, Axis_2, Area, Type, Ray_...
                        self.bubble_list.append({
                            'stt': row.get('STT'),
                            'cx': row.get('Center_X'),
                            'cy': row.get('Center_Y'),
                            'area_mm': row.get('Area'),
                            'pixels': "N/A" # Count from mask? Or Pixel CSV Area?
                        })
            
            # If we want pixel area, we could read pixel csv too.
            if os.path.exists(csv_path):
                 with open(csv_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        if i < len(self.bubble_list):
                            self.bubble_list[i]['area_px'] = row.get('Area')
            
            # Prepare Visualizer Items (Using Visualizer util or custom)
            # The Visualizer util does full reconstruction.
            # We need to retrieve the 'VisualItems' list for the Stepper.
            # Visualizer.load_and_visualize returns None, it launches plotting.
            # We need to expose a method in Visualizer to just GET the items.
            # For now, let's use the Visualizer class to parse only.
            
            if os.path.exists(csv_path):
                self.current_result_items = Visualizer.get_visual_items(img_path, csv_path)
            else:
                self.current_result_items = []

            # --- Calculate Statistics ---
            img_h, img_w = self.current_original_img.shape
            img_area_px = img_h * img_w
            self.stat_img_size.set(f"{img_w} x {img_h}")
            self.stat_bubble_count.set(str(len(self.bubble_list)))
            
            total_bub_mm = 0.0
            total_bub_px = 0.0
            
            for b in self.bubble_list:
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
            if total_bub_px > 0:
                # ratio_factor = mm^2 per pixel
                ratio_factor = total_bub_mm / total_bub_px
                img_area_mm = img_area_px * ratio_factor
                self.stat_img_area_mm.set(f"{img_area_mm:.2f}")
                
                r_mm = (total_bub_mm / img_area_mm) * 100
                
                self.stat_ratio_mm.set(f"{r_mm:.2f} %")
            else:
                self.stat_img_area_mm.set("N/A")
                self.stat_ratio_mm.set("0.00 %")
                
            # Triggers
            if self.on_bubble_list_update:
                self.on_bubble_list_update()
            
            if self.on_view_update:
                self.on_view_update()
                
        except Exception as e:
            print(f"Error loading data: {e}")

    def toggle_view(self):
        if self.on_view_update:
            self.on_view_update()
