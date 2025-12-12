import tkinter as tk
from tkinter import ttk

class ControlPanel(ttk.Frame):
    def __init__(self, parent, viewmodel, callbacks):
        super().__init__(parent, relief='groove', padding=5)
        self.vm = viewmodel
        self.callbacks = callbacks # dict: prev, next, show, clear
        self.lbl_coords = None # Will be created in setup_ui
        self.setup_ui()
        
    def setup_ui(self):
        ttk.Label(self, text="Control Center", font=('Helvetica', 10, 'bold')).pack(side=tk.TOP, pady=5)
        
        # Bubble Navigation Buttons
        fr_nav = ttk.Frame(self)
        fr_nav.pack(fill=tk.X, pady=5)
        
        self.btn_prev = ttk.Button(fr_nav, text="Prev", command=self.callbacks.get('prev'), state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.btn_next = ttk.Button(fr_nav, text="Next", command=self.callbacks.get('next'), state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Batch Buttons
        fr_batch = ttk.Frame(self)
        fr_batch.pack(fill=tk.X, pady=5)
        
        self.btn_all = ttk.Button(fr_batch, text="Show", command=self.callbacks.get('show'), state=tk.DISABLED)
        self.btn_all.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.btn_clear = ttk.Button(fr_batch, text="Clear", command=self.callbacks.get('clear'), state=tk.DISABLED)
        self.btn_clear.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Coordinate Label (Bottom-most)
        self.lbl_coords = tk.Label(self, text="Ready", relief="sunken", anchor="center", height=2)
        self.lbl_coords.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
        
        # Toolbar Container PLACEHOLDER (managed by parent or injected here?)
        # In original, toolbar is packed above coords.
        # We will expose a frame for toolbar
        self.fr_toolbar = ttk.Frame(self)
        self.fr_toolbar.pack(side=tk.BOTTOM, fill=tk.X, expand=False, pady=(2, 0))

        # Target Mode Switch
        fr_target = ttk.LabelFrame(self, text="Control Target")
        fr_target.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        ttk.Radiobutton(fr_target, text="SD & RDC", variable=self.vm.control_mode, value="RDC", command=lambda: self.vm.set_control_mode("RDC")).pack(side=tk.LEFT, expand=True)
        ttk.Radiobutton(fr_target, text="StarDist", variable=self.vm.control_mode, value="SD", command=lambda: self.vm.set_control_mode("SD")).pack(side=tk.LEFT, expand=True)

    def update_states(self, has_stepper):
         state = tk.NORMAL if has_stepper else tk.DISABLED
         self.btn_next.config(state=state)
         self.btn_prev.config(state=state)
         self.btn_all.config(state=state)
         self.btn_clear.config(state=state)
