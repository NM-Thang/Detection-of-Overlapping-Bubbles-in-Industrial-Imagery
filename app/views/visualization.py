import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import cv2
from matplotlib.collections import LineCollection
from app.utils.starbub.stepper import BubbleStepper

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

class VisualizationView(ttk.Frame):
    def __init__(self, parent, viewmodel):
        super().__init__(parent)
        self.vm = viewmodel
        
        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.stepper_rdc = None # Persistence for RDC
        self.stepper_sd = None # Persistence for StarDist
        self.stepper = None # Active reference
        
        # Flash animation state
        self.flash_job = None
        self.flash_artists = []
        
        self.mask_ax = None
        
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
        
        # Main Paned Window (Horizontal Split)
        self.paned_main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_main.pack(fill=tk.BOTH, expand=True)
        
        # --- LEFT PANE: Image List + Controls ---
        fr_left_container = ttk.Frame(self.paned_main, width=240)
        fr_left_container.pack_propagate(False) # Prevent frame from shrinking to fit content
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

        # Target Mode Switch
        fr_target = ttk.LabelFrame(fr_controls, text="Control Target")
        fr_target.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        ttk.Radiobutton(fr_target, text="SD & RDC", variable=self.vm.control_mode, value="RDC", command=lambda: self.vm.set_control_mode("RDC")).pack(side=tk.LEFT, expand=True)
        ttk.Radiobutton(fr_target, text="StarDist", variable=self.vm.control_mode, value="SD", command=lambda: self.vm.set_control_mode("SD")).pack(side=tk.LEFT, expand=True)
        





        # --- RIGHT PANE: Detail + Visualization ---
        fr_right = ttk.Frame(self.paned_main)
        self.paned_main.add(fr_right, weight=8) # Give more space
        
        self.paned_right = ttk.PanedWindow(fr_right, orient=tk.VERTICAL)
        self.paned_right.pack(fill=tk.BOTH, expand=True)
        
        # Top Right: Split into Statistics (Left) and Bubble List (Right)
        fr_top_right = ttk.Frame(self.paned_right)
        self.paned_right.add(fr_top_right, weight=0) # weight=0 to respect height

        # Create Horizontal Pane for Top Right
        self.paned_top_right = ttk.PanedWindow(fr_top_right, orient=tk.HORIZONTAL)
        self.paned_top_right.pack(fill=tk.BOTH, expand=True)

        # 1. Statistics (Left)
        fr_stats_container = ttk.Frame(self.paned_top_right)
        self.paned_top_right.add(fr_stats_container, weight=1)
        
        fr_stats = ttk.LabelFrame(fr_stats_container, text="Statistics")
        fr_stats.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Configure Grid Columns to expand
        fr_stats.columnconfigure(0, weight=1)
        fr_stats.columnconfigure(1, weight=1)
        fr_stats.columnconfigure(2, weight=1)
        
        # Custom Grid Layout for 2-Column Stats
        # Headers
        ttk.Label(fr_stats, text="Metric", font=('Helvetica', 9, 'italic')).grid(row=0, column=0, sticky='w', padx=2)
        ttk.Label(fr_stats, text="SD & RDC", font=('Helvetica', 9, 'bold')).grid(row=0, column=1, padx=5)
        ttk.Label(fr_stats, text="StarDist", font=('Helvetica', 9, 'bold'), foreground='blue').grid(row=0, column=2, padx=5)

        current_row = 1
        def add_2col_row(label, var_final, var_sd=None):
            nonlocal current_row
            ttk.Label(fr_stats, text=label+":", font=('Helvetica', 9)).grid(row=current_row, column=0, sticky='w', pady=1)
            # Center values by removing sticky='e'
            ttk.Label(fr_stats, textvariable=var_final, font=('Helvetica', 9)).grid(row=current_row, column=1, padx=5)
            if var_sd:
                 ttk.Label(fr_stats, textvariable=var_sd, font=('Helvetica', 9), foreground='blue').grid(row=current_row, column=2, padx=5)
            current_row += 1

        add_2col_row("Count", self.vm.stat_bubble_count, self.vm.stat_sd_count)
        add_2col_row("Area (px)", self.vm.stat_bub_area_px, self.vm.stat_sd_area_px)
        add_2col_row("Area (mm²)", self.vm.stat_bub_area_mm, self.vm.stat_sd_area_mm)
        add_2col_row("Ratio (%)", self.vm.stat_ratio_mm, self.vm.stat_sd_ratio)
        
        # Separator or Space
        ttk.Separator(fr_stats, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', pady=5)
        current_row += 1
        
        # Single items
        def add_single_row(label, var):
             nonlocal current_row
             ttk.Label(fr_stats, text=label+":", font=('Helvetica', 9)).grid(row=current_row, column=0, sticky='w')
             ttk.Label(fr_stats, textvariable=var, font=('Helvetica', 9, 'bold')).grid(row=current_row, column=1, columnspan=2, sticky='w')
             current_row += 1

        add_single_row("Img Size", self.vm.stat_img_size)
        add_single_row("Mean Prob", self.vm.stat_sd_prob)

        # 2. Bubble List (Right)
        fr_bubbles = ttk.Frame(self.paned_top_right)
        self.paned_top_right.add(fr_bubbles, weight=3)
        

        
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
        
        ttk.Checkbutton(fr_viz_opts, text="SD & RDC", variable=self.vm.show_result, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(fr_viz_opts, text="StarDist", variable=self.vm.show_mask, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(fr_viz_opts, text="Original", variable=self.vm.show_original, command=self.vm.toggle_view).pack(side=tk.LEFT, padx=5)
        
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
        
        # Interaction state
        self.mask_ax = None

    def on_mask_click(self, event):
        if not self.mask_ax or event.inaxes != self.mask_ax:
            return
            
        if event.button != 1: # Left click only
            return
        
        x, y = int(event.xdata), int(event.ydata)
        
        if self.vm.current_mask_img is not None:
             mask = self.vm.current_mask_img
             h, w = mask.shape
             if 0 <= y < h and 0 <= x < w:
                 label_id = mask[y, x]
                 if label_id > 0:
                     # Select corresponding item in TreeView
                     # Assuming order matches (Index = ID - 1)
                     children = self.tree_bubbles.get_children()
                     idx = int(label_id) - 1
                     if 0 <= idx < len(children):
                         self.tree_bubbles.selection_set(children[idx])
                         self.tree_bubbles.focus(children[idx])
                         self.tree_bubbles.see(children[idx])
                         
                     # Show Detail View (StarDist Raw Rays)
                     self.show_stardist_detail(idx)

    def show_stardist_detail(self, idx):
        if not self.vm.current_json_details:
             messagebox.showerror("Data Missing", "No StarDist JSON details found.\nPlease re-run prediction.")
             return
             
        details = self.vm.current_json_details
        
        # We need 'coord' at minimum
        if 'coord' not in details:
            messagebox.showerror("Data Error", "'coord' data missing from JSON.")
            return

        # Helper to get item from list/array
        def _get_item(data, i):
            if data is None: return None
            if isinstance(data, list): 
                return np.array(data[i])
            return data[i]

        try:
             # 1. Get Polygon Coords (Vertices)
             coords_all = details.get('coord')
             poly = _get_item(coords_all, idx) # Shape usually (2, N_rays)
             
             # StarDist coords are (y, x). Transpose if needed.
             # If shape is (2, N), Row 0 is Y, Row 1 is X.
             poly = np.array(poly)
             if poly.shape[0] == 2 and poly.shape[1] > 2:
                 ys = poly[0, :]
                 xs = poly[1, :]
             elif poly.shape[1] == 2 and poly.shape[0] > 2:
                 # (N, 2)
                 ys = poly[:, 0]
                 xs = poly[:, 1]
             else:
                 raise ValueError(f"Unknown polygon shape: {poly.shape}")

             # 2. Get/Calc Center
             points = details.get('points') 
             pt = _get_item(points, idx)
             
             if pt is not None:
                 cy, cx = pt[0], pt[1]
             else:
                 # Fallback: Centroid of polygon
                 cy = np.mean(ys)
                 cx = np.mean(xs)

             # 3. Prob
             prob = details.get('prob')
             p_val = _get_item(prob, idx) if prob is not None else 0
             
             # 4. Prepare Plot Data
             # Rays: Line from (cx, cy) to (xs[i], ys[i])
             n_rays = len(xs)
             segments = []
             for i in range(n_rays):
                 segments.append([(cx, cy), (xs[i], ys[i])])
             
             # Polygon Loop
             poly_x = np.append(xs, xs[0])
             poly_y = np.append(ys, ys[0])
             
             # 5. Draw
             fig, ax = plt.subplots(figsize=(6, 6))
             ax.set_title(f"StarDist Detail (Coords): Bubble {idx+1}\nProb: {p_val:.4f}")
             
             # Background
             if self.vm.current_original_img is not None:
                 ax.imshow(self.vm.current_original_img, cmap='gray')
             
             # Rays (Green)
             lc = LineCollection(segments, colors='lime', linewidths=0.5, alpha=0.6)
             ax.add_collection(lc)
             
             # Polygon (Red)
             ax.plot(poly_x, poly_y, 'r-', linewidth=1.5)
             
             # Center (Blue)
             ax.plot(cx, cy, 'bo', markersize=4)
             
             # Zoom
             min_x, max_x = min(poly_x), max(poly_x)
             min_y, max_y = min(poly_y), max(poly_y)
             pad = max(max_x - min_x, max_y - min_y) * 0.5
             ax.set_xlim(min_x - pad, max_x + pad)
             ax.set_ylim(max_y + pad, min_y - pad)
             
             plt.tight_layout()
             plt.show(block=False)
             
        except Exception as e:
            print(f"Error showing Stardist detail: {e}")
            messagebox.showerror("Error", f"Could not show detail: {e}")


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
        
        # Cleanup Previous Canvas to prevent stacking
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.figure:
            self.figure.clear()
            self.figure = None

        n_plots = len(active_plots)
        if n_plots == 0:
            return

        # 3. Create Figure
        self.figure = Figure(figsize=(5*n_plots, 5), dpi=100)
        axes = self.figure.subplots(1, n_plots)
        if n_plots == 1: axes = [axes]
        
        # 4. Plot Logic
        self.stepper_rdc = None
        self.stepper_sd = None
        
        for i, plot_type in enumerate(active_plots):
            ax = axes[i]
            # Disable axis ticks
            ax.set_xticks([])
            ax.set_yticks([])
            
            if plot_type == 'orig':
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                    ax.set_title("Original Image")
                    
            elif plot_type == 'mask':
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                
                # Draw Masks
                if self.vm.current_json_details:
                    details = self.vm.current_json_details
                    # We do NOT draw static mask here anymore.
                    # We rely on self.stepper_sd to handle visualization interactively.
                    ax.set_title("StarDist")
                    
                    # Store items for SD Stepper
                    sd_items = self.vm.get_stardist_visual_items()
                    if sd_items:
                        self.stepper_sd = BubbleStepper(ax, sd_items, self.vm.current_original_img)

                elif self.vm.current_mask_img is not None:
                     # Helper to create colored mask
                     mask = self.vm.current_mask_img
                     h, w = mask.shape
                     color_mask = np.zeros((h, w, 4), dtype=np.float32)
                     unique_labels = np.unique(mask)
                     for label in unique_labels:
                         if label == 0: continue
                         color = plt.cm.tab20(label % 20)
                         color_mask[mask == label] = color
                     ax.imshow(color_mask)
                     ax.set_title("StarDist")
                     
                # Click event for Detail
                self.canvas_click_cid = self.figure.canvas.mpl_connect('button_press_event', self.on_mask_click)

            elif plot_type == 'res':
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                
                # Static Result Drawing (Optional, maybe RDC also should rely purely on Stepper?)
                # Previously RDC drew static. Let's keep it consistent?
                # User liked RDC as is. RDC usually has static drawing...
                # Actually, in 'on_show_all' stepper draws everything.
                # If we rely on stepper, we don't need static drawing here.
                # If I remove static lines, RDC plot starts empty.
                # User might want to see the result immediately.
                # So maybe I should call `show_all()` on stepper_rdc immediately?
                # Let's do that for RDC to match "Result" expectation.
                if self.vm.current_result_items:
                     self.stepper_rdc = BubbleStepper(ax, self.vm.current_result_items, self.vm.current_original_img)
                     # self.stepper_rdc.show_all() # Removed as per user request
                     ax.set_title("SD & RDC")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.fr_canvas)
        self.canvas.draw()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        if hasattr(self, 'toolbar') and self.toolbar is not None:
            self.toolbar.destroy()
        self.toolbar = CustomToolbar(self.canvas, self.fr_toolbar, coord_label=self.lbl_coords)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind Control
        self.update_control_binding()

    def update_control_binding(self):
        # Determine Active Stepper based on Control Mode
        mode = self.vm.control_mode.get()
        
        if mode == "RDC":
            self.stepper = self.stepper_rdc
        elif mode == "SD":
            self.stepper = self.stepper_sd
        else:
            self.stepper = None
            
        # Update Button States
        state = tk.NORMAL if self.stepper else tk.DISABLED
        self.btn_next.config(state=state)
        self.btn_prev.config(state=state)
        self.btn_all.config(state=state)
        self.btn_clear.config(state=state)
