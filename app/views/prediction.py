import tkinter as tk
from tkinter import ttk
from app.viewmodels.prediction import PredictionViewModel

class PredictionView(tk.Frame):
    def __init__(self, parent, viewmodel: PredictionViewModel):
        super().__init__(parent)
        self.vm = viewmodel
        self.pack(fill=tk.BOTH, expand=True)
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        # Section 1: Models
        lf_model = ttk.LabelFrame(self, text="1. Model Configuration")
        lf_model.pack(fill=tk.X, pady=10, padx=10)
        
        # 1.1 StarDist Selection
        fr_sd = ttk.Frame(lf_model)
        fr_sd.pack(fill=tk.X, padx=10, pady=(5, 0))
        ttk.Label(fr_sd, text="StarDist (Folder):", width=15).pack(side=tk.LEFT)
        entry_sd = ttk.Entry(fr_sd, textvariable=self.vm.sd_model_path, state='readonly')
        entry_sd.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(fr_sd, text="Browse...", command=self.vm.select_sd_model).pack(side=tk.LEFT)

        # 1.2 RDC Selection
        fr_rdc = ttk.Frame(lf_model)
        fr_rdc.pack(fill=tk.X, padx=10, pady=(5, 5))
        ttk.Label(fr_rdc, text="RDC (.h5 File):", width=15).pack(side=tk.LEFT)
        entry_rdc = ttk.Entry(fr_rdc, textvariable=self.vm.rdc_model_path, state='readonly')
        entry_rdc.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(fr_rdc, text="Browse...", command=self.vm.select_rdc_model).pack(side=tk.LEFT)

        # 1.3 Status & Action
        fr_model_action = ttk.Frame(lf_model)
        fr_model_action.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        lbl_status = ttk.Label(fr_model_action, text="Status:")
        lbl_status.pack(side=tk.LEFT)
        
        lbl_status_val = ttk.Label(fr_model_action, textvariable=self.vm.model_status, foreground="blue", style='Status.TLabel')
        lbl_status_val.pack(side=tk.LEFT, padx=10)
        
        self.btn_load = ttk.Button(fr_model_action, text="Load Models", command=self.vm.load_models)
        self.btn_load.pack(side=tk.RIGHT)

        # Section 2: Input
        lf_input = ttk.LabelFrame(self, text="2. Input Settings")
        lf_input.pack(fill=tk.X, pady=10, padx=10)
        
        # Folder / Files Selection
        fr_folder = ttk.Frame(lf_input)
        fr_folder.pack(fill=tk.X, padx=10, pady=5)
        
        # Mode Selection
        fr_mode = ttk.Frame(fr_folder)
        fr_mode.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        ttk.Label(fr_mode, text="Mode:").pack(side=tk.LEFT)
        ttk.Radiobutton(fr_mode, text="Folder", variable=self.vm.input_mode, value="Folder").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(fr_mode, text="Files", variable=self.vm.input_mode, value="Files").pack(side=tk.LEFT)

        # Path Entry
        fr_path_entry = ttk.Frame(fr_folder)
        fr_path_entry.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(fr_path_entry, text="Input Path:", width=15).pack(side=tk.LEFT)
        entry_folder = ttk.Entry(fr_path_entry, textvariable=self.vm.input_path_display, state='readonly')
        entry_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.btn_browse = ttk.Button(fr_path_entry, text="Browse...", command=self.vm.select_input)
        self.btn_browse.pack(side=tk.LEFT)
        
        # Metric
        fr_metric = ttk.Frame(lf_input)
        fr_metric.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(fr_metric, text="Metric (mm/px):", width=15).pack(side=tk.LEFT)
        entry_metric = ttk.Entry(fr_metric, textvariable=self.vm.metric)
        entry_metric.pack(side=tk.LEFT, padx=5)
        ttk.Label(fr_metric, text="(Default: 5.2E-2)", foreground="gray").pack(side=tk.LEFT, padx=5)

        # Section 3: Execution
        lf_exec = ttk.LabelFrame(self, text="3. Execution")
        lf_exec.pack(fill=tk.X, pady=10, padx=10)
        
        self.btn_start = ttk.Button(lf_exec, text="Start Prediction", command=self.vm.start_processing)
        self.btn_start.pack(fill=tk.X, padx=20, pady=15)
        
        # Progress
        self.pb = ttk.Progressbar(lf_exec, variable=self.vm.progress_value, maximum=100)
        self.pb.pack(fill=tk.X, padx=20, pady=(0, 5))
        
        lbl_progress = ttk.Label(lf_exec, textvariable=self.vm.progress_text, anchor="center")
        lbl_progress.pack(fill=tk.X, pady=(0, 10))

        self.btn_open = ttk.Button(lf_exec, text="Open Results Folder", command=self.vm.open_result_folder)
        self.btn_open.pack(pady=(0, 5))
        
        self.btn_viz = ttk.Button(lf_exec, text="Visualize Results", command=self.vm.request_visualization_transfer, state=tk.DISABLED)
        self.btn_viz.pack(pady=(0, 10))

    def setup_bindings(self):
        # Trace 'is_processing' for general lock
        self.vm.is_processing.trace_add("write", self._on_processing_change)
        
        # Trace 'can_visualize' for Viz button
        self.vm.can_visualize.trace_add("write", self._on_viz_state_change)
        
        # Initial state
        self._on_processing_change()
        self._on_viz_state_change()

    def _on_viz_state_change(self, *args):
        # Only enable if not processing AND can_visualize is true
        is_busy = self.vm.is_processing.get()
        can_viz = self.vm.can_visualize.get()
        
        if not is_busy and can_viz:
            self.btn_viz.config(state=tk.NORMAL)
        else:
            self.btn_viz.config(state=tk.DISABLED)

    def _on_processing_change(self, *args):
        is_busy = self.vm.is_processing.get()
        state = tk.DISABLED if is_busy else tk.NORMAL
        
        self.btn_load.config(state=state)
        self.btn_start.config(state=state)
        self.btn_browse.config(state=state)
