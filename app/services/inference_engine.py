import os
if os.name == 'nt':
    import ctypes
    sys_path = r"C:\path\to\your\dlls" # Placeholder if needed, otherwise ignore
    # os.add_dll_directory(sys_path)

from app.utils.io_manager import IOManager
from app.services.model_service import ModelService
from app.utils.data_saver import DataSaver

class InferenceEngine:
    def __init__(self):
        self.io = IOManager()
        self.model_service = ModelService()
        self.saver = DataSaver()

    def load_models(self, sd_path, rdc_path):
        return self.model_service.load_models(sd_path, rdc_path)

    def process_batch(self, input_data, metric, progress_callback=None):
        """
        Runs prediction on images using the new Facade pattern.
        """
        # 1. Standardize Input
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

        # 2. IO Preparation Phase
        # We process linearly to keep feedback simple, 
        # but technically we could prepare all then process all.
        # Sticking to per-item loop for compatibility with progress bars.
        
        processed_count = 0
        root_dir_for_metadata = None
        
        for idx, img_path in enumerate(image_files):
            img_name = os.path.splitext(os.path.basename(img_path))[0]
            
            if progress_callback:
                progress_callback(processed_count, total_files, f"Processing {img_name}...")

            try:
                # A. Prepare Directory Structure
                dest_path, results_dir = self.io.prepare_file_structure(img_path)
                if not dest_path:
                    continue
                
                # Capture root dir for metadata (from the first valid item)
                if root_dir_for_metadata is None:
                    root_dir_for_metadata = os.path.dirname(results_dir)

                # B. Predict
                labels, details, bubbles, _ = self.model_service.predict(dest_path, metric)
                
                # C. Save
                self.saver.save_results(results_dir, img_name, labels, details, bubbles, metric)
                
                processed_count += 1
                
            except Exception as e:
                print(f"Failed to process {img_name}: {e}")

        # 3. Finalize
        if processed_count > 0 and root_dir_for_metadata:
             self.io.generate_metadata(root_dir_for_metadata)

        if progress_callback:
             progress_callback(processed_count, processed_count, "Done!")
        
        return processed_count, root_dir_for_metadata
