import os
import json
import numpy as np
from PIL import Image

from app.utils.io_manager import IOManager
from app.services.model_service import ModelService
from app.utils.data_saver import DataSaver
from app.utils.preprocessor import preprocess_pipeline, load_flat_frame

class InferenceEngine:
    def __init__(self):
        self.io = IOManager()
        self.model_service = ModelService()
        self.saver = DataSaver()

    def load_models(self, sd_path, rdc_path):
        return self.model_service.load_models(sd_path, rdc_path)

    def process_batch(self, input_data, metric, progress_callback=None, preprocessing_config=None):
        """
        Runs prediction on images with optional preprocessing.
        
        Args:
            input_data: Folder path or list of file paths
            metric: Pixel to mm conversion factor
            progress_callback: Function(current, total, message)
            preprocessing_config: dict with preprocessing options (from ViewModel)
        """
        # Default config if not provided
        if preprocessing_config is None:
            preprocessing_config = {
                'use_flatfield': False,
                'use_dog': False,
                'use_lanczos': False,
            }

        # 1. Gather image files
        image_files = []
        if isinstance(input_data, str):
            if os.path.isdir(input_data):
                image_files = self.io.get_image_files(input_data)
        elif isinstance(input_data, (list, tuple)):
            image_files = list(input_data)
            
        total_files = len(image_files)
        if total_files == 0:
            print("No images to process")
            return 0, None

        # 2. Load flat_frame once if flatfield is enabled
        flat_frame = None
        if preprocessing_config.get('use_flatfield'):
            # Check if flat_frame is already provided (from generation)
            if preprocessing_config.get('flat_frame') is not None:
                flat_frame = preprocessing_config.get('flat_frame')
                print(f"Using generated flatfield ({flat_frame.shape[1]}x{flat_frame.shape[0]})")
            else:
                # Load from file
                flat_path = preprocessing_config.get('flatfield_ref_path')
                if flat_path and os.path.exists(flat_path):
                    flat_frame = load_flat_frame(flat_path)
                    print(f"Loaded flatfield reference: {flat_path}")
                else:
                    print("Warning: Flatfield enabled but no reference image found. Skipping flatfield.")
                    preprocessing_config['use_flatfield'] = False
        
        # Build effective config with loaded flat_frame
        effective_config = preprocessing_config.copy()
        effective_config['flat_frame'] = flat_frame
        
        processed_count = 0
        root_dir_for_metadata = None
        preprocessed_folder = None
        
        for idx, img_path in enumerate(image_files):
            img_name = os.path.splitext(os.path.basename(img_path))[0]
            
            if progress_callback:
                progress_callback(processed_count, total_files, f"Processing {img_name}...")

            try:
                # A. Prepare Directory Structure (original image is copied/moved)
                dest_path, root_dir = self.io.prepare_file_structure(img_path)
                if not dest_path:
                    continue
                
                # Capture root dir for metadata (from the first valid item)
                if root_dir_for_metadata is None:
                    root_dir_for_metadata = root_dir
                    
                    # Create preprocessed folder and save config once
                    preprocessed_folder = os.path.join(root_dir, 'preprocessed')
                    os.makedirs(preprocessed_folder, exist_ok=True)
                    
                    # Save preprocessing config to JSON
                    config_to_save = {
                        'use_flatfield': preprocessing_config.get('use_flatfield', False),
                        'flatfield_source': 'generated' if preprocessing_config.get('flat_frame') is not None else preprocessing_config.get('flatfield_ref_path'),
                        'use_dog': preprocessing_config.get('use_dog', False),
                        'dog_sigma1': preprocessing_config.get('dog_sigma1', 2.0),
                        'dog_sigma2': preprocessing_config.get('dog_sigma2', 20.0),
                        'use_lanczos': preprocessing_config.get('use_lanczos', False),
                        'lanczos_scale': preprocessing_config.get('lanczos_scale', 1),
                    }
                    config_path = os.path.join(preprocessed_folder, 'preprocessing_config.json')
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_to_save, f, indent=2, ensure_ascii=False)
                    print(f"Saved preprocessing config to: {config_path}")

                # B. Load image as grayscale for preprocessing
                try:
                    pil_img = Image.open(dest_path).convert('L')
                    img_gray = np.array(pil_img)
                except Exception as e:
                    print(f"Failed to load image: {dest_path} - {e}")
                    continue
                
                # C. Apply preprocessing pipeline
                preprocessed, scale_factor = preprocess_pipeline(img_gray, effective_config)
                
                # D. Save preprocessed image for debugging
                if preprocessed_folder:
                    preprocessed_path = os.path.join(preprocessed_folder, f"{img_name}.png")
                    Image.fromarray(preprocessed).save(preprocessed_path)
                
                # E. Predict (with automatic scaling back)
                labels, details, bubbles = self.model_service.predict_from_array(
                    preprocessed, metric, scale_factor
                )
                
                # F. Save results (already at original scale)
                self.saver.save_results(root_dir, img_name, labels, details, bubbles, metric)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Failed to process {img_name}: {e}")
                import traceback
                traceback.print_exc()

        # 3. Finalize
        if processed_count > 0 and root_dir_for_metadata:
             self.io.generate_metadata(root_dir_for_metadata, metric=metric)

        if progress_callback:
             progress_callback(processed_count, processed_count, "Done!")
        
        return processed_count, root_dir_for_metadata
