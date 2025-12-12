import tkinter as tk
from tkinter import ttk

class ImageList(ttk.Frame):
    def __init__(self, parent, viewmodel, on_select_callback):
        super().__init__(parent)
        self.vm = viewmodel
        self.on_select_callback = on_select_callback
        self.setup_ui()
        
    def setup_ui(self):
        cols = ("STT", "Image Name")
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        self.tree.heading("STT", text="STT")
        self.tree.heading("Image Name", text="Image Name")
        self.tree.column("STT", width=35, stretch=False, anchor='center')
        self.tree.column("Image Name", width=65, stretch=True)
        
        # Scrollbar
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
    def update_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, name in enumerate(self.vm.image_list):
            self.tree.insert("", "end", values=(i+1, name))
            
        # Select first item if exists
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])
            
    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            # Check if values exist and are valid
            item = self.tree.item(selected[0])
            if item and 'values' in item and item['values']:
                try:
                    idx = int(item['values'][0]) - 1
                    self.on_select_callback(idx)
                except ValueError:
                    pass
