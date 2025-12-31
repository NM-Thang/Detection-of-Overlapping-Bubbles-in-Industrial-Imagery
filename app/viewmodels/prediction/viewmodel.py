import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import cv2
import numpy as np
from PIL import Image, ImageTk
from app.services.inference_engine import InferenceEngine
from app.utils.validators import validate_directory_path, validate_metric
from app.utils.preprocessor import generate_flat_frame, load_flat_frame

class PredictionViewModel:
    def __init__(self, root):
        self.root = root
        self.engine = InferenceEngine()
        
        # State Variables
        self.model_status = tk.StringVar(value="Models Not Loaded")
        
        # Default Paths
        base_model_dir = os.path.abspath(os.path.join(os.getcwd(), 'Models'))
        default_sd = os.path.join(base_model_dir, 'SDmodel', 'data_mix_64_400')
        default_rdc = os.path.join(base_model_dir, 'RDC', 'rdc_model_mm.h5')
        
        self.sd_model_path = tk.StringVar(value=default_sd if os.path.exists(default_sd) else "")
        self.rdc_model_path = tk.StringVar(value=default_rdc if os.path.exists(default_rdc) else "")
        
        self.input_mode = tk.StringVar(value="Folder") # "Folder" or "Files"
        self.input_path_display = tk.StringVar(value="")
        self.selected_files = [] # Store file paths if mode is Files
        
        self.metric = tk.StringVar(value="5.2E-2") 
        self.progress_text = tk.StringVar(value="Ready")
        self.progress_value = tk.DoubleVar(value=0.0)
        
        # Logic Flags
        self.is_processing = tk.BooleanVar(value=False)
        self.models_are_loaded = tk.BooleanVar(value=False)
        self.can_visualize = tk.BooleanVar(value=False)
        
        self.last_result_root = None
        self.on_transfer_request = None
        
        # Preprocessing Options
        # Flatfield
        self.use_flatfield = tk.BooleanVar(value=False)
        self.flatfield_ref_path = tk.StringVar(value="")
        self.flat_source = tk.StringVar(value="load")  # "load" or "generate"
        self.flat_gen_images = []  # List of image paths for generation
        self.flat_gen_count = tk.StringVar(value="0 images selected")
        self.flat_smooth_method = tk.StringVar(value="resize")  # "blur", "resize", "none"
        self.flat_blur_kernel = tk.StringVar(value="151")
        self.flat_shrink_size = tk.StringVar(value="30")
        self.flat_gen_status = tk.StringVar(value="")
        self.generated_flat = None  # Cached generated flat frame
        
        # DoG (Difference of Gaussians)
        self.use_dog = tk.BooleanVar(value=False)
        self.dog_sigma1 = tk.StringVar(value="2.0")
        self.dog_sigma2 = tk.StringVar(value="20.0")
        
        # Lanczos Upscale
        self.use_lanczos = tk.BooleanVar(value=False)
        self.lanczos_scale = tk.IntVar(value=2)

    def select_sd_model(self):
        path = filedialog.askdirectory(title="Select StarDist Model Folder (e.g. data_mix_64_400)")
        if path:
            self.sd_model_path.set(path)
            self._reset_model_status()

    def select_rdc_model(self):
        if messagebox.askyesno("Select RDC Model Type", "Do you want to select a Folder containing the SavedModel?\n\nYes: Select Folder\nNo: Select .h5 File"):
            path = filedialog.askdirectory(title="Select RDC Model Folder")
        else:
            path = filedialog.askopenfilename(title="Select RDC Model File", filetypes=[("H5 Files", "*.h5"), ("All Files", "*.*")])
            
        if path:
            self.rdc_model_path.set(path)
            self._reset_model_status()
            
    def _reset_model_status(self):
        self.model_status.set("Not Loaded (Changed)")
        self.models_are_loaded.set(False)

    def select_flatfield_ref(self):
        """Select flatfield reference image."""
        path = filedialog.askopenfilename(
            title="Select Flatfield Reference Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
        )
        if path:
            self.flatfield_ref_path.set(path)
    
    def select_flat_gen_images(self):
        """Select multiple images for flat frame generation."""
        paths = filedialog.askopenfilenames(
            title="Select Images for Flat Generation (same illumination)",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
        )
        if paths:
            self.flat_gen_images = list(paths)
            self.flat_gen_count.set(f"{len(paths)} images selected")
            self.flat_gen_status.set("")
            self.generated_flat = None
    
    def generate_flat_frame(self):
        """Generate flat frame from selected images in background."""
        if not self.flat_gen_images:
            messagebox.showwarning("Warning", "Please select images first!")
            return
        
        min_frames = 100
        if len(self.flat_gen_images) < min_frames:
            messagebox.showwarning("Warning", f"Need at least {min_frames} images for good flat generation!\n\nYou selected {len(self.flat_gen_images)} images.")
            return
        
        self.flat_gen_status.set("Generating...")
        
        def _generate():
            try:
                smooth_method = self.flat_smooth_method.get()
                blur_kernel = int(self.flat_blur_kernel.get() or 151)
                shrink_factor = int(self.flat_shrink_size.get() or 30)
                
                def progress_cb(current, total):
                    self.root.after(0, lambda: self.flat_gen_status.set(f"Loading {current}/{total}..."))
                
                flat = generate_flat_frame(
                    self.flat_gen_images,
                    smooth_method=smooth_method,
                    blur_kernel=blur_kernel,
                    shrink_factor=shrink_factor,
                    progress_callback=progress_cb
                )
                
                self.generated_flat = flat
                self.root.after(0, lambda: self.flat_gen_status.set(f"✓ Generated ({flat.shape[1]}x{flat.shape[0]})"))
            except Exception as ex:
                err_msg = str(ex)
                self.root.after(0, lambda m=err_msg: self.flat_gen_status.set(f"Error: {m[:30]}"))
                self.root.after(0, lambda m=err_msg: messagebox.showerror("Generation Error", m))
        
        threading.Thread(target=_generate, daemon=True).start()
    
    def preview_flat_frame(self):
        """Show preview of current flat frame."""
        flat = None
        
        if self.flat_source.get() == "load":
            path = self.flatfield_ref_path.get()
            if path and os.path.exists(path):
                flat = load_flat_frame(path)
            else:
                messagebox.showwarning("Warning", "Please select a flat reference image first!")
                return
        else:
            if self.generated_flat is None:
                messagebox.showwarning("Warning", "Please generate a flat frame first!")
                return
            flat = self.generated_flat
        
        # Show in new window
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Flat Frame Preview")
        preview_win.geometry("600x500")
        
        # Convert to display image
        h, w = flat.shape
        # Resize for display if too large
        max_size = 500
        scale = min(max_size / w, max_size / h, 1.0)
        disp_w, disp_h = int(w * scale), int(h * scale)
        disp_img = cv2.resize(flat, (disp_w, disp_h))
        
        pil_img = Image.fromarray(disp_img)
        photo = ImageTk.PhotoImage(pil_img)
        
        lbl = tk.Label(preview_win, image=photo)
        lbl.image = photo  # Keep reference
        lbl.pack(expand=True)
        
        info = f"Size: {w}x{h} | Mean: {flat.mean():.1f} | Min: {flat.min()} | Max: {flat.max()}"
        tk.Label(preview_win, text=info).pack(pady=5)
    
    def get_preprocessing_config(self):
        """Build preprocessing config dict from UI state."""
        # Determine flat frame to use
        flat_frame = None
        flat_path = None
        
        if self.use_flatfield.get():
            if self.flat_source.get() == "load":
                flat_path = self.flatfield_ref_path.get()
            elif self.generated_flat is not None:
                flat_frame = self.generated_flat
        
        config = {
            'use_flatfield': self.use_flatfield.get(),
            'flatfield_ref_path': flat_path,
            'flat_frame': flat_frame,  # Direct array if generated
            'use_dog': self.use_dog.get(),
            'dog_sigma1': float(self.dog_sigma1.get() or 2.0),
            'dog_sigma2': float(self.dog_sigma2.get() or 20.0),
            'use_lanczos': self.use_lanczos.get(),
            'lanczos_scale': self.lanczos_scale.get() if self.use_lanczos.get() else 1,
        }
        return config

    def select_input(self):
        mode = self.input_mode.get()
        if mode == "Folder":
            path = filedialog.askdirectory()
            if path:
                self.input_path_display.set(path)
                self.selected_files = [] 
        else:
            files = filedialog.askopenfilenames(
                title="Select Images",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")]
            )
            if files:
                self.selected_files = list(files)
                count = len(files)
                self.input_path_display.set(f"{count} files selected")

    def load_models(self):
        if self.is_processing.get():
            return

        self.model_status.set("Loading...")
        self.is_processing.set(True)
        
        def _task():
            sd_path = self.sd_model_path.get()
            rdc_path = self.rdc_model_path.get()
            
            success, msg = self.engine.load_models(sd_path, rdc_path)
            
            def _update():
                self.is_processing.set(False)
                if success:
                    self.model_status.set("Models Loaded") 
                    self.models_are_loaded.set(True)
                else:
                    self.model_status.set("Error: " + msg) 
                    self.models_are_loaded.set(False)
                    messagebox.showerror("Model Load Error", msg)
            self.root.after(0, _update)

        threading.Thread(target=_task, daemon=True).start()

    def start_processing(self):
        if self.is_processing.get():
            return
            
        # 1. Validate Input
        mode = self.input_mode.get()
        input_data = None
        
        if mode == "Folder":
            folder = self.input_path_display.get()
            valid_folder, msg_folder = validate_directory_path(folder)
            if not valid_folder:
                messagebox.showwarning("Invalid Input", f"Folder error: {msg_folder}")
                return
            input_data = folder
            self.last_input_context = folder
        else:
            if not self.selected_files:
                messagebox.showwarning("Invalid Input", "No files selected.")
                return
            input_data = self.selected_files
            if self.selected_files:
                self.last_input_context = os.path.dirname(self.selected_files[0])

        # 2. Validate Metric
        metric_str = self.metric.get()
        valid_metric, msg_metric = validate_metric(metric_str)
        try:
            metric_val = float(metric_str)
            if metric_val <= 0: raise ValueError
        except:
            messagebox.showwarning("Invalid Input", "Metric must be a positive number.")
            return

        # 3. Check Models
        if not self.models_are_loaded.get():
            messagebox.showwarning("Models Required", "Please load models first.")
            return

        # 4. Validate Preprocessing Options
        if self.use_flatfield.get():
            if self.flat_source.get() == "load":
                if not self.flatfield_ref_path.get():
                    messagebox.showwarning("Flatfield Error", "Flatfield correction is enabled but no reference image is selected.\n\nPlease select a flatfield reference image or disable the option.")
                    return
            else:  # generate mode
                if self.generated_flat is None:
                    messagebox.showwarning("Flatfield Error", "Flatfield correction is enabled but flat frame has not been generated.\n\nPlease generate a flat frame first or switch to load mode.")
                    return

        # Start Batch Processing
        self.is_processing.set(True)
        self.progress_value.set(0)
        self.progress_text.set("Initializing...")
        
        def _bg_task():
            def _progress(current, total, msg):
                def _ui_update():
                    self.progress_text.set(f"{msg}")
                    if total > 0:
                         percent = (current / total) * 100
                         self.progress_value.set(percent)
                self.root.after(0, _ui_update)

            count, root_dir = self.engine.process_batch(
                input_data, metric_val, _progress, 
                preprocessing_config=self.get_preprocessing_config()
            )
            
            def _finish():
                self.is_processing.set(False)
                self.progress_text.set(f"Finished. Processed {count} images.")
                
                if count > 0 and root_dir:
                    self.last_result_root = root_dir
                    self.can_visualize.set(True)
                else:
                    self.can_visualize.set(False)
                    
            self.root.after(0, _finish)
            
        threading.Thread(target=_bg_task, daemon=True).start()

    def request_visualization_transfer(self):
        if self.can_visualize.get() and self.last_result_root:
            if self.on_transfer_request:
                meta_path = os.path.join(self.last_result_root, 'metadata.txt')
                if os.path.exists(meta_path):
                    self.on_transfer_request(meta_path)
                else:
                    messagebox.showerror("Error", "Metadata file not found in output directory.")

    def open_result_folder(self):
        if hasattr(self, 'last_input_context') and os.path.exists(self.last_input_context):
            res_path = self.last_input_context
            if os.path.exists(res_path):
                os.startfile(res_path)
            else:
                 messagebox.showinfo("Info", "No results folder found in input location.")
        else:
            messagebox.showinfo("Info", "Nothing processed yet.")
