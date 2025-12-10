import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from app.utils.starbub import BubbleStepper

class VisualizationView(ttk.Frame):
    def __init__(self, parent, vm):
        super().__init__(parent)
        self.vm = vm
        
        # Bind VM Callbacks
        self.vm.on_image_list_update = self.update_image_list
        self.vm.on_bubble_list_update = self.update_bubble_list
        self.vm.on_view_update = self.update_visualization
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top Bar
        fr_top = ttk.Frame(self)
        fr_top.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(fr_top, text="Up Load", command=self.vm.select_metadata).pack(side=tk.LEFT)
        ttk.Label(fr_top, textvariable=self.vm.metadata_path).pack(side=tk.LEFT, padx=10)
        
        # Main Paned Window (Horizontal Split)
        self.paned_main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_main.pack(fill=tk.BOTH, expand=True)
        
        # --- LEFT PANE: Image List + Controls ---
        fr_left_container = ttk.Frame(self.paned_main, width=320)
        self.paned_main.add(fr_left_container, weight=0)
        
        # Split Left Pane Vertical: Top=List, Bottom=Controls
        self.paned_left = ttk.PanedWindow(fr_left_container, orient=tk.VERTICAL)
        self.paned_left.pack(fill=tk.BOTH, expand=True)

        # 1. Image List (Top)
        fr_list = ttk.Frame(self.paned_left)
        self.paned_left.add(fr_list, weight=3) # List takes more space

        cols = ("STT", "Image Name")
        self.tree_imgs = ttk.Treeview(fr_list, columns=cols, show='headings')
        self.tree_imgs.heading("STT", text="STT")
        self.tree_imgs.heading("Image Name", text="Image Name")
        self.tree_imgs.column("STT", width=35, stretch=False, anchor='center')
        self.tree_imgs.column("Image Name", width=65, stretch=True)
        # Scrollbar
        sb_imgs = ttk.Scrollbar(fr_list, orient="vertical", command=self.tree_imgs.yview)
        sb_imgs.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_imgs.configure(yscrollcommand=sb_imgs.set)
        self.tree_imgs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_imgs.bind("<<TreeviewSelect>>", self.on_image_select)
        
        # 2. Control Panel (Bottom)
        fr_controls_wrapper = ttk.Frame(self.paned_left)
        self.paned_left.add(fr_controls_wrapper, weight=1)
        
        # Spacer to mimic scrollbar width
        sb_width = sb_imgs.winfo_reqwidth() 
        fr_spacer = ttk.Frame(fr_controls_wrapper, width=sb_width)
        fr_spacer.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Actual Control Frame (with border)
        fr_controls = ttk.Frame(fr_controls_wrapper, relief='groove', padding=5)
        fr_controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # --- Statistics Panel ---
        fr_stats = ttk.LabelFrame(fr_controls, text="Statistics")
        fr_stats.pack(side=tk.TOP, fill=tk.X, pady=5, ipadx=5, ipady=5)
        
        def add_stat_row(parent, label, var):
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=1)
            ttk.Label(row, text=label + ":", font=('Helvetica', 11)).pack(side=tk.LEFT)
            ttk.Label(row, textvariable=var, font=('Helvetica', 11, 'bold')).pack(side=tk.RIGHT)
            
        add_stat_row(fr_stats, "Img Size (px)", self.vm.stat_img_size)
        add_stat_row(fr_stats, "Total Bubbles", self.vm.stat_bubble_count)
        add_stat_row(fr_stats, "Bub Area (mm²)", self.vm.stat_bub_area_mm)
        add_stat_row(fr_stats, "Bub Area (px)", self.vm.stat_bub_area_px)
        add_stat_row(fr_stats, "Img Area (mm²)", self.vm.stat_img_area_mm)
        add_stat_row(fr_stats, "Ratio (%)", self.vm.stat_ratio_mm)
        
        ttk.Label(fr_controls, text="Control Center", font=('Helvetica', 10, 'bold')).pack(side=tk.TOP, pady=5)
        
        # Bubble Navigation Buttons
        fr_nav = ttk.Frame(fr_controls)
        fr_nav.pack(fill=tk.X, pady=5)
        
        self.btn_prev = ttk.Button(fr_nav, text="Prev", command=self.on_prev_bubble, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.btn_next = ttk.Button(fr_nav, text="Next", command=self.on_next_bubble, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Batch Buttons
        fr_batch = ttk.Frame(fr_controls)
        fr_batch.pack(fill=tk.X, pady=5)
        
        self.btn_all = ttk.Button(fr_batch, text="Show", command=self.on_show_all, state=tk.DISABLED)
        self.btn_all.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.btn_clear = ttk.Button(fr_batch, text="Clear", command=self.on_clear_all, state=tk.DISABLED)
        self.btn_clear.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Coordinate Label (Bottom-most)
        self.lbl_coords = tk.Label(fr_controls, text="Ready", relief="sunken", anchor="center", height=2)
        self.lbl_coords.pack(side=tk.BOTTOM, fill=tk.X, pady=2)
        
        # Toolbar Container (Above Coords)
        self.fr_toolbar = ttk.Frame(fr_controls)
        self.fr_toolbar.pack(side=tk.BOTTOM, fill=tk.X, expand=False, pady=(2, 0))


        # --- RIGHT PANE: Detail + Visualization ---
        fr_right = ttk.Frame(self.paned_main)
        self.paned_main.add(fr_right, weight=8) # Give more space
        
        self.paned_right = ttk.PanedWindow(fr_right, orient=tk.VERTICAL)
        self.paned_right.pack(fill=tk.BOTH, expand=True)
        
        # Top Right: Bubble List
        fr_bubbles = ttk.Frame(self.paned_right)
        self.paned_right.add(fr_bubbles, weight=0) # weight=0 to respect height=5
        
        b_cols = ("STT", "Center X", "Center Y", "Pixels", "Area (mm²)")
        self.tree_bubbles = ttk.Treeview(fr_bubbles, columns=b_cols, show='headings', height=5)
        for col in b_cols:
            self.tree_bubbles.heading(col, text=col)
        
        # Configure columns
        self.tree_bubbles.column("STT", width=40, minwidth=30, anchor='center')
        self.tree_bubbles.column("Center X", width=60, minwidth=50, anchor='center')
        self.tree_bubbles.column("Center Y", width=60, minwidth=50, anchor='center')
        self.tree_bubbles.column("Pixels", width=60, minwidth=50, anchor='center')
        self.tree_bubbles.column("Area (mm²)", width=80, minwidth=60, anchor='center')
        
        self.tree_bubbles.pack(fill=tk.BOTH, expand=True)
        self.tree_bubbles.bind("<<TreeviewSelect>>", self.on_bubble_select)

        # Bottom Right: Visualization Control + Canvas
        fr_viz_container = ttk.Frame(self.paned_right)
        self.paned_right.add(fr_viz_container, weight=3)
        
        # Viz Options
        fr_viz_opts = ttk.Frame(fr_viz_container)
        fr_viz_opts.pack(fill=tk.X)
        
        ttk.Checkbutton(fr_viz_opts, text="Results (StarDist + RDC)", variable=self.vm.show_result, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(fr_viz_opts, text="Mask (StarDist)", variable=self.vm.show_mask, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(fr_viz_opts, text="Original Image", variable=self.vm.show_original, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        
        # Canvas Area
        self.fr_canvas = ttk.Frame(fr_viz_container)
        self.fr_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.stepper = None # Keep reference to stepper
        
        # Flash animation state
        self.flash_job = None
        self.flash_artists = []

    def on_image_select(self, event):
        selected = self.tree_imgs.selection()
        if selected:
            idx = int(self.tree_imgs.item(selected[0])['values'][0]) - 1
            self.vm.select_image(idx)

    def on_bubble_select(self, event):
        # Cancel current flash if any
        if self.flash_job:
            self.after_cancel(self.flash_job)
            self.flash_job = None
        
        # Cleanup matches
        for art in self.flash_artists:
            art.remove()
        self.flash_artists = []
        if self.canvas:
             self.canvas.draw_idle()

        if not self.stepper:
            return

        selected = self.tree_bubbles.selection()
        if not selected:
            return
            
        # Get bubble index
        # We assume bubble list order matches stepper items order
        # Tree items are children of root
        idx = self.tree_bubbles.index(selected[0])
        
        # Create highlight artists
        self.flash_artists = self.stepper.create_highlight_artists(idx)
        if self.flash_artists:
            self.canvas.draw_idle()
            # Start flash loop (5 times = 10 toggles)
            self._flash_step(6)
            
    def _flash_step(self, count):
        if count <= 0:
            # Cleanup
            for art in self.flash_artists:
                art.remove()
            self.flash_artists = []
            if self.canvas:
                self.canvas.draw_idle()
            return

        # Toggle visibility
        is_visible = (count % 2 == 0)
        for art in self.flash_artists:
            art.set_visible(is_visible)
        
        if self.canvas:
            self.canvas.draw_idle()
            
        # Schedule next step (slow flash: 500ms)
        self.flash_job = self.after(500, lambda: self._flash_step(count - 1))

    def on_next_bubble(self):
        if self.stepper:
            self.stepper.next()

    def on_prev_bubble(self):
        if self.stepper:
            self.stepper.prev()
            
    def on_show_all(self):
        if self.stepper:
            self.stepper.show_all()
            
    def on_clear_all(self):
        if self.stepper:
            self.stepper.clear_all()

    def update_image_list(self):
        for item in self.tree_imgs.get_children():
            self.tree_imgs.delete(item)
        
        for i, name in enumerate(self.vm.image_list):
            self.tree_imgs.insert("", "end", values=(i+1, name))
            
        # Select first item if exists
        children = self.tree_imgs.get_children()
        if children:
            self.tree_imgs.selection_set(children[0])
            self.tree_imgs.focus(children[0])

    def update_bubble_list(self):
        for item in self.tree_bubbles.get_children():
            self.tree_bubbles.delete(item)
            
        for b in self.vm.bubble_list:
            # {stt, x, y, area_px, area_mm}
            cx = b.get('cx', '')
            cy = b.get('cy', '')
            area_mm = b.get('area_mm', '')
            area_px = b.get('area_px', 'N/A')
            
            try:
                cx = f"{float(cx):.0f}"
                cy = f"{float(cy):.0f}"
            except:
                pass
                
            try:
                area_mm = f"{float(area_mm):.4f}"
            except:
                pass
            
            # Format area_px to int if possible
            if area_px != 'N/A':
                try:
                     area_px = f"{float(area_px):.0f}"
                except:
                     pass

            self.tree_bubbles.insert("", "end", values=(
                b.get('stt', ''),
                cx,
                cy,
                area_px,
                area_mm
            ))
            
    def update_visualization(self):
        # Determine Checkbox state
        show_orig = self.vm.show_original.get()
        show_mask = self.vm.show_mask.get()
        show_res = self.vm.show_result.get()
        
        active_plots = []
        if show_res: active_plots.append('res')
        if show_mask: active_plots.append('mask')
        if show_orig: active_plots.append('orig')
        
        n_plots = len(active_plots)
        
        # Clear previous
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        if self.figure:
            plt.close(self.figure)
            
        # Reset Buttons state
        self.btn_next.config(state=tk.DISABLED)
        self.btn_prev.config(state=tk.DISABLED)
        self.btn_all.config(state=tk.DISABLED)
        self.btn_clear.config(state=tk.DISABLED)
        self.stepper = None
            
        if n_plots == 0:
            return

        # Create Figure
        self.figure = Figure(figsize=(5*n_plots, 5), dpi=100)
        axes = self.figure.subplots(1, n_plots)
        
        if n_plots == 1:
            axes = [axes]
            
        # Plot Logic
        for i, ptype in enumerate(active_plots):
            ax = axes[i]
            if ptype == 'orig':
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                    ax.set_title("Original Image")
                else:
                    ax.text(0.5, 0.5, "Not Found", ha='center')
                    
            elif ptype == 'mask':
                # 1. Plot Background (Original Image)
                if self.vm.current_original_img is not None:
                     ax.imshow(self.vm.current_original_img, cmap='gray')
                
                # 2. Plot Overlay (Mask)
                if self.vm.current_mask_img is not None:
                    # Create transparent overlay for background (0)
                    mask = self.vm.current_mask_img
                    masked_overlay = np.ma.masked_where(mask == 0, mask)
                    
                    # Overlay with alpha
                    # cmap='nipy_spectral' gives good instance distinction
                    ax.imshow(masked_overlay, cmap='nipy_spectral', interpolation='nearest', alpha=0.5) 
                    ax.set_title("StarDist Mask Overlay")
                else:
                    if self.vm.current_original_img is None:
                        ax.text(0.5, 0.5, "Not Found", ha='center')
                    
            elif ptype == 'res':
                # This needs interaction
                if self.vm.current_original_img is not None:
                     ax.imshow(self.vm.current_original_img, cmap='gray')
                
                # Check if we have items
                if self.vm.current_result_items:
                    pass 
                else:
                    ax.text(0.5, 0.5, "No Results", ha='center')
                    
        # Put figure in Tk
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.fr_canvas)
        self.canvas.draw()
        
        # Add Toolbar (Placed in Control Panel)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.fr_toolbar)
        
        # Override set_message to update our label instead of toolbar label
        def set_message(s):
             self.lbl_coords.config(text=s)
        self.toolbar.set_message = set_message
        
        self.toolbar.update()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Now init Stepper if needed (Canvas exists now)
        if 'res' in active_plots:
            idx = active_plots.index('res')
            ax = axes[idx]
            if self.vm.current_result_items:
                # Stepper needs background image?
                # Stepper constructor: __init__(self, ax, visual_items, background_img=None)
                # We already plotted background on ax.
                self.stepper = BubbleStepper(ax, self.vm.current_result_items, self.vm.current_original_img)
                # Enable Buttons
                self.btn_next.config(state=tk.NORMAL)
                self.btn_prev.config(state=tk.NORMAL)
                self.btn_all.config(state=tk.NORMAL)
                self.btn_clear.config(state=tk.NORMAL)
