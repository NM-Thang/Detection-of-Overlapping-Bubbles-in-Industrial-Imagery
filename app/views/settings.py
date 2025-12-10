import tkinter as tk
from tkinter import ttk, messagebox
from app.utils.config import AppConfig

class SettingsViewModel:
    def __init__(self, root, on_apply_callback):
        self.root = root
        self.on_apply = on_apply_callback
        
        # State
        self.width = tk.IntVar(value=AppConfig.WINDOW_WIDTH)
        self.height = tk.IntVar(value=AppConfig.WINDOW_HEIGHT)
        self.font_base = tk.IntVar(value=AppConfig.FONT_SIZE_BASE)
        self.font_header = tk.IntVar(value=AppConfig.FONT_SIZE_HEADER)

    def save_and_apply(self):
        try:
            # Update Config
            AppConfig.WINDOW_WIDTH = self.width.get()
            AppConfig.WINDOW_HEIGHT = self.height.get()
            AppConfig.FONT_SIZE_BASE = self.font_base.get()
            AppConfig.FONT_SIZE_HEADER = self.font_header.get()
            
            # Save
            AppConfig.save()
            
            # Apply Live
            if self.on_apply:
                self.on_apply()
                
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            return False

class SettingsView(tk.Toplevel):
    def __init__(self, parent, on_apply_callback):
        super().__init__(parent)
        self.title("Application Settings")
        self.geometry("400x350")
        
        # Center popup
        x = parent.winfo_x() + (parent.winfo_width()//2) - 200
        y = parent.winfo_y() + (parent.winfo_height()//2) - 175
        self.geometry(f"+{x}+{y}")
        
        self.vm = SettingsViewModel(self, on_apply_callback)
        self.setup_ui()
        
    def setup_ui(self):
        pad_opts = {'padx': 10, 'pady': 10}
        
        # Window Size
        lf_geo = ttk.LabelFrame(self, text="Window Size")
        lf_geo.pack(fill=tk.X, **pad_opts)
        
        fr_w = ttk.Frame(lf_geo)
        fr_w.pack(fill=tk.X, pady=5)
        ttk.Label(fr_w, text="Width:", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Entry(fr_w, textvariable=self.vm.width).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        fr_h = ttk.Frame(lf_geo)
        fr_h.pack(fill=tk.X, pady=5)
        ttk.Label(fr_h, text="Height:", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Entry(fr_h, textvariable=self.vm.height).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Fonts
        lf_font = ttk.LabelFrame(self, text="Font Sizes")
        lf_font.pack(fill=tk.X, **pad_opts)
        
        fr_fbase = ttk.Frame(lf_font)
        fr_fbase.pack(fill=tk.X, pady=5)
        ttk.Label(fr_fbase, text="Base Font:", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Entry(fr_fbase, textvariable=self.vm.font_base).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        fr_fhead = ttk.Frame(lf_font)
        fr_fhead.pack(fill=tk.X, pady=5)
        ttk.Label(fr_fhead, text="Header Font:", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Entry(fr_fhead, textvariable=self.vm.font_header).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Actions
        fr_act = ttk.Frame(self)
        fr_act.pack(fill=tk.X, pady=20)
        
        ttk.Button(fr_act, text="Apply & Save", command=self.apply).pack(side=tk.RIGHT, padx=10)
        ttk.Button(fr_act, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def apply(self):
        if self.vm.save_and_apply():
            self.destroy()
