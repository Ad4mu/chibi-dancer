import tkinter as tk
import cv2
from PIL import Image, ImageTk
import numpy as np
import os

class VideoPlayer:
    def __init__(self, root, video_path):
        self.root = root
        self.root.title("Video Player")
        self.root.geometry("500x600")
        self.root.attributes('-transparentcolor', 'black')  # Make the root window transparent
        self.root.attributes('-topmost', True)  # Make the window always on top
        self.root.config(bg='black')  # Set background color of the root window

        self.video_path = video_path
        print(f"Loading video from: {self.video_path}")
        if not os.path.isfile(self.video_path):
            raise FileNotFoundError(f"Video file '{self.video_path}' not found")

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Error opening video file '{self.video_path}'")

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            raise ValueError(f"Video file '{self.video_path}' has zero FPS, unable to calculate delay")

        self.delay = int(454 / fps)

        # Initialize variables to store original video dimensions
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate dimensions to fit within 500x600 preserving aspect ratio
        self.display_width, self.display_height = self.calculate_display_size(self.video_width, self.video_height, 500, 600)

        self.canvas = tk.Canvas(root, width=self.display_width, height=self.display_height, bg='black', bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.root.bind('<B1-Motion>', self.move_window)
        self.root.bind('<Button-1>', self.set_window_position)

        self.update()

    def calculate_display_size(self, original_width, original_height, max_width, max_height):
        # Calculate dimensions to fit within max_width x max_height preserving aspect ratio
        ratio = min(max_width / original_width, max_height / original_height)
        display_width = int(original_width * ratio)
        display_height = int(original_height * ratio)
        return display_width, display_height

    def set_window_position(self, event):
        self._drag_data = {"x": event.x, "y": event.y}

    def move_window(self, event):
        x = self.root.winfo_pointerx() - self._drag_data["x"]
        y = self.root.winfo_pointery() - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        # Resize frame to fit within display dimensions preserving aspect ratio
        resized_frame = cv2.resize(frame, (self.display_width, self.display_height))

        # Convert frame to RGBA format
        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGBA)

        # Split the frame into RGB and alpha channels
        rgb_frame = resized_frame[:, :, :3]  # RGB channels
        alpha_channel = resized_frame[:, :, 3]  # Alpha channel

        # Convert RGB frame to HSV color space
        hsv_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2HSV)

        # Define range of green color in HSV
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])

        # Threshold the HSV image to get only green colors
        mask = cv2.inRange(hsv_frame, lower_green, upper_green)

        # Set areas of the alpha channel that are green to be fully transparent
        alpha_channel[mask != 0] = 0

        # Merge RGB channels and updated alpha channel back into RGBA format
        processed_frame = cv2.merge([rgb_frame, alpha_channel])

        # Convert processed frame to PIL Image
        image = Image.fromarray(processed_frame)

        # Convert PIL Image to Tkinter PhotoImage with alpha channel
        self.photo = ImageTk.PhotoImage(image=image)

        # Clear previous image
        self.canvas.delete("all")

        # Display on Tkinter canvas
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        # Schedule the next frame update
        self.root.after(self.delay, self.update)

if __name__ == "__main__":
    try:
        print("Starting application")
        root = tk.Tk()
        root.overrideredirect(True)
        VideoPlayer(root, "video.mp4")
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
