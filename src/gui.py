import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageTk

from config import config_manager
from processor import PDFProcessor
from logger import app_logger

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x250")
        
        # Make it modal (blocks main window). Wait for window to be viewable first.
        self.transient(parent)
        self.after(100, self.grab_set)

        self.parent = parent

        # --- Output Directory ---
        ctk.CTkLabel(self, text="Output Directory", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), anchor="w", padx=20)
        
        dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        dir_frame.pack(fill="x", padx=20)
        
        self.out_dir_label = ctk.CTkLabel(dir_frame, text=config_manager.get("output_directory") or "Not Set", text_color="gray", wraplength=250)
        self.out_dir_label.pack(side="left", fill="x", expand=True)
        
        out_btn = ctk.CTkButton(dir_frame, text="Change", width=60, command=self.select_output_dir)
        out_btn.pack(side="right", padx=5)

        # --- Theme ---
        ctk.CTkLabel(self, text="Appearance", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), anchor="w", padx=20)
        
        self.theme_switch = ctk.CTkOptionMenu(self, values=["Light", "Dark", "System"], command=self.change_theme)
        self.theme_switch.pack(pady=5, anchor="w", padx=20)
        self.theme_switch.set(config_manager.get("theme", "System"))

    def select_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            config_manager.set("output_directory", directory)
            self.out_dir_label.configure(text=directory)
            self.parent.status_var.set("Output directory updated.")

    def change_theme(self, new_theme: str):
        ctk.set_appearance_mode(new_theme)
        config_manager.set("theme", new_theme)
        
        # Update canvas bg based on theme
        bg_color = "#2b2b2b" if new_theme.lower() == "dark" else "#e0e0e0"
        self.parent.canvas.configure(bg=bg_color)

