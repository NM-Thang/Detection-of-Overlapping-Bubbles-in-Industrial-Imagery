import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
import matplotlib.pyplot as plt
import numpy as np

from app.utils.starbub.stepper import BubbleStepper
from .toolbar import CustomToolbar

class PlotsPanel(ttk.Frame):
    def __init__(self, parent, viewmodel, control_panel):
        super().__init__(parent)
        self.vm = viewmodel
        self.control_panel = control_panel # Reference to update toolbar in control panel
        
        self.figure = None
        self.canvas = None
        self.toolbar = None
        
        # Steppers
        self.stepper_rdc = None
        self.stepper_sd = None
        self.stepper = None # Active
        
        # Interaction state
        self.mask_ax = None
        
        # Bubble List reference (optional, for selection sync)
        self.bubble_list_ref = None
        
    def set_bubble_list_ref(self, ref):
        self.bubble_list_ref = ref

    def update_visualization(self):
        # Determine Checkbox state
        show_orig = self.vm.show_original.get()
        show_mask = self.vm.show_mask.get()
        show_res = self.vm.show_result.get()
        
        active_plots = []
        if show_res: active_plots.append('res')
        if show_mask: active_plots.append('mask')
        if show_orig: active_plots.append('orig')
        
        # Cleanup
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.figure:
            self.figure.clear()
            self.figure = None
            
        n_plots = len(active_plots)
        if n_plots == 0:
            return
            
        # Create Figure
        self.figure = Figure(figsize=(5*n_plots, 5), dpi=100)
        axes = self.figure.subplots(1, n_plots)
        if n_plots == 1: axes = [axes]
        
        # Reset Steppers
        self.stepper_rdc = None
        self.stepper_sd = None
        self.mask_ax = None
        
        for i, plot_type in enumerate(active_plots):
            ax = axes[i]
            ax.set_xticks([])
            ax.set_yticks([])
            
            if plot_type == 'orig':
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                    ax.set_title("Original Image")
                    
            elif plot_type == 'mask':
                self.mask_ax = ax
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                
                # Draw Masks
                if self.vm.current_json_details:
                    ax.set_title("StarDist")
                    # Store items for SD Stepper
                    sd_items = self.vm.get_stardist_visual_items()
                    if sd_items:
                        self.stepper_sd = BubbleStepper(ax, sd_items, self.vm.current_original_img)
                        
                elif self.vm.current_mask_img is not None:
                     # Color mask fallback
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
                
                # Click event for Detail (Manual mask click)
                # Note: Stepper also handles clicks. If stepper is active, it handles it.
                # If no stepper (fallback to colored mask), we need manual handler.
                if not self.stepper_sd:
                     self.figure.canvas.mpl_connect('button_press_event', self.on_mask_click)

            elif plot_type == 'res':
                if self.vm.current_original_img is not None:
                    ax.imshow(self.vm.current_original_img, cmap='gray')
                
                if self.vm.current_result_items:
                     self.stepper_rdc = BubbleStepper(ax, self.vm.current_result_items, self.vm.current_original_img)
                     ax.set_title("SD & RDC")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Update Toolbar
        if self.toolbar is not None:
            self.toolbar.destroy()
        
        # Inject toolbar into control panel's frame
        if self.control_panel and self.control_panel.fr_toolbar:
            # Clean up old toolbar from that frame if any? 
            # Actually CustomToolbar packs itself into 'window' arg.
            for child in self.control_panel.fr_toolbar.winfo_children():
                child.destroy()
                
            self.toolbar = CustomToolbar(self.canvas, self.control_panel.fr_toolbar, coord_label=self.control_panel.lbl_coords)
            self.toolbar.update()
            self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
            
    def set_active_stepper(self, mode):
        # "RDC" or "SD"
        if mode == "RDC":
            self.stepper = self.stepper_rdc
        elif mode == "SD":
            self.stepper = self.stepper_sd
        else:
            self.stepper = None
            
        return self.stepper

    def on_mask_click(self, event):
        # Legacy handler for when Stepper is NOT active (e.g. static mask image)
        if not self.mask_ax or event.inaxes != self.mask_ax:
            return
            
        if event.button != 1: 
            return
        
        x, y = int(event.xdata), int(event.ydata)
        
        if self.vm.current_mask_img is not None:
             mask = self.vm.current_mask_img
             h, w = mask.shape
             if 0 <= y < h and 0 <= x < w:
                 label_id = mask[y, x]
                 if label_id > 0:
                     # Select corresponding item in TreeView
                     if self.bubble_list_ref:
                         idx = int(label_id) - 1
                         self.bubble_list_ref.select_item(idx)
                         
                     # Show Detail View (StarDist Raw Rays)
                     self.show_stardist_detail(int(label_id) - 1)

    def show_stardist_detail(self, idx):
        # Copied logic from original
        if not self.vm.current_json_details:
             messagebox.showerror("Data Missing", "No StarDist JSON details found.\nPlease re-run prediction.")
             return
             
        details = self.vm.current_json_details
        if 'coord' not in details:
            messagebox.showerror("Data Error", "'coord' data missing from JSON.")
            return

        def _get_item(data, i):
            if data is None: return None
            if isinstance(data, list): 
                return np.array(data[i])
            return data[i]

        try:
             coords_all = details.get('coord')
             poly = _get_item(coords_all, idx)
             poly = np.array(poly)
             if poly.shape[0] == 2 and poly.shape[1] > 2:
                 ys, xs = poly[0, :], poly[1, :]
             elif poly.shape[1] == 2 and poly.shape[0] > 2:
                 ys, xs = poly[:, 0], poly[:, 1]
             else:
                 raise ValueError(f"Unknown polygon shape: {poly.shape}")

             points = details.get('points') 
             pt = _get_item(points, idx)
             
             if pt is not None:
                 cy, cx = pt[0], pt[1]
             else:
                 cy, cx = np.mean(ys), np.mean(xs)

             prob = details.get('prob')
             p_val = _get_item(prob, idx) if prob is not None else 0
             
             n_rays = len(xs)
             segments = []
             for i in range(n_rays):
                 segments.append([(cx, cy), (xs[i], ys[i])])
             
             poly_x = np.append(xs, xs[0])
             poly_y = np.append(ys, ys[0])
             
             fig, ax = plt.subplots(figsize=(6, 6))
             ax.set_title(f"StarDist Detail (Coords): Bubble {idx+1}\nProb: {p_val:.4f}")
             
             if self.vm.current_original_img is not None:
                 ax.imshow(self.vm.current_original_img, cmap='gray')
             
             lc = LineCollection(segments, colors='lime', linewidths=0.5, alpha=0.6)
             ax.add_collection(lc)
             ax.plot(poly_x, poly_y, 'r-', linewidth=1.5)
             ax.plot(cx, cy, 'bo', markersize=4)
             
             min_x, max_x = min(poly_x), max(poly_x)
             min_y, max_y = min(poly_y), max(poly_y)
             pad = max(max_x - min_x, max_y - min_y) * 0.5
             ax.set_xlim(min_x - pad, max_x + pad)
             ax.set_ylim(max_y + pad, min_y - pad)
             
             plt.tight_layout()
             plt.show(block=False) # Important fix from previous tasks
             
        except Exception as e:
            print(f"Error showing Stardist detail: {e}")
            messagebox.showerror("Error", f"Could not show detail: {e}")
