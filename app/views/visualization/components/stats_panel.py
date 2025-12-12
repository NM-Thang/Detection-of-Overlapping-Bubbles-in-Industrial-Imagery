import tkinter as tk
from tkinter import ttk

class StatsPanel(ttk.LabelFrame):
    def __init__(self, parent, viewmodel):
        super().__init__(parent, text="Statistics")
        self.vm = viewmodel
        self.setup_ui()
        
    def setup_ui(self):
        # Configure Grid Columns to expand
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        
        # Headers
        ttk.Label(self, text="Metric", font=('Helvetica', 9, 'italic')).grid(row=0, column=0, sticky='w', padx=2)
        ttk.Label(self, text="SD & RDC", font=('Helvetica', 9, 'bold')).grid(row=0, column=1, padx=5)
        ttk.Label(self, text="StarDist", font=('Helvetica', 9, 'bold'), foreground='blue').grid(row=0, column=2, padx=5)

        self.current_row = 1
        
        self.add_2col_row("Count", self.vm.stat_bubble_count, self.vm.stat_sd_count)
        self.add_2col_row("Area (px)", self.vm.stat_bub_area_px, self.vm.stat_sd_area_px)
        self.add_2col_row("Area (mm²)", self.vm.stat_bub_area_mm, self.vm.stat_sd_area_mm)
        self.add_2col_row("Ratio (%)", self.vm.stat_ratio_mm, self.vm.stat_sd_ratio)
        
        # Separator
        ttk.Separator(self, orient='horizontal').grid(row=self.current_row, column=0, columnspan=3, sticky='ew', pady=5)
        self.current_row += 1
        
        self.add_single_row("Img Size", self.vm.stat_img_size)
        self.add_single_row("Mean Prob", self.vm.stat_sd_prob)

    def add_2col_row(self, label, var_final, var_sd=None):
        ttk.Label(self, text=label+":", font=('Helvetica', 9)).grid(row=self.current_row, column=0, sticky='w', pady=1)
        # Center values by removing sticky='e'
        ttk.Label(self, textvariable=var_final, font=('Helvetica', 9)).grid(row=self.current_row, column=1, padx=5)
        if var_sd:
             ttk.Label(self, textvariable=var_sd, font=('Helvetica', 9), foreground='blue').grid(row=self.current_row, column=2, padx=5)
        self.current_row += 1

    def add_single_row(self, label, var):
         ttk.Label(self, text=label+":", font=('Helvetica', 9)).grid(row=self.current_row, column=0, sticky='w')
         ttk.Label(self, textvariable=var, font=('Helvetica', 9, 'bold')).grid(row=self.current_row, column=1, columnspan=2, sticky='w')
         self.current_row += 1
