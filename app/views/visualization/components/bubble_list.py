import tkinter as tk
from tkinter import ttk

class BubbleList(ttk.Frame):
    def __init__(self, parent, viewmodel, on_select_callback):
        super().__init__(parent)
        self.vm = viewmodel
        self.on_select_callback = on_select_callback
        self.setup_ui()
        
    def setup_ui(self):
        b_cols = ("STT", "Center X", "Center Y", "Pixels", "Area (mm²)")
        self.tree = ttk.Treeview(self, columns=b_cols, show='headings', height=5)
        for col in b_cols:
            self.tree.heading(col, text=col)
        
        # Configure columns
        self.tree.column("STT", width=40, minwidth=30, anchor='center')
        self.tree.column("Center X", width=60, minwidth=50, anchor='center')
        self.tree.column("Center Y", width=60, minwidth=50, anchor='center')
        self.tree.column("Pixels", width=60, minwidth=50, anchor='center')
        self.tree.column("Area (mm²)", width=80, minwidth=60, anchor='center')
        
        # Scrollbar if needed, but usually this is in a pane that manages size.
        # Let's add scrollbar for safety
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=sb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
    def update_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for b in self.vm.bubble_list:
            # {stt, x, y, area_px, area_mm}
            cx = b.get('cx', '')
            cy = b.get('cy', '')
            
            # Format numbers
            try: cx = f"{float(cx):.0f}"
            except: pass
            
            try: cy = f"{float(cy):.0f}"
            except: pass
            
            area_mm = b.get('area_mm', '')
            try: area_mm = f"{float(area_mm):.4f}"
            except: pass
            
            area_px = b.get('area_px', 'N/A')
            if area_px != 'N/A':
                try: area_px = f"{float(area_px):.0f}"
                except: pass

            self.tree.insert("", "end", values=(
                b.get('stt', ''),
                cx,
                cy,
                area_px,
                area_mm
            ))
            
    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        # Get bubble index
        idx = self.tree.index(selected[0])
        self.on_select_callback(idx)

    def select_item(self, idx):
        children = self.tree.get_children()
        if 0 <= idx < len(children):
             self.tree.selection_set(children[idx])
             self.tree.focus(children[idx])
             self.tree.see(children[idx])
