import tkinter as tk
from tkinter import colorchooser, font, ttk
from PIL import ImageGrab, Image, ImageChops
from skimage.metrics import structural_similarity as ssim
from deep_translator import GoogleTranslator, DeeplTranslator, BaiduTranslator
import os
import sys
import re
import easyocr
import numpy as np
import time
import threading
import logging

class OverText:
    def __init__(self, root):
        self.root = root
        self.root.title("OverText")
        
        # Initialize logging
        logging.basicConfig(format='%(asctime)s %(message)s', encoding='utf-8', level=logging.INFO)
        logging.warning('OverText started!')
        
        # Initialize variables
        self.init_variables()

        # Set up main overlay window
        self.setup_main_window()
        
        # Create control panel with tabs
        self.create_control_panel()

        # Initialize OCR reader
        self.initialize_ocr_reader()
        
        # Create tabs window
        self.create_tabs_window()
        
        # Set up resize handlers
        self.setup_resize_handlers()
    
    def init_variables(self):
        """Initialize all variables used by the application"""
        # Window settings
        self.border_width = 1
        self.width = 1020
        self.height = 264
        self.is_maximized = False
        self.pre_maximize_geometry = None
        self.hide_frame = False
        
        # OCR settings
        self.ocr_languages = ['en', 'de']  # Default OCR languages
        self.reader = None  # Initialize to None, will create on first use
        self.text_boxes = []
        self.translation_boxes = []
        self.ocr_text_boxes = []
        
        # Text appearance
        self.text_color = "#FFFFFF"
        self.text_font_family = "Arial"
        self.text_font_size = 9
        self.text_font_weight = "bold"

        # Text rendering settings
        self.use_fixed_font_size = True
        self.use_advanced_rendering = False # unused
        self.text_shrink_factor = 0.9 # unused
        self.splitting_method = "Smart" # unused

        # Capture settings
        self.save_screenshot = False
        self.change_threshold = 0.30
        self.comparison_method = "PIL"
        
        # Auto-update settings
        self.auto_update = False
        self.update_interval = 1.0
        self.update_thread = None
        self.stop_update_thread = threading.Event()
        self.last_screenshot = None
        self.last_text_hash = None
        
        # UI state
        self.show_tabs_var = tk.BooleanVar(value=False)
        self.resizing = False
        self.resize_edge = None

    def initialize_ocr_reader(self):
        """Initialize or update the OCR reader with current language settings"""
        source_lang = self.source_lang.get().lower().split('-')[0]
        target_lang = self.target_lang.get().lower().split('-')[0]
        
        # Build language list for OCR
        languages = []
        
        # Add source language if it's not 'auto'
        if source_lang != 'auto' and source_lang not in languages:
            languages.append(source_lang)
        else:
            # If source is auto, include English as a fallback
            if 'en' not in languages:
                languages.append('en')
        
        # Add target language if not already included
        if target_lang not in languages:
            languages.append(target_lang)
        
        # Check if we need to reinitialize the reader
        current_langs = set(self.ocr_languages)
        new_langs = set(languages)
        
        if current_langs != new_langs or self.reader is None:
            logging.info(f"Initializing OCR reader with languages: {languages}")
            try:
                self.reader = easyocr.Reader(languages)
                self.ocr_languages = languages
            except Exception as e:
                logging.error(f"Error initializing OCR reader: {e}")
                # Fallback to English if there's an error
                if self.reader is None:
                    logging.info("Falling back to English-only OCR")
                    self.reader = easyocr.Reader(['en'])
                    self.ocr_languages = ['en']

    def setup_main_window(self):
        """Set up the main transparent overlay window"""
        # Make window transparent and keep in foreground
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        
        # Set initial geometry
        total_width = self.width + (self.border_width * 2)
        total_height = self.height + (self.border_width * 2)
        self.root.geometry(f"{total_width}x{total_height}+100+100")
        
        # Main outer frame with border
        self.outer_frame = tk.Frame(self.root, bg="#C0C0C0", borderwidth=self.border_width)
        self.outer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Main content frame
        self.main_frame = tk.Frame(self.outer_frame, bg="#F0F0F0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Inner frame for content
        self.frame = tk.Frame(self.main_frame, bg="#FFFFFF")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for displaying translations
        self.canvas = tk.Canvas(self.frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Make window draggable
        self.frame.bind("<ButtonPress-1>", self.start_drag)
        self.frame.bind("<B1-Motion>", self.on_drag)
    
    def create_control_panel(self):
        """Create the tabbed control panel for all settings"""
        self.control_panel = tk.Toplevel(self.root)
        self.control_panel.title("Controls")
        self.control_panel.attributes("-topmost", True)
        self.control_panel.geometry("320x500+10+10")
        
        # Create notebook for tabs
        self.control_tabs = ttk.Notebook(self.control_panel)
        self.control_tabs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.window_tab = ttk.Frame(self.control_tabs)
        self.appearance_tab = ttk.Frame(self.control_tabs)
        self.translation_tab = ttk.Frame(self.control_tabs)
        self.capture_tab = ttk.Frame(self.control_tabs)
        
        # Add tabs to notebook
        self.control_tabs.add(self.window_tab, text="Window")
        self.control_tabs.add(self.appearance_tab, text="Appearance")
        self.control_tabs.add(self.translation_tab, text="Translation")
        self.control_tabs.add(self.capture_tab, text="Capture")
        
        # Set up tab contents
        self.setup_window_tab()
        self.setup_appearance_tab()
        self.setup_translation_tab()
        self.setup_capture_tab()
        
        # Add action buttons at the bottom of the control panel
        self.setup_action_buttons()
        
        # Close main window when control panel is closed
        self.control_panel.protocol("WM_DELETE_WINDOW", self.quit)
    
    def setup_window_tab(self):
        """Set up window settings tab"""
        frame = self.window_tab
        row = 0
        
        # Window size controls
        tk.Label(frame, text="Width:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.width_entry = tk.Entry(frame, width=10)
        self.width_entry.insert(0, str(self.width))
        self.width_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        tk.Label(frame, text="Height:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.height_entry = tk.Entry(frame, width=10)
        self.height_entry.insert(0, str(self.height))
        self.height_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        # Apply size button
        self.apply_btn = tk.Button(frame, text="Apply Size", command=self.apply_size)
        self.apply_btn.grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # Window transparency
        tk.Label(frame, text="Window Transparency:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        row += 1
        self.transparency_slider = tk.Scale(frame, from_=0.05, to=1.0, resolution=0.05,
                                         orient=tk.HORIZONTAL, command=self.update_transparency)
        self.transparency_slider.set(0.3)
        self.transparency_slider.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1
        
        # Hide window frame option
        self.hide_frame_var = tk.BooleanVar(value=self.hide_frame)
        self.hide_frame_check = tk.Checkbutton(frame, text="Hide Window Frame", 
                                             variable=self.hide_frame_var,
                                             command=self.toggle_window_frame)
        self.hide_frame_check.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1
        
        # Show tabs window option
        self.show_tabs_check = tk.Checkbutton(frame, text="Show Tabs Window", 
                                            variable=self.show_tabs_var,
                                            command=self.toggle_tabs_window)
        self.show_tabs_check.grid(row=row, column=0, columnspan=2, pady=5, sticky="w")
    
    def setup_appearance_tab(self):
        """Set up appearance settings tab with additional options"""
        frame = self.appearance_tab
        row = 0
        
        # Text color
        tk.Label(frame, text="Text Color:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.color_btn = tk.Button(frame, text="Choose Color", command=self.choose_color, 
                                  bg=self.text_color)
        self.color_btn.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1
        
        # Font selection
        tk.Label(frame, text="Font:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        available_fonts = sorted(font.families())
        self.font_var = tk.StringVar(value=self.text_font_family)
        self.font_dropdown = ttk.Combobox(frame, textvariable=self.font_var, values=available_fonts)
        self.font_dropdown.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.font_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_font())
        row += 1
        
        # Font size
        tk.Label(frame, text="Font Size:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.font_size_var = tk.IntVar(value=self.text_font_size)
        self.font_size = tk.Scale(frame, from_=8, to=24, variable=self.font_size_var,
                                 orient=tk.HORIZONTAL, command=lambda x: self.update_font())
        self.font_size.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1
        
        # Bold checkbox
        self.bold_var = tk.BooleanVar(value=True)
        self.bold_check = tk.Checkbutton(frame, text="Bold Text", 
                                        variable=self.bold_var, command=self.update_font)
        self.bold_check.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1
        
        # Add separator
        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # Option to use fixed font size vs. auto-detected
        self.use_fixed_font_size = tk.BooleanVar(value=True)
        self.fixed_font_check = tk.Checkbutton(frame, text="Use Fixed Font Size", 
                                             variable=self.use_fixed_font_size)
        self.fixed_font_check.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1
        
        # NEW OPTIONS FOR TEXT RENDERING
        """
        # Option for advanced text rendering (character spacing)
        self.use_advanced_rendering = tk.BooleanVar(value=False)
        self.advanced_rendering_check = tk.Checkbutton(frame, text="Advanced Text Rendering", 
                                                     variable=self.use_advanced_rendering)
        self.advanced_rendering_check.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1
        
        # Text shrink factor when too long
        tk.Label(frame, text="Text Shrink Factor:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.shrink_slider = tk.Scale(frame, from_=0.6, to=1.0, resolution=0.05,
                                     orient=tk.HORIZONTAL)
        self.shrink_slider.set(0.9)  # Default shrink to 90%
        self.shrink_slider.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1
        
        # Smart splitting method selection
        tk.Label(frame, text="Text Splitting Method:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.splitting_var = tk.StringVar(value="Smart")
        self.splitting_dropdown = ttk.Combobox(frame, textvariable=self.splitting_var,
                                             values=["Smart", "Word Count", "Character Count", "Sentence"], 
                                             state="readonly")
        self.splitting_dropdown.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        """

    def setup_translation_tab(self):
        """Set up translation settings tab"""
        frame = self.translation_tab
        row = 0
        
        # Source and target languages
        tk.Label(frame, text="Source Language:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.source_lang = tk.Entry(frame, width=10)
        self.source_lang.insert(0, "auto")
        self.source_lang.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        tk.Label(frame, text="Target Language:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.target_lang = tk.Entry(frame, width=10)
        self.target_lang.insert(0, "de")
        self.target_lang.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        # OCR language refresh button
        self.ocr_refresh_btn = tk.Button(
            frame, 
            text="Update OCR Languages",
            command=self.initialize_ocr_reader
        )
        self.ocr_refresh_btn.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1

        # Translation service selection
        tk.Label(frame, text="Translation Service:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.translation_service = tk.StringVar(value="Google")
        self.service_dropdown = ttk.Combobox(frame, textvariable=self.translation_service,
                                            values=["Google", "DeepL", "Baidu"], state="readonly")
        self.service_dropdown.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        row += 1
        
        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # API Keys (shown/hidden based on selected service)
        tk.Label(frame, text="DeepL API Key:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.deepl_key = tk.Entry(frame, width=20)
        self.deepl_key.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        tk.Label(frame, text="Baidu App ID:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.baidu_app_id = tk.Entry(frame, width=20)
        self.baidu_app_id.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        tk.Label(frame, text="Baidu API Key:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.baidu_api_key = tk.Entry(frame, width=20)
        self.baidu_api_key.grid(row=row, column=1, padx=5, pady=5)
        
        # Language information button
        self.lang_info_btn = tk.Button(
            self.translation_tab, 
            text="Language Info", 
            command=self.show_language_info
        )
        self.lang_info_btn.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def setup_capture_tab(self):
        """Set up capture settings tab"""
        frame = self.capture_tab
        row = 0
        
        # Save screenshot option
        self.save_screenshot_var = tk.BooleanVar(value=self.save_screenshot)
        self.save_screenshot_check = tk.Checkbutton(frame, text="Save Screenshot", 
                                                  variable=self.save_screenshot_var,
                                                  command=lambda: setattr(self, 'save_screenshot', self.save_screenshot_var.get()))
        self.save_screenshot_check.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        row += 1
        
        # Auto update settings
        self.auto_update_var = tk.BooleanVar(value=self.auto_update)
        self.auto_update_check = tk.Checkbutton(frame, text="Auto Update", 
                                              variable=self.auto_update_var,
                                              command=self.toggle_auto_update)
        self.auto_update_check.grid(row=row, column=0, columnspan=2, pady=5, sticky="w")
        row += 1
        
        # Update interval
        tk.Label(frame, text="Update Interval (sec):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        row += 1
        self.interval_slider = tk.Scale(frame, from_=0.5, to=10.0, resolution=0.5,
                                      orient=tk.HORIZONTAL, command=self.update_interval_time)
        self.interval_slider.set(self.update_interval)
        self.interval_slider.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1
        
        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # Change detection settings
        tk.Label(frame, text="Change Threshold (%):").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        row += 1
        self.threshold_slider = tk.Scale(frame, from_=1, to=100, resolution=1,
                                       orient=tk.HORIZONTAL, command=self.update_threshold)
        self.threshold_slider.set(self.change_threshold * 100)
        self.threshold_slider.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1
        
        # Comparison method
        tk.Label(frame, text="Comparison Method:").grid(row=row, column=0, sticky="w", padx=5, pady=5)
        self.comparison_var = tk.StringVar(value=self.comparison_method)
        self.comparison_dropdown = ttk.Combobox(frame, textvariable=self.comparison_var,
                                               values=["PIL", "SSIM", "Histogram"], state="readonly")
        self.comparison_dropdown.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.comparison_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_comparison_method())
    
    def setup_action_buttons(self):
        """Set up action buttons at the bottom of the control panel"""
        button_frame = ttk.Frame(self.control_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Create action buttons
        self.capture_btn = tk.Button(button_frame, text="Capture & Translate", command=self.capture_and_translate)
        self.capture_btn.pack(fill=tk.X, pady=2)
        
        self.clear_btn = tk.Button(button_frame, text="Clear Translations", command=self.clear_translations)
        self.clear_btn.pack(fill=tk.X, pady=2)
        
        self.quit_btn = tk.Button(button_frame, text="Quit", command=self.quit)
        self.quit_btn.pack(fill=tk.X, pady=2)
    
    def create_tabs_window(self):
        """Create a separate window for tabs display"""
        self.tabs_window = tk.Toplevel(self.root)
        self.tabs_window.title("Text Viewer")
        self.tabs_window.geometry(f"{self.width}x{self.height}+400+100")
        self.tabs_window.attributes("-topmost", True)
        
        # Tab control for switching between views
        self.tab_control = ttk.Notebook(self.tabs_window)
        
        # Tab for translated text
        self.translate_tab = tk.Frame(self.tab_control, bg="black")
        self.tab_control.add(self.translate_tab, text="Translated")
        
        # Tab for OCR text
        self.ocr_tab = tk.Frame(self.tab_control, bg="black")
        self.tab_control.add(self.ocr_tab, text="OCR Text")
        
        # Pack the tab control
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for displaying translated text in tabs window
        self.tab_canvas = tk.Canvas(self.translate_tab, bg="black", highlightthickness=0)
        self.tab_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for displaying original OCR text in tabs window
        self.ocr_canvas = tk.Canvas(self.ocr_tab, bg="black", highlightthickness=0)
        self.ocr_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Hide the window initially
        self.tabs_window.withdraw()
        
        # Close main window when tabs window is closed
        self.tabs_window.protocol("WM_DELETE_WINDOW", lambda: self.show_tabs_var.set(False))
    
    def setup_resize_handlers(self):
        """Set up mouse event bindings for resizing window"""
        # Bind motion events to detect when cursor is near edges
        self.outer_frame.bind("<Motion>", self.detect_edge)
        
        # Bind mouse events for resizing
        self.outer_frame.bind("<ButtonPress-1>", self.start_resize_or_drag)
        self.outer_frame.bind("<B1-Motion>", self.on_resize_or_drag)
        self.outer_frame.bind("<ButtonRelease-1>", self.stop_resize)
    
    def toggle_auto_update(self):
        """Toggle the auto update feature"""
        self.auto_update = self.auto_update_var.get()
        
        if self.auto_update:
            # Start the auto-update thread if it's not already running
            if self.update_thread is None or not self.update_thread.is_alive():
                self.stop_update_thread.clear()
                self.update_thread = threading.Thread(target=self.auto_update_thread)
                self.update_thread.daemon = True
                self.update_thread.start()
        else:
            # Stop the auto-update thread if it's running
            if self.update_thread and self.update_thread.is_alive():
                self.stop_update_thread.set()
    
    def update_interval_time(self, value):
        """Update the auto-update interval time"""
        try:
            self.update_interval = float(value)
        except ValueError:
            pass
    
    def auto_update_thread(self):
        """Thread function for auto-updating based on changes to the screen content"""
        while not self.stop_update_thread.is_set():
            if self.auto_update:
                # Capture the current screenshot
                current_screenshot = self.capture_screenshot()
                
                # Check if the screenshot or text content has changed
                if self.has_content_changed(current_screenshot):
                    # Update the last screenshot
                    self.last_screenshot = current_screenshot
                    
                    # Process the screenshot
                    self.process_screenshot(current_screenshot)
            
            # Wait for the specified interval before the next check
            time.sleep(self.update_interval)
    
    def capture_screenshot(self):
        """Capture a screenshot of the overlay area"""
        # Make window invisible temporarily
        self.root.attributes("-alpha", 0.0)
        self.root.update()
        
        # Get window coordinates
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        
        # Calculate offset based on window mode
        offset_x = self.border_width if not self.hide_frame else 0
        offset_y = self.border_width if not self.hide_frame else 0
        
        x = root_x + offset_x
        y = root_y + offset_y
        
        # Take screenshot of the area inside the frame
        screenshot = ImageGrab.grab(bbox=(x, y, x + self.width, y + self.height))
        
        # Make window visible again with proper transparency
        self.root.attributes("-alpha", float(self.transparency_slider.get()))
        
        return screenshot
    
    def has_content_changed(self, current_screenshot):
        """Check if the screenshot content has changed beyond the threshold"""
        if self.last_screenshot is None:
            return True
        
        comparison_method = self.comparison_method
        
        if comparison_method == "PIL":
            # PIL difference method
            diff_stats = ImageChops.difference(current_screenshot, self.last_screenshot).convert('L').point(lambda x: 255 if x > 0 else 0).getdata()
            changed_pixels = sum(1 for pixel in diff_stats if pixel > 0)
            total_pixels = current_screenshot.width * current_screenshot.height
            change_ratio = changed_pixels / total_pixels if total_pixels > 0 else 0
            
            return change_ratio > self.change_threshold
        
        elif comparison_method == "SSIM":
            # Structural Similarity Index method
            current_array = np.array(current_screenshot.convert('L'))
            last_array = np.array(self.last_screenshot.convert('L'))
            
            score = ssim(current_array, last_array, full=False)
            change_measure = 1 - ((score + 1) / 2)
            
            return change_measure > self.change_threshold
        
        elif comparison_method == "Histogram":
            # Histogram comparison method
            current_hist = current_screenshot.convert('L').histogram()
            last_hist = self.last_screenshot.convert('L').histogram()
            
            hist_diff = sum(abs(c - l) for c, l in zip(current_hist, last_hist))
            max_diff = sum(max(c, l) for c, l in zip(current_hist, last_hist))
            hist_change_ratio = hist_diff / max_diff if max_diff > 0 else 0
            
            return hist_change_ratio > self.change_threshold
        
        # Fallback to text-based comparison
        current_text_blocks = self.extract_text_with_positions(current_screenshot)
        current_text_hash = self.generate_text_hash(current_text_blocks)
        
        if self.last_text_hash is not None and current_text_hash == self.last_text_hash:
            return False
        
        self.last_text_hash = current_text_hash
        return True
    
    def generate_text_hash(self, text_blocks):
        """Generate a hash from text blocks for comparison"""
        text_str = ""
        for block in text_blocks:
            text_str += f"{block['text']}_{block['x']}_{block['y']}|"
        
        return hash(text_str)

    def scale_text_to_fit(self, canvas_id, text, max_width, max_height, font_family, initial_font_size):
        """Scale text to fit within the given boundaries"""
        font_size = initial_font_size
        
        # Create text with initial font size
        text_font = (font_family, font_size, "bold" if self.bold_var.get() else "normal")
        self.canvas.itemconfig(canvas_id, font=text_font)
        
        # Get text bounding box
        bbox = self.canvas.bbox(canvas_id)
        if not bbox:
            return font_size
        
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Reduce font size until text fits
        while (text_width > max_width or text_height > max_height) and font_size > 6:
            font_size -= 1
            text_font = (font_family, font_size, "bold" if self.bold_var.get() else "normal")
            self.canvas.itemconfig(canvas_id, font=text_font)
            
            # Get updated text bounding box
            bbox = self.canvas.bbox(canvas_id)
            if not bbox:
                break
                
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        return font_size

    def estimate_original_font_size(self, img_np, bbox):
        """Estimate the font size of original text using image analysis"""
        # Extract text region
        x, y, width, height = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
        text_region = img_np[y:y+height, x:x+width]
        
        # Count text pixels (assuming dark text on light background or vice versa)
        text_pixels = np.sum(text_region < 128)  # For dark text
        if text_pixels < (width * height * 0.1):  # If too few dark pixels, try light text
            text_pixels = np.sum(text_region > 128)
        
        # Calculate text density
        text_density = text_pixels / (width * height)
        
        # Calculate a rough font size based on height and density
        font_size = int(height * 0.7 * text_density)
        
        # Limit to reasonable range
        return max(8, min(font_size, 36))

    def create_wrapped_text(self, canvas, x, y, text, max_width, font):
        """Create text with intelligent line breaks that respect word boundaries"""
        if not text:
            # Return a dummy text ID if there's no text
            return canvas.create_text(x, y, text="", anchor="nw")
            
        # Check if using Asian language
        is_asian = self.is_asian_language(self.target_lang.get())
        
        # For Asian languages, use different wrapping logic
        if is_asian:
            return self.create_asian_wrapped_text(canvas, x, y, text, max_width, font)
        
        # For non-Asian languages, use word-based wrapping
        words = text.split()
        lines = []
        current_line = []
        
        # Create a temporary window for text measurement (hidden)
        temp = tk.Toplevel()
        temp.withdraw()
        temp_canvas = tk.Canvas(temp)
        
        for word in words:
            # Try adding this word to the current line
            current_line.append(word)
            temp_text = " ".join(current_line)
            
            # Measure the text width
            text_id = temp_canvas.create_text(0, 0, text=temp_text, font=font, anchor="nw")
            bbox = temp_canvas.bbox(text_id)
            
            # If adding this word makes the line too long
            if bbox and (bbox[2] - bbox[0]) > max_width and len(current_line) > 1:
                # Remove the last word as it made the line too long
                current_line.pop()
                # Add the current line to our lines list
                lines.append(" ".join(current_line))
                # Start a new line with the word that didn't fit
                current_line = [word]
        
        # Add the last line if there's anything left
        if current_line:
            lines.append(" ".join(current_line))
        
        # Clean up temporary window
        temp.destroy()
        
        # Create the final text with proper line breaks
        if lines:
            return canvas.create_text(
                x, y, 
                text="\n".join(lines), 
                font=font, 
                anchor="nw", 
                fill=self.text_color
            )
        else:
            # Fallback in case of empty result
            return canvas.create_text(
                x, y, 
                text=text, 
                font=font, 
                anchor="nw", 
                width=max_width,
                fill=self.text_color
            )

    def create_asian_wrapped_text(self, canvas, x, y, text, max_width, font):
        """Create text with character-based wrapping for Asian languages"""
        # For Asian languages we need character-by-character wrapping
        # since words aren't separated by spaces
        chars = list(text)
        lines = []
        current_line = []
        
        # Create a temporary window for text measurement
        temp = tk.Toplevel()
        temp.withdraw()
        temp_canvas = tk.Canvas(temp)
        
        for char in chars:
            # Try adding this character to the current line
            current_line.append(char)
            temp_text = "".join(current_line)
            
            # Measure the text width
            text_id = temp_canvas.create_text(0, 0, text=temp_text, font=font, anchor="nw")
            bbox = temp_canvas.bbox(text_id)
            
            # If adding this character makes the line too long
            if bbox and (bbox[2] - bbox[0]) > max_width and len(current_line) > 1:
                # Remove the last character as it made the line too long
                current_line.pop()
                # Add the current line to our lines list
                lines.append("".join(current_line))
                # Start a new line with the character that didn't fit
                current_line = [char]
        
        # Add the last line if there's anything left
        if current_line:
            lines.append("".join(current_line))
        
        # Clean up temporary window
        temp.destroy()
        
        # Create the final text with proper line breaks
        if lines:
            return canvas.create_text(
                x, y, 
                text="\n".join(lines), 
                font=font, 
                anchor="nw", 
                fill=self.text_color
            )
        else:
            # Fallback in case of empty result
            return canvas.create_text(
                x, y, 
                text=text, 
                font=font, 
                anchor="nw", 
                width=max_width,
                fill=self.text_color
            )

    def show_language_info(self):
        """Show information about language codes and expansion characteristics"""
        info_window = tk.Toplevel(self.control_panel)
        info_window.title("Language Information")
        info_window.geometry("400x300")
        
        # Create a text widget to display information
        text = tk.Text(info_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Insert information about languages
        text.insert(tk.END, "Language Codes and Expansion Information\n\n")
        text.insert(tk.END, "Common Language Codes:\n")
        text.insert(tk.END, "en - English\n")
        text.insert(tk.END, "de - German\n")
        text.insert(tk.END, "fr - French\n")
        text.insert(tk.END, "es - Spanish\n")
        text.insert(tk.END, "it - Italian\n")
        text.insert(tk.END, "zh - Chinese\n")
        text.insert(tk.END, "ja - Japanese\n")
        text.insert(tk.END, "ko - Korean\n\n")
        
        text.insert(tk.END, "Typical Text Expansion:\n")
        text.insert(tk.END, "• English → German: +30% (factor 1.3)\n")
        text.insert(tk.END, "• German → English: -23% (factor 0.77)\n")
        text.insert(tk.END, "• English → French: +15% (factor 1.15)\n")
        text.insert(tk.END, "• French → English: -13% (factor 0.87)\n") 
        text.insert(tk.END, "• English → Spanish: +25% (factor 1.25)\n")
        text.insert(tk.END, "• Spanish → English: -20% (factor 0.8)\n")
        text.insert(tk.END, "• English → Japanese: -40% (factor 0.6)\n")
        text.insert(tk.END, "• Japanese → English: +67% (factor 1.67)\n\n")
        
        text.insert(tk.END, "Asian Languages Note:\n")
        text.insert(tk.END, "• Asian to non-Asian: +80% (factor 1.8)\n")
        text.insert(tk.END, "• Non-Asian to Asian: -40% (factor 0.6)\n")
        
        # Make text widget read-only
        text.config(state=tk.DISABLED)

    def process_screenshot(self, screenshot):
        """Process the screenshot with improved text wrapping and language detection"""
        # Convert PIL Image to numpy array for analysis
        img_np = np.array(screenshot)
        
        # Extract text with positions
        text_blocks = self.extract_text_with_positions(screenshot)
        self.text_boxes = text_blocks
        
        # Only proceed if text is found
        if text_blocks:
            # Clear previous translations
            self.clear_translations()
            
            # Configure canvas backgrounds
            self.canvas.config(bg="black", highlightthickness=0)
            self.tab_canvas.config(bg="black", highlightthickness=0)
            self.ocr_canvas.config(bg="black", highlightthickness=0)
            
            # Background color
            bg_fill = "black"
            
            # Combine all text into one string for translation
            combined_text = " ".join(block["text"] for block in text_blocks if block["text"].strip())
            
            # Translate the combined text
            translated_full_text = self.translate_text(combined_text) if combined_text else ""
            
            # Detect if target language is Asian
            is_asian = self.is_asian_language(self.target_lang.get())
            
            # Split the translated text back into blocks
            translated_blocks = self.split_translated_text(translated_full_text, text_blocks)
            
            # Display each text block
            for i, block in enumerate(text_blocks):
                if block["text"].strip():
                    # Get positions and dimensions
                    x = block["x"]
                    y = block["y"]
                    width = block["width"]
                    height = block["height"]
                    
                    # Get translated text for this block
                    translated_text = translated_blocks[i] if i < len(translated_blocks) else ""
                    original_text = block["text"]
                    
                    # Estimate original font size
                    estimated_font_size = self.estimate_original_font_size(img_np, block)
                    
                    # Adjust font size for Asian languages if needed
                    if is_asian:
                        # Asian languages often need larger font sizes for readability
                        estimated_font_size = int(estimated_font_size * 1.2)
                    
                    # If user has specified a fixed font size, use that instead
                    if self.use_fixed_font_size:
                        font_size = self.text_font_size
                    else:
                        # Use estimated font size with appropriate scaling
                        font_size = max(8, min(int(estimated_font_size * 0.9), 36))
                    
                    # Set the font
                    text_font = (self.text_font_family, font_size, 
                               "bold" if self.bold_var.get() else "normal")
                    
                    # MAIN OVERLAY WINDOW - Background rectangle
                    bg_id = self.canvas.create_rectangle(
                        x, y, x + width, y + height,
                        fill=bg_fill, 
                        outline=""
                    )
                    
                    # Create wrapped text for better line breaks
                    text_id = self.create_wrapped_text(
                        self.canvas, x, y, translated_text, 
                        width, text_font
                    )
                    
                    # Set visibility state
                    self.canvas.itemconfig(text_id, state="hidden" if self.show_tabs_var.get() else "normal")
                    
                    # Store reference to text object
                    self.translation_boxes.append({"bg": bg_id, "text": text_id})
                    
                    # TABS WINDOW - TRANSLATED TAB with wrapped text
                    tab_bg_id = self.tab_canvas.create_rectangle(
                        x, y, x + width, y + height,
                        fill=bg_fill,
                        outline=""
                    )
                    
                    tab_text_id = self.create_wrapped_text(
                        self.tab_canvas, x, y, translated_text, 
                        width, text_font
                    )
                    
                    # TABS WINDOW - OCR TEXT TAB
                    ocr_bg_id = self.ocr_canvas.create_rectangle(
                        x, y, x + width, y + height,
                        fill=bg_fill,
                        outline=""
                    )
                    
                    ocr_text_id = self.create_wrapped_text(
                        self.ocr_canvas, x, y, original_text,
                        width, text_font
                    )
                    
                    self.ocr_text_boxes.append({"bg": ocr_bg_id, "text": ocr_text_id})
            
            # Save screenshot if option is enabled
            if self.save_screenshot_var.get():
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                screenshot_path = os.path.join(desktop, "translated_screenshot.png")
                screenshot.save(screenshot_path)
                print(f"Screenshot saved at: {screenshot_path}")

    def is_asian_language(self, lang_code):
        """Check if language is an Asian character-based language"""
        asian_langs = ['zh', 'ja', 'ko', 'th', 'vi']
        
        # Handle language codes with region specifiers (e.g., zh-CN)
        base_lang = lang_code.lower().strip().split('-')[0]
        
        return base_lang in asian_langs

    def get_language_expansion_factor(self, src_lang, tgt_lang):
        """Get approximate text length expansion factor between languages"""
        # First check if either language is Asian as this affects expansion dramatically
        src_is_asian = self.is_asian_language(src_lang)
        tgt_is_asian = self.is_asian_language(tgt_lang)
        
        # Asian to non-Asian or vice-versa requires special handling
        if src_is_asian and not tgt_is_asian:
            return 1.8  # Asian to non-Asian expands significantly
        elif not src_is_asian and tgt_is_asian:
            return 0.6  # Non-Asian to Asian contracts significantly
        
        # For other language pairs, use the standard mapping
        # Clean language codes
        src = src_lang.lower().strip().split('-')[0]
        if src == 'auto':
            src = 'en'  # Default to English if auto-detect
        
        tgt = tgt_lang.lower().strip().split('-')[0]
        
        # Common language expansion factors (approximate values)
        expansion_factors = {
            ('en', 'de'): 1.3,  # English to German: ~30% longer
            ('de', 'en'): 0.77,  # German to English: ~23% shorter
            ('en', 'fr'): 1.15,  # English to French: ~15% longer
            ('fr', 'en'): 0.87,  # French to English: ~13% shorter
            ('en', 'es'): 1.25,  # English to Spanish: ~25% longer
            ('es', 'en'): 0.8,   # Spanish to English: ~20% shorter
            # Add more common language pairs as needed
        }
        
        # Get the expansion factor or default to 1.0
        return expansion_factors.get((src, tgt), 1.0)

    def split_translated_text(self, translated_text, original_blocks):
        """Split translated text into blocks more accurately matching original blocks"""
        if not translated_text or not original_blocks:
            return []
            
        # Remove blocks with empty text
        valid_blocks = [block for block in original_blocks if block["text"].strip()]
        
        if not valid_blocks:
            return []
        
        # Detect language characteristics
        src_lang = self.source_lang.get()
        tgt_lang = self.target_lang.get()
        
        # Get expansion/contraction factor between languages
        expansion_factor = self.get_language_expansion_factor(src_lang, tgt_lang)
        
        # Split text more intelligently
        result = []
        
        # If we can rely on sentence boundaries in both original and translated
        sentences_original = self.split_into_sentences([block["text"] for block in valid_blocks])
        sentences_translated = self.split_into_sentences([translated_text])
        
        if len(sentences_original) > 0 and len(sentences_translated) > 0:
            # Try aligning sentences if possible
            if len(sentences_original) == len(sentences_translated[0]):
                # Simple 1:1 mapping of sentences
                sentence_idx = 0
                for block in valid_blocks:
                    block_sentences = self.split_into_sentences([block["text"]])
                    block_sentence_count = len(block_sentences)
                    
                    if block_sentence_count > 0:
                        block_translated = " ".join(sentences_translated[0][sentence_idx:sentence_idx+block_sentence_count])
                        result.append(block_translated)
                        sentence_idx += block_sentence_count
                    else:
                        # Fallback for blocks without clear sentences
                        result.append("")
                
                return result
        
        # Fallback to character-count based approach if sentence matching fails
        original_texts = [block["text"] for block in valid_blocks]
        original_char_counts = [len(text) for text in original_texts]
        total_original_chars = sum(original_char_counts)
        
        # Adjust for language expansion/contraction
        translated_chars = len(translated_text)
        
        # Start index for character-based splitting
        start_idx = 0
        
        for i, count in enumerate(original_char_counts):
            if total_original_chars == 0:
                result.append("")
                continue
                
            # Calculate proportion of characters for this block, adjusted for expansion
            proportion = count / total_original_chars
            
            # Calculate end index, considering expansion factor
            adjusted_count = int(proportion * translated_chars)
            end_idx = min(start_idx + adjusted_count, translated_chars)
            
            # Try to find word boundaries for cleaner splits
            if end_idx < translated_chars:
                # Look for space after the calculated position
                space_after = translated_text.find(' ', end_idx)
                # Look for space before the calculated position
                space_before = translated_text.rfind(' ', start_idx, end_idx)
                
                # Use the closest space to make a clean break
                if space_after != -1 and space_before != -1:
                    if (space_after - end_idx) < (end_idx - space_before):
                        end_idx = space_after
                    else:
                        end_idx = space_before
                elif space_after != -1 and (space_after - end_idx) < 10:  # Within 10 chars
                    end_idx = space_after
                elif space_before != -1:
                    end_idx = space_before
            
            # Extract text for this block
            block_text = translated_text[start_idx:end_idx].strip()
            result.append(block_text)
            
            start_idx = end_idx
        
        return result

    def split_into_sentences(self, text_list):
        """Split text into sentences for better alignment"""
        result = []
        for text in text_list:
            # Basic sentence splitting using regex
            sentences = re.split(r'(?<=[.!?])\s+', text)
            # Filter out empty sentences
            sentences = [s.strip() for s in sentences if s.strip()]
            result.append(sentences)
        return result

    def extract_text_with_positions(self, image):
        """Extract text and positions from image using EasyOCR"""
        # Ensure OCR reader is initialized
        if self.reader is None:
            self.initialize_ocr_reader()

        # Convert PIL Image to numpy array for EasyOCR
        img_np = np.array(image)
        
        # Use EasyOCR to get text and positions
        results = self.reader.readtext(img_np)
        
        # Process the results
        text_blocks = []
        
        for (bbox, text, prob) in results:
            if text.strip():  # Skip empty text
                # Extract bounding box coordinates
                top_left = bbox[0]
                top_right = bbox[1]
                bottom_right = bbox[2]
                bottom_left = bbox[3]
                
                # Calculate dimensions
                x = int(top_left[0])
                y = int(top_left[1])
                width = int(top_right[0] - top_left[0])
                height = int(bottom_left[1] - top_left[1])
                
                text_blocks.append({
                    "text": text,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height
                })
        
        return text_blocks
    
    def translate_text(self, text):
        """Translate text using the selected translation service"""
        if not text:
            return ""
            
        try:
            service = self.translation_service.get()
            
            logging.info('%s %s', 'translation_service request: ', service)
            
            if service == "Google":
                translator = GoogleTranslator(source=self.source_lang.get(), target=self.target_lang.get())
                translated = translator.translate(text)
                
            elif service == "DeepL":
                api_key = self.deepl_key.get().strip()
                if api_key:
                    # Using API Key
                    translator = DeeplTranslator(api_key=api_key, 
                                                source=self.source_lang.get(), 
                                                target=self.target_lang.get())
                else:
                    # Using the free version
                    translator = DeeplTranslator(source=self.source_lang.get(), 
                                               target=self.target_lang.get())
                translated = translator.translate(text)
                
            elif service == "Baidu":
                app_id = self.baidu_app_id.get().strip()
                api_key = self.baidu_api_key.get().strip()
                
                if not app_id or not api_key:
                    return "[Error: Baidu requires App ID and API Key]"
                    
                translator = BaiduTranslator(app_id=app_id, 
                                            app_key=api_key,
                                            source=self.source_lang.get(), 
                                            target=self.target_lang.get())
                translated = translator.translate(text)
                
            else:
                return "[Error: Unknown translation service]"
                
            return translated
            
        except Exception as e:
            print(f"Translation error: {e}")
            return f"[Translation Error: {str(e)}]"
    
    def capture_and_translate(self):
        """Capture screenshot, extract text, and display translations"""
        screenshot = self.capture_screenshot()
        self.process_screenshot(screenshot)
    
    def clear_translations(self):
        """Clear all translations and OCR text from the canvases"""
        self.canvas.delete("all")
        self.tab_canvas.delete("all")
        self.ocr_canvas.delete("all")
        self.text_boxes = []
        self.translation_boxes = []
        self.ocr_text_boxes = []
    
    def detect_edge(self, event):
        """Detect if mouse is near an edge and change cursor accordingly"""
        if not self.resizing:
            x, y = event.x, event.y
            frame_width = self.outer_frame.winfo_width()
            frame_height = self.outer_frame.winfo_height()
            
            # Define edge detection threshold
            threshold = 10
            
            # Check if mouse is near edges
            near_left = x < threshold
            near_top = y < threshold
            near_right = x > frame_width - threshold
            near_bottom = y > frame_height - threshold
            
            # Set cursor based on position
            if near_left and near_top:
                self.outer_frame.config(cursor="size_nw_se")  # top-left corner
                self.resize_edge = "topleft"
            elif near_right and near_top:
                self.outer_frame.config(cursor="size_ne_sw")  # top-right corner
                self.resize_edge = "topright"
            elif near_left and near_bottom:
                self.outer_frame.config(cursor="size_ne_sw")  # bottom-left corner
                self.resize_edge = "bottomleft"
            elif near_right and near_bottom:
                self.outer_frame.config(cursor="size_nw_se")  # bottom-right corner
                self.resize_edge = "bottomright"
            elif near_left:
                self.outer_frame.config(cursor="size_we")  # left edge
                self.resize_edge = "left"
            elif near_right:
                self.outer_frame.config(cursor="size_we")  # right edge
                self.resize_edge = "right"
            elif near_top:
                self.outer_frame.config(cursor="size_ns")  # top edge
                self.resize_edge = "top"
            elif near_bottom:
                self.outer_frame.config(cursor="size_ns")  # bottom edge
                self.resize_edge = "bottom"
            else:
                self.outer_frame.config(cursor="")  # default cursor
                self.resize_edge = None
    
    def start_resize_or_drag(self, event):
        """Start resize operation based on cursor position"""
        if self.resize_edge:
            self.resizing = True
            self.start_x = event.x_root
            self.start_y = event.y_root
            self.start_width = self.root.winfo_width()
            self.start_height = self.root.winfo_height()
            self.start_pos_x = self.root.winfo_x()
            self.start_pos_y = self.root.winfo_y()
        else:
            # If not resizing, then we're dragging
            self.start_drag(event)
    
    def on_resize_or_drag(self, event):
        """Handle window resizing based on flag"""
        if self.resizing:
            # Calculate the difference from starting point
            delta_x = event.x_root - self.start_x
            delta_y = event.y_root - self.start_y
            
            # Calculate new dimensions and position based on which edge is being dragged
            new_width = self.start_width
            new_height = self.start_height
            new_x = self.start_pos_x
            new_y = self.start_pos_y
            
            # Apply changes based on which edge is being resized
            if "left" in self.resize_edge:
                new_width = max(200, self.start_width - delta_x)
                new_x = self.start_pos_x + (self.start_width - new_width)
            
            if "right" in self.resize_edge:
                new_width = max(200, self.start_width + delta_x)
            
            if "top" in self.resize_edge:
                new_height = max(200, self.start_height - delta_y)
                new_y = self.start_pos_y + (self.start_height - new_height)
            
            if "bottom" in self.resize_edge:
                new_height = max(200, self.start_height + delta_y)
            
            # Update the window geometry
            self.root.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
            
            # Update the width and height variables to match the new window size
            # This is key for fixing the resize capture issue
            self.width = new_width - (self.border_width * 2)
            self.height = new_height - (self.border_width * 2)
            
            # Update the width/height entries in the control panel
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(self.width))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(self.height))
            
            # Update tabs window size to match
            self.tabs_window.geometry(f"{self.width}x{self.height}")
        else:
            # If not resizing, then we're dragging
            self.on_drag(event)
    
    def stop_resize(self, event):
        """Stop the resize operation and update internal dimensions"""
        self.resizing = False
        
        # Get the current window dimensions
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        
        # Update internal dimensions
        self.width = current_width - (self.border_width * 2)
        self.height = current_height - (self.border_width * 2)
        
        # Update the width/height entries in the control panel
        self.width_entry.delete(0, tk.END)
        self.width_entry.insert(0, str(self.width))
        self.height_entry.delete(0, tk.END)
        self.height_entry.insert(0, str(self.height))
        
        # Update tabs window size to match
        if self.show_tabs_var.get():
            self.tabs_window.geometry(f"{self.width}x{self.height}")
        
        logging.info(f"Window resized: {self.width}x{self.height}")
    
    def start_drag(self, event):
        """Start drag operation for moving the window"""
        self.x = event.x
        self.y = event.y
    
    def on_drag(self, event):
        """Handle window dragging"""
        x_offset = event.x - self.x
        y_offset = event.y - self.y
        x = self.root.winfo_x() + x_offset
        y = self.root.winfo_y() + y_offset
        self.root.geometry(f"+{x}+{y}")
    
    def apply_size(self):
        """Apply size from control panel inputs"""
        try:
            self.width = int(self.width_entry.get())
            self.height = int(self.height_entry.get())
            
            # Account for the border width in the geometry calculation
            total_width = self.width + (self.border_width * 2)
            total_height = self.height + (self.border_width * 2)
            
            self.root.geometry(f"{total_width}x{total_height}")
            
            # Update tabs window size to match
            self.tabs_window.geometry(f"{self.width}x{self.height}")
            
            # If the window was maximized, it's not anymore
            if self.is_maximized:
                self.is_maximized = False
        except ValueError:
            pass
    
    def update_transparency(self, value):
        """Update window transparency from slider"""
        try:
            alpha = float(value)
            self.root.attributes("-alpha", alpha)
        except ValueError:
            pass
    
    def choose_color(self):
        """Open color chooser dialog and update text color"""
        color = colorchooser.askcolor(initialcolor=self.text_color, 
                                     title="Choose Text Color")[1]
        if color:  # If a color was selected (not canceled)
            self.text_color = color
            self.color_btn.config(bg=color)  # Update button color
    
    def update_font(self):
        """Update font settings"""
        self.text_font_family = self.font_var.get()
        self.text_font_size = self.font_size_var.get()
        self.text_font_weight = "bold" if self.bold_var.get() else "normal"
    
    def toggle_window_frame(self):
        """Toggle the window frame on/off"""
        self.hide_frame = self.hide_frame_var.get()
        
        if self.hide_frame:
            # Hide the window frame (borderless window)
            self.root.overrideredirect(True)
            
            # When hiding the frame, adjust the window size
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            self.root.geometry(f"{current_width}x{current_height}+{current_x}+{current_y}")
        else:
            # Show the window frame
            self.root.overrideredirect(False)
            
            # Apply the current size again
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            self.root.geometry(f"{current_width}x{current_height}+{current_x}+{current_y}")
        
        # Update window to reflect changes
        self.root.update()
    
    def toggle_tabs_window(self):
        """Toggle the visibility of the tabs window"""
        if self.show_tabs_var.get():
            self.tabs_window.deiconify()
            # Update tabs window size to match main window
            self.tabs_window.geometry(f"{self.width}x{self.height}")
            # Hide text in main overlay
            self.update_main_overlay_visibility()
        else:
            self.tabs_window.withdraw()
            # Show text in main overlay
            self.update_main_overlay_visibility()
    
    def update_main_overlay_visibility(self):
        """Update the visibility of text in the main overlay based on tabs window visibility"""
        if self.translation_boxes:
            show_text = not self.show_tabs_var.get()
            for box in self.translation_boxes:
                if show_text:
                    # Show text by restoring its original state
                    self.canvas.itemconfig(box["text"], state="normal")
                else:
                    # Hide text by setting state to hidden
                    self.canvas.itemconfig(box["text"], state="hidden")
    
    def update_threshold(self, value):
        """Update the change threshold for image comparison"""
        try:
            # Convert from percentage to decimal (0.0-1.0)
            self.change_threshold = float(value) / 100
        except ValueError:
            pass
    
    def update_comparison_method(self):
        """Update the image comparison method"""
        self.comparison_method = self.comparison_var.get()
    
    def quit(self):
        """Close the application"""
        if hasattr(self, 'tabs_window') and self.tabs_window:
            self.tabs_window.destroy()
        self.control_panel.destroy()
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = OverText(root)
    root.mainloop()
