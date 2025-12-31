import tkinter as tk
from tkinter import ttk

class ModelConfigPanel(ttk.LabelFrame):
    def __init__(self, parent, viewmodel, on_processing_change_callback):
        super().__init__(parent, text="1. Model Configuration")
        self.vm = viewmodel
        self.on_processing_change_callback = on_processing_change_callback
        self.setup_ui()
        
    def setup_ui(self):
        # 1.1 StarDist Selection
        fr_sd = ttk.Frame(self)
        fr_sd.pack(fill=tk.X, padx=10, pady=(5, 0))
        ttk.Label(fr_sd, text="StarDist (Folder):", width=15).pack(side=tk.LEFT)
        entry_sd = ttk.Entry(fr_sd, textvariable=self.vm.sd_model_path, state='readonly')
        entry_sd.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(fr_sd, text="Browse...", command=self.vm.select_sd_model).pack(side=tk.LEFT)

        # 1.2 RDC Selection
        fr_rdc = ttk.Frame(self)
        fr_rdc.pack(fill=tk.X, padx=10, pady=(5, 5))
        ttk.Label(fr_rdc, text="RDC (.h5 File):", width=15).pack(side=tk.LEFT)
        entry_rdc = ttk.Entry(fr_rdc, textvariable=self.vm.rdc_model_path, state='readonly')
        entry_rdc.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(fr_rdc, text="Browse...", command=self.vm.select_rdc_model).pack(side=tk.LEFT)

        # 1.3 Status & Action
        fr_model_action = ttk.Frame(self)
        fr_model_action.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        lbl_status = ttk.Label(fr_model_action, text="Status:")
        lbl_status.pack(side=tk.LEFT)
        
        lbl_status_val = ttk.Label(fr_model_action, textvariable=self.vm.model_status, foreground="blue", style='Status.TLabel')
        lbl_status_val.pack(side=tk.LEFT, padx=10)
        
        self.btn_load = ttk.Button(fr_model_action, text="Load Models", command=self.vm.load_models)
        self.btn_load.pack(side=tk.RIGHT)

    def update_state(self, is_busy):
        state = tk.DISABLED if is_busy else tk.NORMAL
        self.btn_load.config(state=state)
        # Iterate over browse buttons in children frames if needed?
        # Browse buttons are packed directly.
        # Actually simplest way is if we keep references or rely on rebuild? No rebuild.
        # Let's traverse
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Button):
                         sub.config(state=state)
