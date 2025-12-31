import tkinter as tk
from tkinter import ttk


class PreprocessingPanel(ttk.Frame):
    """Collapsible panel for image preprocessing options: Flatfield, DoG, Lanczos."""
    
    def __init__(self, parent, viewmodel):
        super().__init__(parent)
        self.vm = viewmodel
        self.is_expanded = tk.BooleanVar(value=False)
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        # ========== HEADER (always visible) ==========
        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        
        self.toggle_btn = ttk.Button(
            header, text="▶ 3. Preprocessing Options (Advanced)", 
            command=self.toggle_panel,
            style="Toolbutton"
        )
        self.toggle_btn.pack(fill=tk.X, pady=2)
        
        # ========== COLLAPSIBLE CONTENT ==========
        self.content_frame = ttk.LabelFrame(self, text="Preprocessing Options")
        # Start collapsed - don't pack
        
        # Main container inside content
        container = ttk.Frame(self.content_frame)
        container.pack(fill=tk.X, padx=10, pady=5)
        
        # ========== FLATFIELD SECTION ==========
        flatfield_frame = ttk.LabelFrame(container, text="Flatfield Correction")
        flatfield_frame.pack(fill=tk.X, pady=5)
        
        # Enable checkbox
        fr_enable = ttk.Frame(flatfield_frame)
        fr_enable.pack(fill=tk.X, padx=5, pady=2)
        
        self.chk_flatfield = ttk.Checkbutton(
            fr_enable, text="Enable Flatfield Correction", 
            variable=self.vm.use_flatfield,
            command=self._on_flatfield_toggle
        )
        self.chk_flatfield.pack(side=tk.LEFT)
        
        # Option 1: Load existing flat
        fr_load = ttk.Frame(flatfield_frame)
        fr_load.pack(fill=tk.X, padx=5, pady=2)
        
        self.radio_load = ttk.Radiobutton(
            fr_load, text="Load existing flat:", 
            variable=self.vm.flat_source,
            value="load", width=22
        )
        self.radio_load.pack(side=tk.LEFT)
        
        self.btn_flatfield_browse = ttk.Button(
            fr_load, text="Browse...", 
            command=self.vm.select_flatfield_ref,
            width=14
        )
        self.btn_flatfield_browse.pack(side=tk.LEFT, padx=5)
        
        self.lbl_flatfield_path = ttk.Label(
            fr_load, textvariable=self.vm.flatfield_ref_path,
            foreground="gray", width=35
        )
        self.lbl_flatfield_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Option 2: Generate from images
        fr_gen = ttk.Frame(flatfield_frame)
        fr_gen.pack(fill=tk.X, padx=5, pady=2)
        
        self.radio_gen = ttk.Radiobutton(
            fr_gen, text="Generate from images:", 
            variable=self.vm.flat_source,
            value="generate"
        )
        self.radio_gen.pack(side=tk.LEFT)
        
        self.btn_select_images = ttk.Button(
            fr_gen, text="Select Images...", 
            command=self.vm.select_flat_gen_images,
            width=14
        )
        self.btn_select_images.pack(side=tk.LEFT, padx=5)
        
        self.lbl_gen_count = ttk.Label(
            fr_gen, textvariable=self.vm.flat_gen_count,
            foreground="blue"
        )
        self.lbl_gen_count.pack(side=tk.LEFT, padx=5)
        
        # Smoothing options row
        fr_smooth = ttk.Frame(flatfield_frame)
        fr_smooth.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(fr_smooth, text="    Smoothing:").pack(side=tk.LEFT)
        
        self.combo_smooth = ttk.Combobox(
            fr_smooth, textvariable=self.vm.flat_smooth_method,
            values=["blur", "resize", "none"], width=8, state='readonly'
        )
        self.combo_smooth.pack(side=tk.LEFT, padx=5)
        self.combo_smooth.set("resize")
        self.combo_smooth.bind("<<ComboboxSelected>>", self._on_smooth_method_change)
        
        ttk.Label(fr_smooth, text="Blur kernel:").pack(side=tk.LEFT, padx=(15, 2))
        self.entry_kernel = ttk.Entry(fr_smooth, textvariable=self.vm.flat_blur_kernel, width=5)
        self.entry_kernel.pack(side=tk.LEFT)
        
        ttk.Label(fr_smooth, text="Shrink÷:").pack(side=tk.LEFT, padx=(15, 2))
        self.entry_shrink = ttk.Entry(fr_smooth, textvariable=self.vm.flat_shrink_size, width=4)
        self.entry_shrink.pack(side=tk.LEFT)
        
        # Action buttons row
        fr_actions = ttk.Frame(flatfield_frame)
        fr_actions.pack(fill=tk.X, padx=5, pady=5)
        
        self.btn_generate = ttk.Button(
            fr_actions, text="Generate Flat", 
            command=self.vm.generate_flat_frame,
            style="Accent.TButton"
        )
        self.btn_generate.pack(side=tk.LEFT, padx=5)
        
        self.btn_preview = ttk.Button(
            fr_actions, text="Preview Flat", 
            command=self.vm.preview_flat_frame
        )
        self.btn_preview.pack(side=tk.LEFT, padx=5)
        
        self.lbl_flat_status = ttk.Label(
            fr_actions, textvariable=self.vm.flat_gen_status,
            foreground="green"
        )
        self.lbl_flat_status.pack(side=tk.LEFT, padx=10)
        
        # ========== DOG SECTION ==========
        fr_dog = ttk.Frame(container)
        fr_dog.pack(fill=tk.X, pady=2)
        
        self.chk_dog = ttk.Checkbutton(
            fr_dog, text="DoG (Difference of Gaussians)", 
            variable=self.vm.use_dog,
            command=self._on_dog_toggle
        )
        self.chk_dog.pack(side=tk.LEFT)
        
        ttk.Label(fr_dog, text="σ1:").pack(side=tk.LEFT, padx=(20, 2))
        self.entry_sigma1 = ttk.Entry(fr_dog, textvariable=self.vm.dog_sigma1, width=6)
        self.entry_sigma1.pack(side=tk.LEFT)
        
        ttk.Label(fr_dog, text="σ2:").pack(side=tk.LEFT, padx=(15, 2))
        self.entry_sigma2 = ttk.Entry(fr_dog, textvariable=self.vm.dog_sigma2, width=6)
        self.entry_sigma2.pack(side=tk.LEFT)
        
        # ========== LANCZOS SECTION ==========
        fr_lanczos = ttk.Frame(container)
        fr_lanczos.pack(fill=tk.X, pady=2)
        
        self.chk_lanczos = ttk.Checkbutton(
            fr_lanczos, text="Lanczos Upscale", 
            variable=self.vm.use_lanczos,
            command=self._on_lanczos_toggle
        )
        self.chk_lanczos.pack(side=tk.LEFT)
        
        ttk.Label(fr_lanczos, text="Scale:").pack(side=tk.LEFT, padx=(20, 2))
        self.combo_scale = ttk.Combobox(
            fr_lanczos, textvariable=self.vm.lanczos_scale, 
            values=[2, 3, 4], width=5, state='readonly'
        )
        self.combo_scale.pack(side=tk.LEFT)
        self.combo_scale.set(2)
        
        # Initial state
        self._on_flatfield_toggle()
        self._on_dog_toggle()
        self._on_lanczos_toggle()
        self._update_smooth_fields()
    
    def toggle_panel(self):
        """Toggle expand/collapse and resize window height accordingly."""
        root = self.winfo_toplevel()
        current_width = root.winfo_width()  # Keep current width
        
        if self.is_expanded.get():
            # Collapse
            self.content_frame.pack_forget()
            self.toggle_btn.config(text="▶ 3. Preprocessing Options (Advanced)")
            self.is_expanded.set(False)
            # Shrink window height only
            root.update_idletasks()
            new_height = root.winfo_reqheight()
            root.geometry(f"{current_width}x{new_height}")
        else:
            # Expand
            self.content_frame.pack(fill=tk.X, padx=5, pady=5)
            self.toggle_btn.config(text="▼ 3. Preprocessing Options (Advanced)")
            self.is_expanded.set(True)
            # Grow window height only
            root.update_idletasks()
            new_height = root.winfo_reqheight()
            root.geometry(f"{current_width}x{new_height}")
    
    def setup_bindings(self):
        # Update flatfield checkbox state based on ref path
        self.vm.flatfield_ref_path.trace_add("write", self._update_flatfield_state)
        self.vm.flat_source.trace_add("write", self._on_flat_source_change)
    
    def _on_flatfield_toggle(self):
        """Enable/disable flatfield controls based on checkbox."""
        enabled = self.vm.use_flatfield.get()
        state = tk.NORMAL if enabled else tk.DISABLED
        
        self.radio_load.config(state=state)
        self.radio_gen.config(state=state)
        self.btn_flatfield_browse.config(state=state)
        self.btn_select_images.config(state=state)
        self.combo_smooth.config(state='readonly' if enabled else tk.DISABLED)
        self.entry_kernel.config(state=state)
        self.entry_shrink.config(state=state)
        self.btn_generate.config(state=state)
        self.btn_preview.config(state=state)
        
        if enabled:
            self._on_flat_source_change()
        
    def _update_flatfield_state(self, *args):
        self._on_flatfield_toggle()
    
    def _on_flat_source_change(self, *args):
        """Update UI based on load vs generate selection."""
        source = self.vm.flat_source.get()
        enabled = self.vm.use_flatfield.get()
        
        if source == "load":
            self.btn_flatfield_browse.config(state=tk.NORMAL if enabled else tk.DISABLED)
            self.btn_select_images.config(state=tk.DISABLED)
            self.combo_smooth.config(state=tk.DISABLED)
            self.entry_kernel.config(state=tk.DISABLED)
            self.entry_shrink.config(state=tk.DISABLED)
            self.btn_generate.config(state=tk.DISABLED)
        else:  # generate
            self.btn_flatfield_browse.config(state=tk.DISABLED)
            self.btn_select_images.config(state=tk.NORMAL if enabled else tk.DISABLED)
            self.combo_smooth.config(state='readonly' if enabled else tk.DISABLED)
            self.btn_generate.config(state=tk.NORMAL if enabled else tk.DISABLED)
            # Update kernel/shrink based on smooth method
            self._update_smooth_fields()
    
    def _on_smooth_method_change(self, event=None):
        """Enable/disable blur kernel or shrink based on smooth method."""
        self._update_smooth_fields()
    
    def _update_smooth_fields(self):
        """Update blur kernel and shrink fields based on smooth method."""
        enabled = self.vm.use_flatfield.get() and self.vm.flat_source.get() == "generate"
        method = self.vm.flat_smooth_method.get()
        
        if not enabled:
            self.entry_kernel.config(state=tk.DISABLED)
            self.entry_shrink.config(state=tk.DISABLED)
        elif method == "blur":
            self.entry_kernel.config(state=tk.NORMAL)
            self.entry_shrink.config(state=tk.DISABLED)
        elif method == "resize":
            self.entry_kernel.config(state=tk.DISABLED)
            self.entry_shrink.config(state=tk.NORMAL)
        else:  # none
            self.entry_kernel.config(state=tk.DISABLED)
            self.entry_shrink.config(state=tk.DISABLED)
    
    def _on_dog_toggle(self):
        """Enable/disable DoG controls based on checkbox."""
        enabled = self.vm.use_dog.get()
        state = tk.NORMAL if enabled else tk.DISABLED
        self.entry_sigma1.config(state=state)
        self.entry_sigma2.config(state=state)
    
    def _on_lanczos_toggle(self):
        """Enable/disable Lanczos controls based on checkbox."""
        enabled = self.vm.use_lanczos.get()
        state = 'readonly' if enabled else tk.DISABLED
        self.combo_scale.config(state=state)
    
    def update_state(self, is_busy):
        """Called when processing starts/stops."""
        state = tk.DISABLED if is_busy else tk.NORMAL
        self.toggle_btn.config(state=state)
        self.chk_flatfield.config(state=state)
        self.chk_dog.config(state=state)
        self.chk_lanczos.config(state=state)
        
        if not is_busy:
            self._on_flatfield_toggle()
            self._on_dog_toggle()
            self._on_lanczos_toggle()
        else:
            self.radio_load.config(state=tk.DISABLED)
            self.radio_gen.config(state=tk.DISABLED)
            self.btn_flatfield_browse.config(state=tk.DISABLED)
            self.btn_select_images.config(state=tk.DISABLED)
            self.combo_smooth.config(state=tk.DISABLED)
            self.entry_kernel.config(state=tk.DISABLED)
            self.entry_shrink.config(state=tk.DISABLED)
            self.btn_generate.config(state=tk.DISABLED)
            self.btn_preview.config(state=tk.DISABLED)
            self.entry_sigma1.config(state=tk.DISABLED)
            self.entry_sigma2.config(state=tk.DISABLED)
            self.combo_scale.config(state=tk.DISABLED)
