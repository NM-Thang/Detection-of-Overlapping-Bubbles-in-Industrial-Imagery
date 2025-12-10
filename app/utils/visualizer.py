import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from app.utils.starbub import BubbleStepper

class Visualizer:
    @staticmethod
    def get_visual_items(img_path, csv_path):
        """
        Parses CSV and returns visual items list for BubbleStepper.
        """
        visual_items = []
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        cx = float(row.get('Center_X', 0))
                        cy = float(row.get('Center_Y', 0))
                        
                        # Rays
                        rays = []
                        for i in range(64):
                            key = f"Ray_{i+1}"
                            val = float(row.get(key, 0))
                            rays.append(val)
                        rays = np.array(rays)
                        
                        # Reconstruct Polygon Points
                        points = []
                        for i in range(64):
                            angle = 2 * math.pi * i / 64
                            r = rays[i]
                            
                            # Standard Polar to Image Coords
                            # Y = Row, X = Col
                            bg_row = cy + r * math.sin(angle)
                            bg_col = cx + r * math.cos(angle)
                            
                            points.append([bg_row, bg_col])
                            
                        points = np.array(points)
                        
                        # Area in this CSV (if pixel csv) is pixel count
                        area = float(row.get('Area', 0))
                        stt = row.get('STT') # Get STT

                        visual_items.append({
                            'type': 'rdc',
                            'stt': stt,
                            'points': points,
                            'center': [cy, cx], # [Row, Col]
                            'color': tuple(np.random.random(3)), 
                            'dists': rays,
                            'pixel_count': int(area)
                        })
                        
                    except ValueError:
                        continue
            return visual_items
        except Exception as e:
            print(f"Error parsing visual items: {e}")
            return []

    @staticmethod
    def load_and_visualize(img_path, csv_path, metric_val=1.0):
        """
        Loads image and CSV, reconstructs shapes, and launches BubbleStepper (Standalone).
        """
        try:
            img = np.array(Image.open(img_path).convert('L'))
            visual_items = Visualizer.get_visual_items(img_path, csv_path)
            
            if not visual_items:
                return False, "No items found in CSV."

            # Launch Viewer in new window (Blocking Main Thread)
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(img, cmap='gray')
            ax.set_title(f"Re-visualization: {os.path.basename(img_path)}")
            
            stepper = BubbleStepper(ax, visual_items)
            return True, "Visualization closed."
            
        except Exception as e:
            return False, f"Error visualizing: {e}"
