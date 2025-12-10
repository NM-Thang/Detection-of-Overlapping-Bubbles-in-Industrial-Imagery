import tkinter as tk
from tkinter import ttk
from app.viewmodels.main import MainViewModel
from app.views.prediction import PredictionView
from app.views.visualization import VisualizationView
from app.utils.config import AppConfig

class MainView(tk.Frame):
    def __init__(self, parent, viewmodel: MainViewModel):
        super().__init__(parent)
        self.vm = viewmodel
        self.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.setup_ui()
        
        # Bind VM Actions
        self.vm.on_switch_tab = self.switch_to_tab

    def switch_to_tab(self, index):
        self.notebook.select(index)
        
    def setup_ui(self):
        # Header Row
        fr_header = ttk.Frame(self)
        fr_header.pack(fill=tk.X, pady=(0, 20))
        
        # Centered Title (using grid or pack tricks)
        # Simplest: Title in center, button on right
        lbl_title = ttk.Label(fr_header, text="Bubble Detection System", style='Header.TLabel')
        lbl_title.pack(side=tk.LEFT, expand=True) # Takes up space
        
        btn_settings = ttk.Button(fr_header, text="⚙ Settings", width=10, command=self.vm.open_settings)
        btn_settings.pack(side=tk.RIGHT)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Prediction
        self.tab_predict = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_predict, text="Prediction")
        
        # Instantiate PredictionView
        self.view_predict = PredictionView(self.tab_predict, self.vm.prediction_vm)
        self.view_predict.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: Visualization
        self.tab_visualize = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_visualize, text="Visualization")
        
        # Instantiate VisualizationView
        self.view_visualize = VisualizationView(self.tab_visualize, self.vm.visualization_vm)
        self.view_visualize.pack(fill=tk.BOTH, expand=True)
