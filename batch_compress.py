#!/usr/bin/env python3
"""
Batch Video Compressor

A simple GUI for batch compressing multiple video files.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import threading
import queue

class BatchCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Video Compressor")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        
        self.input_files = []
        self.output_dir = ""
        self.process_queue = queue.Queue()
        self.is_processing = False
        
        self.create_widgets()
        self.create_layout()
        
    def create_widgets(self):
        # Input files frame
        self.input_frame = ttk.LabelFrame(self.root, text="Input Videos")
        
        # Input files list
        self.files_listbox = tk.Listbox(self.input_frame, selectmode=tk.EXTENDED, height=10)
        self.files_scrollbar = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=self.files_scrollbar.set)
        
        # Input buttons
        self.input_buttons_frame = ttk.Frame(self.input_frame)
        self.add_files_button = ttk.Button(self.input_buttons_frame, text="Add Files", command=self.add_files)
        self.add_folder_button = ttk.Button(self.input_buttons_frame, text="Add Folder", command=self.add_folder)
        self.remove_button = ttk.Button(self.input_buttons_frame, text="Remove Selected", command=self.remove_files)
        self.clear_button = ttk.Button(self.input_buttons_frame, text="Clear All", command=self.clear_files)
        
        # Output directory frame
        self.output_frame = ttk.LabelFrame(self.root, text="Output Directory")
        
        # Output directory entry
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(self.output_frame, textvariable=self.output_var, width=50)
        self.browse_button = ttk.Button(self.output_frame, text="Browse...", command=self.browse_output)
        
        # Compression settings frame
        self.settings_frame = ttk.LabelFrame(self.root, text="Compression Settings")
        
        # Target size
        self.size_label = ttk.Label(self.settings_frame, text="Target Size (MB):")
        self.size_var = tk.IntVar(value=30)
        self.size_entry = ttk.Spinbox(self.settings_frame, from_=5, to=100, textvariable=self.size_var, width=5)
        
        # Codec
        self.codec_label = ttk.Label(self.settings_frame, text="Codec:")
        self.codec_var = tk.StringVar(value="libx265")
        self.codec_combo = ttk.Combobox(self.settings_frame, textvariable=self.codec_var, width=10)
        self.codec_combo['values'] = ("libx264", "libx265", "vp9")
        self.codec_combo['state'] = 'readonly'
        
        # CRF
        self.crf_label = ttk.Label(self.settings_frame, text="Quality (CRF):")
        self.crf_var = tk.IntVar(value=28)
        self.crf_entry = ttk.Spinbox(self.settings_frame, from_=18, to=35, textvariable=self.crf_var, width=5)
        
        # Preset
        self.preset_label = ttk.Label(self.settings_frame, text="Preset:")
        self.preset_var = tk.StringVar(value="medium")
        self.preset_combo = ttk.Combobox(self.settings_frame, textvariable=self.preset_var, width=10)
        self.preset_combo['values'] = ("ultrafast", "superfast", "veryfast", "faster", "fast", 
                                      "medium", "slow", "slower", "veryslow")
        self.preset_combo['state'] = 'readonly'
        
        # Max width
        self.width_label = ttk.Label(self.settings_frame, text="Max Width:")
        self.width_var = tk.StringVar(value="")
        self.width_entry = ttk.Combobox(self.settings_frame, textvariable=self.width_var, width=10)
        self.width_entry['values'] = ("", "1920", "1280", "854", "640")
        
        # Parallel jobs
        self.jobs_label = ttk.Label(self.settings_frame, text="Parallel Jobs:")
        self.jobs_var = tk.IntVar(value=1)
        self.jobs_entry = ttk.Spinbox(self.settings_frame, from_=1, to=8, textvariable=self.jobs_var, width=5)
        
        # Progress frame
        self.progress_frame = ttk.LabelFrame(self.root, text="Progress")
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.progress_frame, textvariable=self.status_var)
        
        # Log
        self.log_frame = ttk.LabelFrame(self.root, text="Log")
        self.log_text = tk.Text(self.log_frame, height=10, width=80, wrap=tk.WORD)
        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)
        self.log_text.configure(state=tk.DISABLED)
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.root)
        self.start_button = ttk.Button(self.buttons_frame, text="Start Compression", command=self.start_compression)
        self.stop_button = ttk.Button(self.buttons_frame, text="Stop", command=self.stop_compression, state=tk.DISABLED)
        
    def create_layout(self):
        # Input files frame
        self.input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        self.input_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        self.add_files_button.pack(side=tk.LEFT, padx=5)
        self.add_folder_button.pack(side=tk.LEFT, padx=5)
        self.remove_button.pack(side=tk.LEFT, padx=5)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Output directory frame
        self.output_frame.pack(fill=tk.X, padx=10, pady=5)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.browse_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Compression settings frame
        self.settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a grid for settings
        self.size_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.size_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.codec_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.codec_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        self.crf_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.crf_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.preset_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.preset_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        self.width_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.width_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.jobs_label.grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        self.jobs_entry.grid(row=2, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Progress frame
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)
        self.status_label.pack(padx=5, pady=2)
        
        # Log frame
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Buttons frame
        self.buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=(
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv"),
                ("All files", "*.*")
            )
        )
        
        if files:
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.files_listbox.insert(tk.END, os.path.basename(file))
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        
        if folder:
            video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(video_extensions):
                        full_path = os.path.join(root, file)
                        if full_path not in self.input_files:
                            self.input_files.append(full_path)
                            self.files_listbox.insert(tk.END, file)
    
    def remove_files(self):
        selected = self.files_listbox.curselection()
        
        # Remove in reverse order to avoid index shifting
        for index in sorted(selected, reverse=True):
            del self.input_files[index]
            self.files_listbox.delete(index)
    
    def clear_files(self):
        self.input_files = []
        self.files_listbox.delete(0, tk.END)
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        
        if folder:
            self.output_var.set(folder)
            self.output_dir = folder
    
    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def start_compression(self):
        if not self.input_files:
            messagebox.showerror("Error", "No input files selected.")
            return
        
        if not self.output_var.get():
            messagebox.showerror("Error", "No output directory selected.")
            return
        
        # Check if FFmpeg is installed
        try:
            subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            messagebox.showerror("Error", "FFmpeg is not installed or not in PATH. Please install FFmpeg first.")
            return
        
        # Prepare output directory
        output_dir = self.output_var.get()
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare command arguments
        cmd_args = []
        
        # Add input files
        cmd_args.extend(self.input_files)
        
        # Add output directory
        cmd_args.extend(["-o", output_dir])
        
        # Add compression settings
        cmd_args.extend(["-s", str(self.size_var.get())])
        cmd_args.extend(["-c", self.codec_var.get()])
        cmd_args.extend(["--crf", str(self.crf_var.get())])
        cmd_args.extend(["-p", self.preset_var.get()])
        
        # Add max width if specified
        if self.width_var.get():
            cmd_args.extend(["-w", self.width_var.get()])
        
        # Add parallel jobs
        cmd_args.extend(["-j", str(self.jobs_var.get())])
        
        # Update UI
        self.status_var.set("Compressing...")
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        self.is_processing = True
        
        # Clear log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Log command
        self.log(f"Starting compression with command:")
        self.log(f"python video_compressor.py {' '.join(cmd_args)}")
        self.log("")
        
        # Start processing thread
        threading.Thread(target=self.process_videos, args=(cmd_args,), daemon=True).start()
    
    def process_videos(self, cmd_args):
        try:
            # Run the video_compressor.py script
            process = subprocess.Popen(
                ["python", "video_compressor.py"] + cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Track progress
            total_files = len(self.input_files)
            processed_files = 0
            
            # Read output line by line
            for line in iter(process.stdout.readline, ""):
                if not self.is_processing:
                    process.terminate()
                    break
                
                self.log(line.strip())
                
                # Update progress based on output
                if "Compression complete" in line:
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    self.progress_var.set(progress)
                
                # Update status if batch processing is complete
                if "Batch processing complete" in line:
                    success_count = 0
                    if "files processed successfully" in line:
                        parts = line.split()
                        for part in parts:
                            if "/" in part:
                                success_count = int(part.split("/")[0])
                    
                    self.status_var.set(f"Completed: {success_count}/{total_files} files")
            
            if self.is_processing:
                self.status_var.set("Compression completed")
                self.progress_var.set(100)
            else:
                self.status_var.set("Compression stopped")
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.status_var.set("Error occurred")
        
        finally:
            self.is_processing = False
            self.start_button.configure(state=tk.NORMAL)
            self.stop_button.configure(state=tk.DISABLED)
    
    def stop_compression(self):
        if self.is_processing:
            self.is_processing = False
            self.status_var.set("Stopping...")
            self.log("Stopping compression...")


if __name__ == "__main__":
    # Check if video_compressor.py exists
    if not os.path.exists("video_compressor.py"):
        print("Error: video_compressor.py not found in the current directory.")
        print("Please make sure you have the video_compressor.py script in the same directory.")
        sys.exit(1)
    
    root = tk.Tk()
    app = BatchCompressorGUI(root)
    root.mainloop() 