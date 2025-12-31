import csv
import json
import os
import math
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from app.utils.starbub import BubbleStepper

class Visualizer:
    @staticmethod
    def get_visual_items(img_path, csv_path, json_path=None):
        """
        Parses CSV and returns visual items list for BubbleStepper.
        Hybrid mode: 
        - Type=1 (collision) → Reconstruct from 64 rays
        - Type=0 (no collision) → Use coords from JSON
        """
        visual_items = []
        
        # Load JSON coords if available
        json_coords = []
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                    json_coords = json_data.get('coord', [])
            except Exception as e:
                print(f"Error loading JSON for hybrid: {e}")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    try:
                        cx = float(row.get('Center_X', 0))
                        cy = float(row.get('Center_Y', 0))
                        
                        # Read collision type (1=collision, 0=no collision)
                        bubble_type = int(row.get('Type', 1))  # Default to collision for backward compat
                        
                        # Hybrid Logic
                        if bubble_type == 0 and idx < len(json_coords):
                            # Non-collision → Use JSON coords directly
                            poly = np.array(json_coords[idx])
                            if poly.shape[0] == 2 and poly.shape[1] > 2:
                                points = poly.T  # (2, N) → (N, 2)
                            elif poly.shape[1] == 2 and poly.shape[0] > 2:
                                points = poly  # Already (N, 2)
                            else:
                                # Fallback to rays if shape is unexpected
                                points = Visualizer._reconstruct_from_rays(row, cx, cy)
                        else:
                            # Collision → Reconstruct from 64 rays
                            points = Visualizer._reconstruct_from_rays(row, cx, cy)
                        
                        # Area (with backward compat for old 'Area' column)
                        area = float(row.get('Area_px', row.get('Area', 0)))
                        stt = row.get('STT')

                        visual_items.append({
                            'type': 'rdc',
                            'stt': stt,
                            'points': points,
                            'center': [cy, cx],  # [Row, Col]
                            'color': tuple(np.random.random(3)), 
                            'dists': Visualizer._get_rays(row),
                            'pixel_count': int(area),
                            'is_collision': bubble_type == 1
                        })
                        
                    except ValueError:
                        continue
            return visual_items
        except Exception as e:
            print(f"Error parsing visual items: {e}")
            return []

    @staticmethod
    def _get_rays(row):
        """Extract 64 rays from CSV row."""
        rays = []
        for i in range(64):
            key = f"Ray_{i+1}"
            val = float(row.get(key, 0))
            rays.append(val)
        return np.array(rays)

    @staticmethod
    def _reconstruct_from_rays(row, cx, cy):
        """Reconstruct polygon from 64 rays using polar to cartesian conversion."""
        rays = Visualizer._get_rays(row)
        points = []
        for i in range(64):
            angle = 2 * math.pi * i / 64
            r = rays[i]
            
            # Standard Polar to Image Coords
            # Y = Row, X = Col
            bg_row = cy + r * math.sin(angle)
            bg_col = cx + r * math.cos(angle)
            
            points.append([bg_row, bg_col])
            
        return np.array(points)