class LeaveSorterApp(ctk.CTk):
    def __init__(self, tesseract_path: str, poppler_path: str):
        super().__init__()

        self.title("ADR Leave Parser")
        self.geometry("1100x800")
        
        # System matching theme preference
        saved_theme = config_manager.get("theme", "System")
        app_logger.debug(f"Setting appearance mode to: {saved_theme}")
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")

        self.processor = PDFProcessor(tesseract_path, poppler_path)
        
        self.current_page_index = 0
        self.total_pages = 0
        self.current_pdf_path = None
        self.base_image = None
        self.tk_image = None
        
        # Prefetching state
        self.page_cache = {}
        self.prefetch_lock = threading.Lock()
        
        # Zoom and pan state
        self.zoom_factor = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0

        self._build_ui()

    def _build_ui(self):
        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Sidebar (Left) ===
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ADR Leave Parser", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="Load PDF", command=self.load_pdf, fg_color="#2b5e8a", hover_color="#1f4464")
        self.load_btn.grid(row=1, column=0, padx=20, pady=10)

        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text="⚙ Settings", command=self.open_settings, fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
        self.settings_btn.grid(row=3, column=0, padx=20, pady=20)

        # === Main Content Area (Right) ===
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=3) # Canvas
        self.main_frame.grid_columnconfigure(1, weight=1) # Form

        # 1. Zoomable Canvas
        self.canvas_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.canvas_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # We use standard tk Canvas for image drawing and scrolling
        bg_color = "#2b2b2b" if config_manager.get("theme", "System").lower() == "dark" else "#e0e0e0"
        self.canvas = Canvas(self.canvas_frame, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Bindings for Pan and Zoom
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_drag)
        self.canvas.bind("<MouseWheel>", self._on_zoom)  # Windows
        self.canvas.bind("<Button-4>", self._on_zoom)    # Linux
        self.canvas.bind("<Button-5>", self._on_zoom)    # Linux

        # 2. Dynamic Input Form
        self.form_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="transparent")
        # Do NOT grid it initially. It will be shown only when a PDF is loaded.
        
        ctk.CTkLabel(self.form_frame, text="Extracted Data", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 10))

        self.entry_initial = ctk.CTkEntry(self.form_frame, placeholder_text="Initial")
        self.entry_initial.pack(pady=5, padx=10, fill="x")

        self.entry_lastname = ctk.CTkEntry(self.form_frame, placeholder_text="Last Name")
        self.entry_lastname.pack(pady=5, padx=10, fill="x")

        leave_types = ["Paid Vacational", "Unpaid Vacational", "Paid Sick", "Unpaid Sick", "Family Responsibility", "Paid compassionate", "Custom..."]
        self.entry_leavetype = ctk.CTkComboBox(self.form_frame, values=leave_types)
        self.entry_leavetype.pack(pady=5, padx=10, fill="x")

        self.entry_date = ctk.CTkEntry(self.form_frame, placeholder_text="Date (YYYY.MM.DD)")
        self.entry_date.pack(pady=5, padx=10, fill="x")

        # Action Buttons
        self.save_btn = ctk.CTkButton(self.form_frame, text="Confirm & Save", command=self.save_current_page, fg_color="#2e8b57", hover_color="#246b43")
        self.save_btn.pack(pady=(20, 5), padx=10, fill="x")

        self.skip_btn = ctk.CTkButton(self.form_frame, text="Skip Page", command=self.skip_page, fg_color="transparent", border_width=1)
        self.skip_btn.pack(pady=5, padx=10, fill="x")

        # Jump to page
        jump_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        jump_frame.pack(pady=10, padx=10, fill="x")
        self.entry_jump = ctk.CTkEntry(jump_frame, width=50, placeholder_text="Page")
        self.entry_jump.pack(side="left", padx=5)
        self.jump_btn = ctk.CTkButton(jump_frame, text="Go", width=40, command=self.jump_to_page)
        self.jump_btn.pack(side="left", padx=5)

        # Status
        self.page_status_var = ctk.StringVar(value="Page: 0 / 0")
        self.page_status_label = ctk.CTkLabel(self.form_frame, textvariable=self.page_status_var, font=ctk.CTkFont(weight="bold"))
        self.page_status_label.pack(side="bottom", pady=5)

        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(self.main_frame, textvariable=self.status_var, text_color="gray")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)

        # Global Hotkeys
        self.bind("<Control-s>", lambda event: self.save_current_page())
        self.bind("<Control-Right>", lambda event: self.skip_page())
        self.bind("<Control-Left>", lambda event: self.load_previous_page())

    def open_settings(self):
        # Open the settings popup
        if hasattr(self, "settings_window") and self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.focus()
        else:
            self.settings_window = SettingsWindow(self)

    def load_pdf(self):
        if not config_manager.get("output_directory"):
            messagebox.showwarning("Warning", "Please select an output directory in Settings first.")
            self.open_settings()
            return

        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.current_pdf_path = file_path
            
            with self.prefetch_lock:
                self.page_cache.clear()
                
            self.current_page_index = self.processor.load_pdf(file_path)
            self.total_pages = self.processor.total_pages
            self._load_page(self.current_page_index)

    def _load_page(self, index: int):
        if index >= self.total_pages:
            self.status_var.set("Finished all pages!")
            self.form_frame.grid_forget() # Hide form
            self.canvas.delete("all")
            return

        self.current_page_index = index
        self.processor.update_session(index)
        self.page_status_var.set(f"Page: {index + 1} / {self.total_pages}")
        
        # Show form if hidden
        self.form_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Clear fields
        self.entry_initial.delete(0, 'end')
        self.entry_lastname.delete(0, 'end')
        self.entry_date.delete(0, 'end')
        
        # Check if page is pre-loaded in cache
        cached_data = None
        with self.prefetch_lock:
            cached = self.page_cache.get(index)
            if cached is not None:
                cached_data = cached

        if cached_data:
            # Load instantly
            image, ocr_data = cached_data
            self.base_image = image
            self.zoom_factor = 1.0
            self._update_gui_after_thread(ocr_data)
            
            # Start prefetching the NEXT page
            threading.Thread(target=self._prefetch_page, args=(index+1,), daemon=True).start()
        else:
            # Blocking load
            self.status_var.set("Loading image & OCR...")
            self.canvas.delete("all")
            self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2, text="Processing...", fill="gray", font=("Arial", 20))
            threading.Thread(target=self._process_page_thread, args=(index,), daemon=True).start()

    def _process_page_thread(self, index: int):
        try:
            image, ocr_data = self.processor.get_page_preview(index)
            
            self.base_image = image # Store high-res for zooming
            self.zoom_factor = 1.0  # Reset zoom

            # Update GUI from main thread
            self.after(0, self._update_gui_after_thread, ocr_data)
            
            # Start prefetching the NEXT page
            threading.Thread(target=self._prefetch_page, args=(index+1,), daemon=True).start()
            
        except Exception as e:
            app_logger.error(f"Thread Error on page {index}: {e}", exc_info=True)
            self.after(0, lambda: self.status_var.set("Error loading page or OCR"))

    def _prefetch_page(self, index: int):
        """Silently extracts image and runs OCR for future pages in the background."""
        if index >= self.total_pages:
            return
            
        with self.prefetch_lock:
            if index in self.page_cache:
                return # Already cached or actively caching
            self.page_cache[index] = None # Mark as caching
            
        try:
            image, ocr_data = self.processor.get_page_preview(index)
            
            with self.prefetch_lock:
                self.page_cache[index] = (image, ocr_data)
                
                # Cleanup old caches to save memory
                keys_to_delete = [k for k in self.page_cache.keys() if k < index - 1 or k > index + 2]
                for k in keys_to_delete:
                    del self.page_cache[k]
                    
            app_logger.debug(f"Successfully prefetched page {index+1}")
        except Exception as e:
            app_logger.error(f"Prefetch Error on page {index}: {e}")
            with self.prefetch_lock:
                if index in self.page_cache:
                    del self.page_cache[index] # Clear failed lock

    def _update_gui_after_thread(self, ocr_data):
        self._redraw_canvas()

        # Fill inputs
        self.entry_initial.insert(0, ocr_data.get("initial", ""))
        self.entry_lastname.insert(0, ocr_data.get("last_name", ""))
        self.entry_date.insert(0, ocr_data.get("date", ""))
        
        lt = ocr_data.get("leave_type", "")
        if lt:
            self.entry_leavetype.set(lt)

        self.status_var.set("Ready. Edit if needed and Confirm (Ctrl+S).")

    # === Canvas Drawing and Zoom Logic ===
    def _redraw_canvas(self, x=None, y=None):
        if not self.base_image:
            return
            
        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()
        
        if c_width < 10:
            c_width = 700
        if c_height < 10:
            c_height = 800

        # Calculate base fit
        w, h = self.base_image.size
        ratio = min(c_width / w, c_height / h) * self.zoom_factor
        new_size = (int(w * ratio), int(h * ratio))
        
        resized = self.base_image.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized)
        
        self.canvas.delete("all")
        
        # Center image if smaller than canvas, otherwise place at 0,0 for panning
        draw_x = c_width//2 if new_size[0] < c_width else new_size[0]//2
        draw_y = c_height//2 if new_size[1] < c_height else new_size[1]//2
        
        self.canvas.create_image(draw_x, draw_y, image=self.tk_image, anchor="center")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _on_zoom(self, event):
        if not self.base_image:
            return
        # Linux uses Button-4 (up) and Button-5 (down)
        # Windows uses event.delta
        if event.num == 4 or getattr(event, 'delta', 0) > 0:
            self.zoom_factor *= 1.2
        elif event.num == 5 or getattr(event, 'delta', 0) < 0:
            self.zoom_factor /= 1.2
            
        self.zoom_factor = max(0.2, min(self.zoom_factor, 5.0)) # Clamp zoom
        self._redraw_canvas()

    def _on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_pan_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    # === Actions ===
    def save_current_page(self):
        if not self.processor.reader:
            return

        initial = self.entry_initial.get()
        last_name = self.entry_lastname.get()
        leave_type = self.entry_leavetype.get()
        date_str = self.entry_date.get()

        if not last_name:
            if not messagebox.askyesno("Warning", "Last Name is empty. Save anyway as UNKNOWN?"):
                return

        try:
            self.processor.save_page(self.current_page_index, initial, last_name, leave_type, date_str)
            self.status_var.set(f"Saved page {self.current_page_index + 1}")
            app_logger.info(f"Successfully saved page {self.current_page_index + 1}")
            self._load_page(self.current_page_index + 1)
        except Exception as e:
            app_logger.error(f"Failed to save page {self.current_page_index + 1}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save: {e}")

    def skip_page(self):
        if self.processor.reader:
            self._load_page(self.current_page_index + 1)

    def load_previous_page(self):
        if self.processor.reader and self.current_page_index > 0:
            self._load_page(self.current_page_index - 1)

    def jump_to_page(self):
        if not self.processor.reader:
            return
        try:
            val = int(self.entry_jump.get()) - 1
            if 0 <= val < self.total_pages:
                self._load_page(val)
            else:
                messagebox.showwarning("Invalid", f"Enter a number between 1 and {self.total_pages}")
        except ValueError:
            messagebox.showwarning("Invalid", "Please enter a valid number")
