import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.collections import LineCollection
from matplotlib.patches import Ellipse
import numpy as np
import math

class BubbleStepper:
    def __init__(self, ax, visual_items, background_img=None):
        self.ax = ax
        self.visual_items = visual_items
        self.background_img = background_img
        self.current_idx = -1
        self.artists = [] 
        self.detail_fig = None
        
        # Connect key press event for keyboard navigation
        self.ax.figure.canvas.mpl_connect('key_press_event', self.on_key)
        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_click)

        print("Interactive Mode: Press Right/Next to draw bubble, Left/Prev to undo. Click on bubble to view detail with rays.")
        
    def next(self, event=None):
        if self.current_idx < len(self.visual_items) - 1:
            self.current_idx += 1
            item = self.visual_items[self.current_idx]
            self.draw_item(item)
            self.ax.figure.canvas.draw_idle()

    def prev(self, event=None):
        if self.current_idx >= 0:
            if self.artists:
                last_artists = self.artists.pop()
                for art in last_artists:
                    art.remove()
                self.current_idx -= 1
                self.ax.figure.canvas.draw_idle()

    def prev(self, event=None):
        if self.current_idx >= 0:
            if self.artists:
                last_artists = self.artists.pop()
                for art in last_artists:
                    art.remove()
                self.current_idx -= 1
                self.ax.figure.canvas.draw_idle()

    def show_all(self, event=None):
        starting_idx = self.current_idx
        # Draw all remaining items
        for i in range(starting_idx + 1, len(self.visual_items)):
            self.current_idx = i
            item = self.visual_items[i]
            self.draw_item(item)
        self.ax.figure.canvas.draw_idle()

    def clear_all(self, event=None):
        # Remove all artists
        for group in self.artists:
            for art in group:
                art.remove()
        self.artists.clear()
        self.current_idx = -1
        self.ax.figure.canvas.draw_idle()

    def draw_item(self, item, draw_rays=False):
        new_artists = self._render_item(item, draw_rays=draw_rays)
        self.artists.append(new_artists)
        
    def create_highlight_artists(self, idx):
        if 0 <= idx < len(self.visual_items):
            item = self.visual_items[idx]
            # Draw with highlight style (e.g. thicker, maybe a specific color override if desired)
            # For now, we'll keep original color but ensure it's on top and visible
            # We can use a thicker linewidth to make it pop
            return self._render_item(item, linewidth_scale=2.5, zorder_override=999)
        return []

    def _render_item(self, item, draw_rays=False, color_override=None, linewidth_scale=1.0, zorder_override=None):
        new_artists = []
        base_zorder = zorder_override if zorder_override else 1
        
        if item['type'] == 'rdc':
            points = item['points']
            color = color_override if color_override else item['color']
            a, b = list(points[:, 1]), list(points[:, 0])
            a += a[:1]
            b += b[:1]
            
            lines = self.ax.plot(a, b, '-', alpha=1, zorder=base_zorder, color=color, linewidth=1.5 * linewidth_scale)
            new_artists.extend(lines)
            
            if draw_rays and 'center' in item:
                center = item['center']
                num_rays = len(points)
                dist_lines = np.empty((num_rays, 2, 2))
                dist_lines[:, 0, 0] = points[:, 1]
                dist_lines[:, 0, 1] = points[:, 0]
                dist_lines[:, 1, 0] = center[1]
                dist_lines[:, 1, 1] = center[0]
                lc = LineCollection(dist_lines, colors=color, linewidths=0.6 * linewidth_scale, alpha=0.7, zorder=base_zorder)
                self.ax.add_collection(lc)
                new_artists.append(lc)
                
        elif item['type'] == 'ellipse':
            params = item['params']
            color = color_override if color_override else item['color']
            y0, x0, a, b, phi = params
            ellipse = Ellipse((y0, x0), 2*a, 2*b, angle=math.degrees(phi), alpha=0.25, color=color, zorder=base_zorder)
            # Make ellipse edge thicker if highlighted
            if linewidth_scale > 1.0:
                ellipse.set_linewidth(1.0 * linewidth_scale)
                ellipse.set_fill(False) # Or keep fill? Let's keep fill but add thick edge
                # If we want thick edge we might need another artist or set edge props
                # Ellipse patch support
                
            self.ax.add_artist(ellipse)
            new_artists.append(ellipse)
            
        return new_artists
    
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        click_x, click_y = event.xdata, event.ydata
        
        matches = []
        for idx in range(self.current_idx + 1):
            item = self.visual_items[idx]
            is_hit = False
            area = float('inf')
            
            if item['type'] == 'rdc':
                points = item['points']
                center = item.get('center', None)
                if center is None:
                    continue
                from matplotlib.path import Path
                polygon_path = Path(np.column_stack([points[:, 1], points[:, 0]]))
                if polygon_path.contains_point((click_x, click_y)):
                    is_hit = True
                    # Use pixel count as proxy for area size, or bounding box
                    try:
                        area = float(item.get('pixel_count', 0))
                    except:
                        area = 0
            
            elif item['type'] == 'ellipse':
                params = item['params']
                y0, x0, a, b, phi = params
                dx = click_x - y0
                dy = click_y - x0
                cos_phi = np.cos(-phi)
                sin_phi = np.sin(-phi)
                dx_rot = dx * cos_phi - dy * sin_phi
                dy_rot = dx * sin_phi + dy * cos_phi
                if (dx_rot**2 / a**2 + dy_rot**2 / b**2) <= 1:
                    is_hit = True
                    area = math.pi * a * b
            
            if is_hit:
                matches.append((area, item, idx))
        
        # If overlapping, handle selection
        if matches:
            matches.sort(key=lambda x: x[0]) # Sort by area ascending
            
            if len(matches) == 1:
                # Single match: Show directly
                best_match = matches[0]
                self.show_bubble_detail(best_match[1], best_match[2])
            else:
                # Multiple matches: Show Popup Menu
                import tkinter as tk
                
                # We need screen coordinates for Tkinter Menu
                # Matplotlib event.guiEvent is the native GUI event (Tkinter event in this backend)
                try:
                    x_root = int(event.guiEvent.x_root)
                    y_root = int(event.guiEvent.y_root)
                    
                    menu = tk.Menu(None, tearoff=0)
                    menu.add_command(label="Select Bubble:", state="disabled")
                    menu.add_separator()
                    
                    for area, item, idx in matches:
                        stt = item.get('stt', idx + 1)
                        label = f"Bubble {stt} (Area: {area:.0f} px)"
                        
                        # Use default argument capture for lambda closure
                        def _callback(i=item, x=idx):
                            self.show_bubble_detail(i, x)
                            
                        menu.add_command(label=label, command=_callback)
                    
                    menu.post(x_root, y_root)
                    
                except Exception as e:
                    print(f"Error showing popup: {e}")
                    # Fallback to smallest
                    best_match = matches[0]
                    self.show_bubble_detail(best_match[1], best_match[2])
    
    def show_bubble_detail(self, item, idx):
        if self.detail_fig is not None and plt.fignum_exists(self.detail_fig.number):
            plt.close(self.detail_fig)
        fig, ax = plt.subplots(figsize=(8, 8))
        self.detail_fig = fig
        if self.background_img is not None:
            ax.imshow(self.background_img, cmap='gray')
        if item['type'] == 'rdc':
            points = item['points']
            color = item['color']
            center = item.get('center', None)
            dists = item.get('dists', None)
            pixel_count = item.get('pixel_count', 'N/A')
            if len(points) > 2:
                poly_area = 0.5 * np.abs(np.dot(points[:, 1], np.roll(points[:, 0], 1)) - np.dot(points[:, 0], np.roll(points[:, 1], 1)))
            else:
                poly_area = 0
            if center is not None:
                num_rays = len(points)
                dist_lines = np.empty((num_rays, 2, 2))
                dist_lines[:, 0, 0] = points[:, 1]
                dist_lines[:, 0, 1] = points[:, 0]
                dist_lines[:, 1, 0] = center[1]
                dist_lines[:, 1, 1] = center[0]
                lc = LineCollection(dist_lines, colors='green', linewidths=0.8, alpha=0.8, zorder=2)
                ax.add_collection(lc)
                ax.plot(center[1], center[0], 'ro', markersize=5, zorder=4)
            a, b = list(points[:, 1]), list(points[:, 0])
            a += a[:1]
            b += b[:1]
            ax.plot(a, b, '-', alpha=1, zorder=3, color=color, linewidth=2)
            info_text = f"Pixels: {pixel_count}\nArea (Poly): {poly_area:.1f}"
            if dists is not None:
                plt.figtext(0.02, 0.02, f"Rays (64): {np.array2string(dists, precision=1, separator=', ', suppress_small=True)}", 
                            fontsize=8, wrap=True, bbox=dict(facecolor='white', alpha=0.8))
            ax.text(0.05, 0.95, info_text, transform=ax.transAxes, verticalalignment='top', 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            min_x, max_x = min(points[:, 1]), max(points[:, 1])
            min_y, max_y = min(points[:, 0]), max(points[:, 0])
            padding = max(max_x - min_x, max_y - min_y) * 0.3
            ax.set_xlim(min_x - padding, max_x + padding)
            ax.set_ylim(max_y + padding, min_y - padding)
            
        elif item['type'] == 'ellipse':
            params = item['params']
            color = item['color']
            y0, x0, a, b, phi = params
            ellipse = Ellipse((y0, x0), 2*a, 2*b, angle=math.degrees(phi), alpha=0.5, color=color)
            ax.add_artist(ellipse)
            ax.plot(y0, x0, 'ro', markersize=5, zorder=4)
            padding = max(a, b) * 0.5
            ax.set_xlim(y0 - a - padding, y0 + a + padding)
            ax.set_ylim(x0 + b + padding, x0 - b - padding)
        
        
        stt = item.get('stt')
        title_id = stt if stt is not None else (idx + 1)
        ax.set_title(f'Bubble {title_id} Detail View')
        ax.set_aspect('equal')
        plt.tight_layout()
        plt.show()

    def on_key(self, event):
        if event.key == 'right':
            self.next()
        elif event.key == 'left':
            self.prev()
