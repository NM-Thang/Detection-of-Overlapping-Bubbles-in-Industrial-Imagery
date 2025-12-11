import os
import glob
import shutil

class IOManager:
    def get_image_files(self, input_folder):
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(input_folder, ext)))
        return sorted(files)

    def prepare_file_structure(self, img_path):
        """
        Prepares the 'imgs' and 'results' folder structure for a given image.
        Moves the image to 'imgs' if it's not already there (or in a compatible structure).
        Returns:
            dest_path: The path of the image in the 'imgs' folder (or where it should be processed from).
            results_dir: The directory where results for this image's batch should be stored.
        """
        if not os.path.exists(img_path):
            return None, None
            
        parent_dir = os.path.dirname(img_path)
        base_name = os.path.basename(img_path)
        
        imgs_dir = os.path.join(parent_dir, 'imgs')
        results_dir = os.path.join(parent_dir, 'results')

        # Logic to determine if we are already inside an 'imgs' folder structure
        # to avoid double nesting like .../imgs/imgs
        if os.path.basename(parent_dir) == 'imgs':
            # Already in imgs. 
            # Results should go to sibling 'results'.
            root_context = os.path.dirname(parent_dir)
            imgs_dir = parent_dir # Stay here
            results_dir = os.path.join(root_context, 'results')
            dest_path = img_path # No move needed
        else:
            # Normal case
            try:
                os.makedirs(imgs_dir, exist_ok=True)
                os.makedirs(results_dir, exist_ok=True)
                dest_path = os.path.join(imgs_dir, base_name)
                
                if img_path != dest_path:
                    if not os.path.exists(dest_path):
                        shutil.move(img_path, dest_path)
                    else:
                        # Destination exists. Use it.
                        pass
            except Exception as e:
                print(f"IO Error preparing structure for {img_path}: {e}")
                return None, None
                
        return dest_path, results_dir

    def generate_metadata(self, root_dir):
        """
        Generates metadata.txt in the root directory listing all valid images in the 'imgs' subdirectory.
        """
        if not root_dir:
            return

        try:
            imgs_dir = os.path.join(root_dir, 'imgs')
            if os.path.exists(imgs_dir):
                meta_path = os.path.join(root_dir, 'metadata.txt')
                existing_files = sorted(os.listdir(imgs_dir))
                valid_imgs = [f for f in existing_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp'))]
                
                with open(meta_path, 'w') as f:
                    for fname in valid_imgs:
                        f.write(f"{fname}\n")
        except Exception as e:
            print(f"Failed to generate metadata: {e}")
