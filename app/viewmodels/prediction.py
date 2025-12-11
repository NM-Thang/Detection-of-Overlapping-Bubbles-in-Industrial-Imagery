import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
from app.services.inference_engine import InferenceEngine
from app.utils.validators import validate_directory_path, validate_metric

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

    def select_sd_model(self):
        # StarDist: Select Folder
        path = filedialog.askdirectory(title="Select StarDist Model Folder (e.g. data_mix_64_400)")
        if path:
            self.sd_model_path.set(path)
            self._reset_model_status()

    def select_rdc_model(self):
        # RDC: Select .h5 File OR Folder
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

    def select_input(self):
        mode = self.input_mode.get()
        if mode == "Folder":
            path = filedialog.askdirectory()
            if path:
                self.input_path_display.set(path)
                self.selected_files = [] # Clear files
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
            
            # Update UI on Main Thread
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
            # For open_results logic, we can track this folder
            self.last_input_context = folder
        else:
            if not self.selected_files:
                messagebox.showwarning("Invalid Input", "No files selected.")
                return
            input_data = self.selected_files
            # For open_results logic, track parent of first file?
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

        # Start Batch Processing
        self.is_processing.set(True)
        self.progress_value.set(0)
        self.progress_text.set("Initializing...")
        
        def _bg_task():
            # Progress Callback
            def _progress(current, total, msg):
                def _ui_update():
                    self.progress_text.set(f"{msg}")
                    if total > 0:
                         percent = (current / total) * 100
                         self.progress_value.set(percent)
                self.root.after(0, _ui_update)

            # Run Engine
            count, root_dir = self.engine.process_batch(input_data, metric_val, _progress)
            
            def _finish():
                self.is_processing.set(False)
                self.progress_text.set(f"Finished. Processed {count} images.")
                
                # Store visualization context
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
                # We essentially pass the metadata path.
                # InferenceEngine guarantees metadata.txt is created in root_dir if count > 0
                meta_path = os.path.join(self.last_result_root, 'metadata.txt')
                if os.path.exists(meta_path):
                    self.on_transfer_request(meta_path)
                else:
                    messagebox.showerror("Error", "Metadata file not found in output directory.")

    def open_result_folder(self):
        # Open 'results' folder in the last input context
        if hasattr(self, 'last_input_context') and os.path.exists(self.last_input_context):
            res_path = os.path.join(self.last_input_context, 'results')
            if os.path.exists(res_path):
                os.startfile(res_path)
            else:
                 messagebox.showinfo("Info", "No results folder found in input location.")
        else:
            messagebox.showinfo("Info", "Nothing processed yet.")
