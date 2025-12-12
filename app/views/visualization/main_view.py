import tkinter as tk
from tkinter import ttk

from .components.image_list import ImageList
from .components.stats_panel import StatsPanel
from .components.bubble_list import BubbleList
from .components.control_panel import ControlPanel
from .components.plots import PlotsPanel

class VisualizationView(ttk.Frame):
    def __init__(self, parent, viewmodel):
        super().__init__(parent)
        self.vm = viewmodel
        
        # Flash animation state (managed by main controller or plots?)
        # Originally in View. Let's keep it here for now or delegating to Stepper.
        # Stepper handles flash via 'create_highlight_artists'.
        self.flash_job = None
        self.flash_artists = []
        
        # Bind VM events
        self.vm.on_image_list_update = self.update_image_list
        self.vm.on_bubble_list_update = self.update_bubble_list
        self.vm.on_view_update = self.update_visualization
        self.vm.on_control_mode_update = self.update_control_binding
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top Bar
        fr_top = ttk.Frame(self)
        fr_top.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(fr_top, text="Up Load", command=self.vm.select_metadata).pack(side=tk.LEFT)
        ttk.Label(fr_top, textvariable=self.vm.metadata_path).pack(side=tk.LEFT, padx=10)
        
        # Main Paned Window
        self.paned_main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_main.pack(fill=tk.BOTH, expand=True)
        
        # --- LEFT PANE ---
        fr_left_container = ttk.Frame(self.paned_main, width=240)
        fr_left_container.pack_propagate(False)
        self.paned_main.add(fr_left_container, weight=0)
        
        self.paned_left = ttk.PanedWindow(fr_left_container, orient=tk.VERTICAL)
        self.paned_left.pack(fill=tk.BOTH, expand=True)
        
        # 1. Image List
        self.comp_img_list = ImageList(self.paned_left, self.vm, self.on_image_select)
        self.paned_left.add(self.comp_img_list, weight=3)
        
        # 2. Control Panel
        fr_controls_wrapper = ttk.Frame(self.paned_left)
        self.paned_left.add(fr_controls_wrapper, weight=1)
        
        # Spacer
        sb_width = 16 # Approx
        fr_spacer = ttk.Frame(fr_controls_wrapper, width=sb_width)
        fr_spacer.pack(side=tk.RIGHT, fill=tk.Y)
        
        callbacks = {
            'prev': self.on_prev_bubble,
            'next': self.on_next_bubble,
            'show': self.on_show_all,
            'clear': self.on_clear_all
        }
        
        # We need coords label valid before passing to ControlPanel if structure requires it
        # Actually ControlPanel creates it or we pass it?
        # In this refactor, ControlPanel creates structure but needs us to maybe inject label?
        # Let's pass a created label so we can reference it easily?
        # Or let ControlPanel create it and we access it via comp_controls.lbl_coords?
        # Let's pass a placeholder variable or let ControlPanel init it.
        # Plan: ControlPanel inits it.
        
        self.comp_controls = ControlPanel(fr_controls_wrapper, self.vm, callbacks)
        self.comp_controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # --- RIGHT PANE ---
        fr_right = ttk.Frame(self.paned_main)
        self.paned_main.add(fr_right, weight=8)
        
        self.paned_right = ttk.PanedWindow(fr_right, orient=tk.VERTICAL)
        self.paned_right.pack(fill=tk.BOTH, expand=True)
        
        # Top Right (Stats + Bubbles)
        fr_top_right = ttk.Frame(self.paned_right)
        self.paned_right.add(fr_top_right, weight=0)
        self.paned_top_right = ttk.PanedWindow(fr_top_right, orient=tk.HORIZONTAL)
        self.paned_top_right.pack(fill=tk.BOTH, expand=True)
        
        # Stats
        self.comp_stats = StatsPanel(self.paned_top_right, self.vm)
        self.paned_top_right.add(self.comp_stats, weight=1)
        
        # Bubble List
        self.comp_bubble_list = BubbleList(self.paned_top_right, self.vm, self.on_bubble_select)
        self.paned_top_right.add(self.comp_bubble_list, weight=3)
        
        # Viz/Plots
        fr_viz_container = ttk.Frame(self.paned_right)
        self.paned_right.add(fr_viz_container, weight=3)
        
        fr_viz_opts = ttk.Frame(fr_viz_container)
        fr_viz_opts.pack(fill=tk.X)
        ttk.Checkbutton(fr_viz_opts, text="SD & RDC", variable=self.vm.show_result, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(fr_viz_opts, text="StarDist", variable=self.vm.show_mask, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(fr_viz_opts, text="Original", variable=self.vm.show_original, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        
        self.comp_plots = PlotsPanel(fr_viz_container, self.vm, self.comp_controls)
        self.comp_plots.pack(fill=tk.BOTH, expand=True)
        self.comp_plots.set_bubble_list_ref(self.comp_bubble_list)

    # --- Event Handlers ---
    def update_image_list(self):
        self.comp_img_list.update_list()
        
    def update_bubble_list(self):
        self.comp_bubble_list.update_list()
        
    def update_visualization(self):
        self.comp_plots.update_visualization()
        self.update_control_binding()
        
    def update_control_binding(self):
        stepper = self.comp_plots.set_active_stepper(self.vm.control_mode.get())
        has_stepper = (stepper is not None)
        self.comp_controls.update_states(has_stepper)

    def on_image_select(self, idx):
        self.vm.select_image(idx)
        
    def on_bubble_select(self, idx):
        # Flash animation logic
        if self.flash_job:
            self.after_cancel(self.flash_job)
            self.flash_job = None
        
        for art in self.flash_artists:
            art.remove()
        self.flash_artists = []
        if self.comp_plots.canvas:
             self.comp_plots.canvas.draw_idle()

        stepper = self.comp_plots.stepper
        if not stepper:
            return
            
        self.flash_artists = stepper.create_highlight_artists(idx)
        if self.flash_artists:
            if self.comp_plots.canvas:
                self.comp_plots.canvas.draw_idle()
            self._flash_step(6)
            
    def _flash_step(self, count):
        if count <= 0:
            for art in self.flash_artists:
                art.remove()
            self.flash_artists = []
            if self.comp_plots.canvas:
                self.comp_plots.canvas.draw_idle()
            return

        is_visible = (count % 2 == 0)
        for art in self.flash_artists:
            art.set_visible(is_visible)
        
        if self.comp_plots.canvas:
            self.comp_plots.canvas.draw_idle()
            
        self.flash_job = self.after(500, lambda: self._flash_step(count - 1))

    # --- Stepper Proxies ---
    def on_next_bubble(self):
        if self.comp_plots.stepper:
            self.comp_plots.stepper.next()
            
    def on_prev_bubble(self):
        if self.comp_plots.stepper:
            self.comp_plots.stepper.prev()
            
    def on_show_all(self):
        if self.comp_plots.stepper:
            self.comp_plots.stepper.show_all()
            
    def on_clear_all(self):
        if self.comp_plots.stepper:
            self.comp_plots.stepper.clear_all()
