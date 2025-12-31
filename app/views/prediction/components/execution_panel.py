import tkinter as tk
from tkinter import ttk

class ExecutionPanel(ttk.LabelFrame):
    def __init__(self, parent, viewmodel):
        super().__init__(parent, text="4. Execution")
        self.vm = viewmodel
        self.setup_ui()
        
    def setup_ui(self):
        self.btn_start = ttk.Button(self, text="Start Prediction", command=self.vm.start_processing)
        self.btn_start.pack(fill=tk.X, padx=20, pady=15)
        
        # Progress
        self.pb = ttk.Progressbar(self, variable=self.vm.progress_value, maximum=100)
        self.pb.pack(fill=tk.X, padx=20, pady=(0, 5))
        
        lbl_progress = ttk.Label(self, textvariable=self.vm.progress_text, anchor="center")
        lbl_progress.pack(fill=tk.X, pady=(0, 10))

        # Buttons row (Visualize and Open Folder side by side)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.btn_viz = ttk.Button(btn_frame, text="Visualize Results", command=self.vm.request_visualization_transfer, state=tk.DISABLED)
        self.btn_viz.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.btn_open = ttk.Button(btn_frame, text="Open Results Folder", command=self.vm.open_result_folder, state=tk.DISABLED)
        self.btn_open.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def update_state(self, is_busy):
        state = tk.DISABLED if is_busy else tk.NORMAL
        self.btn_start.config(state=state)
        
    def update_viz_button(self, is_busy, can_visualize):
        if not is_busy and can_visualize:
            self.btn_viz.config(state=tk.NORMAL)
            self.btn_open.config(state=tk.NORMAL)
        else:
            self.btn_viz.config(state=tk.DISABLED)
            # Open folder also disabled until prediction done
            if not can_visualize:
                self.btn_open.config(state=tk.DISABLED)
