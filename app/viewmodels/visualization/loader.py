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
        csv_path = os.path.join(root_path, 'results', name_no_ext, f"{name_no_ext}_pixel.csv")
        csv_mm_path = os.path.join(root_path, 'results', name_no_ext, f"{name_no_ext}_mm.csv")
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
                data['original_img'] = np.array(Image.open(img_path).convert('L'))
                
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
            
            # 4. Load CSVs (RDC List)
            # Use mm csv for list details
            if os.path.exists(csv_mm_path):
                try:
                    with open(csv_mm_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            data['bubble_list_rdc'].append({
                                'stt': row.get('STT'),
                                'cx': row.get('Center_X'),
                                'cy': row.get('Center_Y'),
                                'area_mm': row.get('Area'),
                                'pixels': "N/A"
                            })
                except Exception as e:
                     print(f"Error reading MM CSV: {e}")
                     
            # Decorate with Pixel Area if available
            if os.path.exists(csv_path):
                 try:
                     with open(csv_path, 'r') as f:
                        reader = csv.DictReader(f)
                        for i, row in enumerate(reader):
                            if i < len(data['bubble_list_rdc']):
                                data['bubble_list_rdc'][i]['area_px'] = row.get('Area')
                 except Exception as e:
                      print(f"Error reading Pixel CSV: {e}")
            
            # 5. Visualizer Items
            if os.path.exists(csv_path):
                # We assume Visualizer util handles this correctly
                data['result_items'] = Visualizer.get_visual_items(img_path, csv_path)
                
        except Exception as e:
            print(f"Error loading image data: {e}")
            
        return data

    @staticmethod
    def load_metadata(path):
        """Loads list of images from metadata.txt"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            return [line.strip() for line in lines if line.strip()]
        except:
            return []
