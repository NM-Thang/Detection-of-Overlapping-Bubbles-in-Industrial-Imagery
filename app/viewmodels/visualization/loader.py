import os
import csv
import json
import numpy as np
from PIL import Image
from app.utils.visualizer import Visualizer

class DataLoader:
    @staticmethod
    def load_image_data(root_path, img_filename):
        """
        Loads all related data for a specific image filename.
        Returns a dictionary with raw data.
        """
        if not root_path:
            return {}
            
        name_no_ext = os.path.splitext(img_filename)[0]
        
        img_path = os.path.join(root_path, 'imgs', img_filename)
        mask_path = os.path.join(root_path, 'SDmask', f"{name_no_ext}.png") 
        csv_path = os.path.join(root_path, 'csv', f"{name_no_ext}.csv")  # Changed: csv/{img}.csv
        json_path = os.path.join(root_path, 'JSMask', f"{name_no_ext}.json")
        
        data = {
            'original_img': None,
            'mask_img': None,
            'json_details': None,
            'bubble_list_rdc': [],
            'result_items': []
        }
        
        try:
            # 1. Load Original
            if os.path.exists(img_path):
                #data['original_img'] = np.array(Image.open(img_path).convert('L'))
                data['original_img'] = np.array(Image.open(img_path))

                
            # 2. Load Mask
            if os.path.exists(mask_path):
                data['mask_img'] = np.array(Image.open(mask_path)) 
                
            # 3. Load JSON
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        data['json_details'] = json.load(f)
                except Exception as e:
                    print(f"Error loading JSON: {e}")
            
            # 4. Load Bubble List from Pixel CSV (now includes Area_mm)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            data['bubble_list_rdc'].append({
                                'stt': row.get('STT'),
                                'cx': row.get('Center_X'),
                                'cy': row.get('Center_Y'),
                                'area_px': row.get('Area_px', row.get('Area', 0)),  # Backward compat
                                'area_mm': row.get('Area_mm', 0),
                            })
                except Exception as e:
                    print(f"Error reading Pixel CSV: {e}")
            
            # 5. Visualizer Items (Hybrid: Type=0 uses JSON, Type=1 uses rays)
            if os.path.exists(csv_path):
                data['result_items'] = Visualizer.get_visual_items(img_path, csv_path, json_path)
                
        except Exception as e:
            print(f"Error loading image data: {e}")
            
        return data

    @staticmethod
    def load_metadata(path):
        """Loads list of images from metadata.txt"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            return [line.split(',')[0].strip() for line in lines if line.strip()]
        except:
            return []
