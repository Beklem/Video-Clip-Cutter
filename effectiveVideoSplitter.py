import tkinter as tk
from tkinter import filedialog, ttk
import os
from threading import Thread

# PySceneDetect imports. Ensure you have run: pip install scenedetect[opencv]
#uses ml from PySceneDetect in opencv - it's pretty cool but my main weird focus here is looking at nightclub scenes, and how to reduce the flashing light effect i guess in video splitting
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

class VideoClipTrimmerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Splitter (PySceneDetect Engine)")
        self.root.geometry("450x450")

        # --- UI Setup ---
        style = ttk.Style()
        style.theme_use('clam')
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- File Selection ---
        file_select_frame = ttk.LabelFrame(main_frame, text="1. Select Video & Output Folder")
        file_select_frame.pack(fill=tk.X, padx=5, pady=5)

        video_row_frame = ttk.Frame(file_select_frame)
        video_row_frame.pack(fill=tk.X, padx=5, pady=5)
        self.video_path = tk.StringVar()
        self.video_entry = ttk.Entry(video_row_frame, textvariable=self.video_path, width=40)
        self.video_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.video_button = ttk.Button(video_row_frame, text="Browse Video...", command=self.select_video_file)
        self.video_button.pack(side=tk.RIGHT, padx=5)

        folder_row_frame = ttk.Frame(file_select_frame)
        folder_row_frame.pack(fill=tk.X, padx=5, pady=5)
        self.folder_path = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_row_frame, textvariable=self.folder_path, width=40)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.folder_button = ttk.Button(folder_row_frame, text="Browse Folder...", command=self.select_folder)
        self.folder_button.pack(side=tk.RIGHT, padx=5)

        # --- FFmpeg Path Selection ---
        ffmpeg_frame = ttk.LabelFrame(main_frame, text="2. Set FFmpeg Path (if needed)")
        ffmpeg_frame.pack(fill=tk.X, padx=5, pady=5)
        self.ffmpeg_path = tk.StringVar()
        self.ffmpeg_entry = ttk.Entry(ffmpeg_frame, textvariable=self.ffmpeg_path, width=40)
        self.ffmpeg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.ffmpeg_button = ttk.Button(ffmpeg_frame, text="Find ffmpeg.exe", command=self.select_ffmpeg_path)
        self.ffmpeg_button.pack(side=tk.RIGHT, padx=5)


        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(main_frame, text="3. Adjust Detection Threshold")
        settings_frame.pack(fill=tk.X, padx=5, pady=10)

        self.threshold_label = ttk.Label(settings_frame, text="Threshold (Lower = More Sensitive, Default: 27)")
        self.threshold_label.pack(pady=5, anchor=tk.W)
        self.threshold_scale = ttk.Scale(settings_frame, from_=10, to=50, orient=tk.HORIZONTAL)
        self.threshold_scale.set(27) # Default threshold for ContentDetector
        self.threshold_scale.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # --- Control and Progress ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=10)
        self.start_button = ttk.Button(control_frame, text="Start Splitting", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.exit_button = ttk.Button(control_frame, text="Exit", command=root.quit)
        self.exit_button.pack(side=tk.RIGHT, padx=5)
        
        self.status_label = ttk.Label(main_frame, text="Status: Idle")
        self.status_label.pack(pady=5)
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=10, fill=tk.X, expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder: self.folder_path.set(folder)

    def select_video_file(self):
        file_path = filedialog.askopenfilename(title="Select a Video File", filetypes=[("Video files", "*.mp4;*.avi;*.mov"), ("All files", "*.*")])
        if file_path: self.video_path.set(file_path)

    def select_ffmpeg_path(self):
        file_path = filedialog.askopenfilename(title="Select ffmpeg.exe", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if file_path: self.ffmpeg_path.set(file_path)

    def start_processing(self):
        video_path = self.video_path.get()
        output_folder = self.folder_path.get()
        ffmpeg_path = self.ffmpeg_path.get()

        if not all([video_path, os.path.exists(video_path), output_folder]):
            self.update_status("Error: Please select valid video and folder paths.", "red")
            return
        
        if ffmpeg_path and not os.path.exists(ffmpeg_path):
            self.update_status("Error: Provided FFmpeg path is not valid.", "red")
            return

        self.start_button.config(state=tk.DISABLED)
        settings = {
            "video_path": video_path,
            "output_folder": output_folder,
            "threshold": self.threshold_scale.get(),
            "ffmpeg_path": ffmpeg_path if ffmpeg_path else None
        }
        Thread(target=self.process_video, args=(settings,), daemon=True).start()

    def update_status(self, message, color="black"):
        self.status_label.config(text=f"Status: {message}", foreground=color)
        self.root.update_idletasks()

    def process_video(self, settings):
        """Processes the video using PySceneDetect."""
        try:
            video_path = settings['video_path']
            output_folder = settings['output_folder']
            threshold = settings['threshold']
            ffmpeg_path = settings['ffmpeg_path']

            # --- FIX: Temporarily modify the PATH environment variable ---
            # This ensures that the subprocess call inside PySceneDetect can find ffmpeg.
            original_path = os.environ['PATH']
            if ffmpeg_path:
                ffmpeg_dir = os.path.dirname(ffmpeg_path)
                os.environ['PATH'] = f"{ffmpeg_dir}{os.pathsep}{original_path}"

            self.update_status("Opening video...", "blue")
            video = open_video(video_path)
            
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold))

            self.update_status("Detecting scenes...", "blue")
            scene_manager.detect_scenes(video=video, show_progress=True)

            scene_list = scene_manager.get_scene_list()
            
            self.update_status(f"Found {len(scene_list)} scenes. Splitting video...", "orange")
            
            if not scene_list:
                self.update_status("No scenes detected. Nothing to split.", "orange")
                self.start_button.config(state=tk.NORMAL)
                return

            # Call the splitter without the incorrect keyword argument.
            # It will now find ffmpeg via the modified PATH.
            split_video_ffmpeg(video_path, scene_list, output_dir=output_folder,
                               show_progress=True)

            self.update_status(f"Success! Video split into {len(scene_list)} clips.", "green")

        except Exception as e:
            self.update_status(f"An error occurred: {e}", "red")
        finally:
            # Restore the original PATH and re-enable the button
            os.environ['PATH'] = original_path
            self.start_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoClipTrimmerApp(root)
    root.mainloop()
