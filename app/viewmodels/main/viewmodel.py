from app.viewmodels.prediction import PredictionViewModel
from app.viewmodels.visualization import VisualizationViewModel
from app.views.settings import SettingsView

class MainViewModel:
    def __init__(self, root):
        self.root = root
        self.on_settings_change = None # Injected by main.py
        
        # Instantiate Sub-ViewModels
        self.prediction_vm = PredictionViewModel(root)
        self.visualization_vm = VisualizationViewModel(root)
        
        # Bridge Logic
        self.prediction_vm.on_transfer_request = self.transfer_to_visualization
        self.on_switch_tab = None
        
    def open_settings(self):
        SettingsView(self.root, on_apply_callback=self.on_settings_change)

    def transfer_to_visualization(self, metadata_path):
        # 1. Load Data in Viz VM
        self.visualization_vm.load_metadata_from_path(metadata_path)
        
        # 2. Switch Tab
        if self.on_switch_tab:
            self.on_switch_tab(1) # Index 1 = Visualization Tab
