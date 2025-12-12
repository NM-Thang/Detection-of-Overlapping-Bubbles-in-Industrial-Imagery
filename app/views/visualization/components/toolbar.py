from tkinter import ttk
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, window, coord_label=None):
        super().__init__(canvas, window)
        self.coord_label = coord_label
        # Manually remove Subplots button if it persists
        if hasattr(self, '_buttons'):
            if 'Subplots' in self._buttons:
                self._buttons['Subplots'].pack_forget()
        
    def set_message(self, s):
        if self.coord_label:
             self.coord_label.config(text=s)
