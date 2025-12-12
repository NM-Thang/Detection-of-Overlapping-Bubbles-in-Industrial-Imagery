import tkinter as tk
from tkinter import messagebox
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
