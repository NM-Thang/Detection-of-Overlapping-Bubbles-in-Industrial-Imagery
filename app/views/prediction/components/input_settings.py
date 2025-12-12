import tkinter as tk
from tkinter import ttk

class InputSettingsPanel(ttk.LabelFrame):
    def __init__(self, parent, viewmodel):
        super().__init__(parent, text="2. Input Settings")
        self.vm = viewmodel
        self.setup_ui()
        
    def setup_ui(self):
        # Folder / Files Selection
        fr_folder = ttk.Frame(self)
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
        fr_metric = ttk.Frame(self)
        fr_metric.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(fr_metric, text="Metric (mm/px):", width=15).pack(side=tk.LEFT)
        entry_metric = ttk.Entry(fr_metric, textvariable=self.vm.metric)
        entry_metric.pack(side=tk.LEFT, padx=5)
        ttk.Label(fr_metric, text="(Default: 5.2E-2)", foreground="gray").pack(side=tk.LEFT, padx=5)

    def update_state(self, is_busy):
        state = tk.DISABLED if is_busy else tk.NORMAL
        self.btn_browse.config(state=state)
