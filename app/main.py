import tkinter as tk
from tkinter import ttk
import os
import sys

# Ensure root dir is in sys.path
# This file is in .../app/main.py
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../app
root_dir = os.path.dirname(current_dir)          # .../
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.viewmodels.main import MainViewModel
from app.views.main import MainView
from tkinter import font as tkfont
from app.utils.config import AppConfig

def apply_settings(root, style):
    # Apply Geometry
    width = AppConfig.WINDOW_WIDTH
    height = AppConfig.WINDOW_HEIGHT
    
    root.geometry(f"{width}x{height}")
    
    # Apply Styles
    base_font_val = (AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BASE)
    header_font_val = AppConfig.get_header_font()
    status_font_val = AppConfig.get_status_font()
    
    # 1. Update Standard Named Fonts (Critical for Entry/Text widgets on Windows)
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family=AppConfig.FONT_FAMILY, size=AppConfig.FONT_SIZE_BASE)
    
    text_font = tkfont.nametofont("TkTextFont")
    text_font.configure(family=AppConfig.FONT_FAMILY, size=AppConfig.FONT_SIZE_BASE)
    
    # 2. Update TTK Styles
    style.configure('.', font=base_font_val)
    style.configure('TLabelframe.Label', font=(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_BASE, 'bold'))
    style.configure('TButton', font=base_font_val)
    style.configure('TEntry', font=base_font_val)
    style.configure('TRadiobutton', font=base_font_val)
    
    # Named Styles for specific overrides
    style.configure('Header.TLabel', font=header_font_val)
    style.configure('Status.TLabel', font=status_font_val)

def main():
    # Load Config First
    AppConfig.load()

    root = tk.Tk()
    root.title("Bubble Detection App - StarDist & RDC")
    style = ttk.Style()
    
    # Initial Apply
    try:
        apply_settings(root, style)
    except:
        pass
        
    # Center window (Initial only)
    # We do this logic manually once
    width = AppConfig.WINDOW_WIDTH
    height = AppConfig.WINDOW_HEIGHT
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    try:
        # Dependency Injection
        # Pass apply_settings callback to VM
        def on_settings_change():
            apply_settings(root, style)
            
        vm = MainViewModel(root)
        vm.on_settings_change = on_settings_change # Inject callback
        
        view = MainView(root, vm)
    except Exception as e:
        tk.messagebox.showerror("Startup Error", f"Failed to initialize app:\n{e}")
        return

    root.mainloop()

if __name__ == "__main__":
    main()
