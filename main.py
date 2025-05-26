import cv2
import tkinter as tk
from tkinter import filedialog, ttk
import os
import numpy as np
from threading import Thread

class VideoClipTrimmerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Clip Trimmer")

        # Threshold scale
        self.threshold_label = tk.Label(root, text="Threshold (Recommended: 0.6):")
        self.threshold_label.pack(pady=5)
        self.threshold_scale = tk.Scale(root, from_=0.1, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
        self.threshold_scale.set(0.6)
        self.threshold_scale.pack(pady=5)

        # Video file selection
        self.video_label = tk.Label(root, text="Video File:")
        self.video_label.pack(pady=5)
        self.video_button = tk.Button(root, text="Select Video File", command=self.select_video_file)
        self.video_button.pack(pady=5)
        self.video_path = tk.StringVar()
        self.video_entry = tk.Entry(root, textvariable=self.video_path, width=50)
        self.video_entry.pack(pady=5)

        # Folder selection
        self.folder_label = tk.Label(root, text="Output Folder:")
        self.folder_label.pack(pady=5)
        self.folder_button = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.folder_button.pack(pady=5)
        self.folder_path = tk.StringVar()
        self.folder_entry = tk.Entry(root, textvariable=self.folder_path, width=50)
        self.folder_entry.pack(pady=5)

        # Start and Exit buttons
        self.start_button = tk.Button(root, text="Start", command=self.start_processing)
        self.start_button.pack(pady=5)
        self.exit_button = tk.Button(root, text="Exit", command=root.quit)
        self.exit_button.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=10)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.folder_path.set(folder)

    def select_video_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video files", "*.mp4;*.avi;*.mov;*.mkv;*.wmv"), ("All files", "*.*")]
        )
        if file_path:
            self.video_path.set(file_path)

    def start_processing(self):
        video_path = self.video_path.get()
        if not video_path:
            print("No video file selected.")
            return

        output_folder = self.folder_path.get()
        if not output_folder:
            print("No output folder selected.")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        threshold = self.threshold_scale.get()
        Thread(target=self.process_video, args=(video_path, output_folder, threshold)).start()

    def process_video(self, video_path, output_folder, threshold):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        clip_count = 0
        prev_hist = None
        out = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray_frame], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if similarity < threshold:
                    if out:
                        out.release()
                    clip_count += 1
                    clip_path = os.path.join(output_folder, f"clip_{clip_count:03d}.mp4")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(clip_path, fourcc, frame_rate, (frame.shape[1], frame.shape[0]))
                    print(f"Started new clip: {clip_path}")

            if out:
                out.write(frame)

            prev_hist = hist
            frame_count += 1

            # Update progress bar
            self.progress['value'] = (frame_count / total_frames) * 100
            self.root.update_idletasks()

        if out:
            out.release()
        cap.release()
        print(f"Video split into {clip_count} clips.")
        self.progress['value'] = 100

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoClipTrimmerApp(root)
    root.mainloop()