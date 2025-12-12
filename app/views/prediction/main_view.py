import tkinter as tk
from tkinter import ttk
from app.viewmodels.prediction import PredictionViewModel

from .components.model_config import ModelConfigPanel
from .components.input_settings import InputSettingsPanel
from .components.execution_panel import ExecutionPanel

class PredictionView(tk.Frame):
    def __init__(self, parent, viewmodel: PredictionViewModel):
        super().__init__(parent)
        self.vm = viewmodel
        self.pack(fill=tk.BOTH, expand=True)
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        # 1. Model Configuration
        self.panel_model = ModelConfigPanel(self, self.vm, self._on_processing_change)
        self.panel_model.pack(fill=tk.X, pady=10, padx=10)

        # 2. Input Settings
        self.panel_input = InputSettingsPanel(self, self.vm)
        self.panel_input.pack(fill=tk.X, pady=10, padx=10)

        # 3. Execution
        self.panel_exec = ExecutionPanel(self, self.vm)
        self.panel_exec.pack(fill=tk.X, pady=10, padx=10)

    def setup_bindings(self):
        # Trace 'is_processing' for general lock
        self.vm.is_processing.trace_add("write", self._on_processing_change)
        
        # Trace 'can_visualize' for Viz button
        self.vm.can_visualize.trace_add("write", self._on_viz_state_change)
        
        # Initial state
        self._on_processing_change()
        self._on_viz_state_change()

    def _on_viz_state_change(self, *args):
        is_busy = self.vm.is_processing.get()
        can_viz = self.vm.can_visualize.get()
        self.panel_exec.update_viz_button(is_busy, can_viz)

    def _on_processing_change(self, *args):
        is_busy = self.vm.is_processing.get()
        
        self.panel_model.update_state(is_busy)
        self.panel_input.update_state(is_busy)
        self.panel_exec.update_state(is_busy)
