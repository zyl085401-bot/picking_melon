import os
import cv2
import yaml
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class RectViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rect Viewer")

        # Canvas for image display
        self.canvas = tk.Canvas(root, cursor="arrow")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Variables
        self.image_files = []  # List of image file paths
        self.current_index = 0  # Current image index
        self.rect_data = {}  # Rectangle data from YAML file
        self.save_directory = None  # Directory to save cropped images
        self.rect_counters = {}  # Counters for each rect name
        self.tk_image = None  # Tkinter image for display
        self.image = None  # Current image (OpenCV format)
        self.resized_image = None  # Resized image for display
        self.scale_factor = 1.0  # Scale factor for resizing

        # Load YAML button
        self.load_yaml_button = tk.Button(root, text="Load YAML", command=self.load_yaml)
        self.load_yaml_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Set Save Directory button
        self.set_save_dir_button = tk.Button(root, text="Set Save Directory", command=self.set_save_directory)
        self.set_save_dir_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Load folder button
        self.load_folder_button = tk.Button(root, text="Load Images", command=self.load_folder)
        self.load_folder_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Next button
        self.next_button = tk.Button(root, text="Next", command=self.show_next_image, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5, pady=5)

    def load_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        # Load all image files in the folder
        self.image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".png", ".bmp", ".tiff"))]
        if not self.image_files:
            messagebox.showerror("Error", "No image files found in the selected folder.")
            return
        self.current_index = 0
        self.next_button.config(state=tk.NORMAL)
        self.load_image()

    def load_yaml(self):
        yaml_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        if not yaml_path:
            return
        with open(yaml_path, "r") as file:
            self.rect_data = yaml.safe_load(file)
        # Reset counters for each rect name
        self.rect_counters = {name: 0 for name in self.rect_data.get("targets", [])}
        messagebox.showinfo("Success", "YAML file loaded successfully.")

    def set_save_directory(self):
        save_dir = filedialog.askdirectory()
        if save_dir:
            self.save_directory = save_dir
            messagebox.showinfo("Success", f"Save directory set to: {save_dir}")

    def load_image(self):
        if self.current_index >= len(self.image_files):
            messagebox.showinfo("End", "No more images to display.")
            return
        file_path = self.image_files[self.current_index]
        self.image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
        self.resized_image = self.resize_image(self.image, width=960)
        self.display_image(file_path)

    def resize_image(self, image, width):
        """Resize the image to the given width while maintaining aspect ratio."""
        h, w, _ = image.shape
        self.scale_factor = width / w
        new_height = int(h * self.scale_factor)
        resized = cv2.resize(image, (width, new_height), interpolation=cv2.INTER_AREA)
        return resized

    def display_image(self, file_path):
        # Display the current image
        image = Image.fromarray(self.resized_image)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.draw_rectangles()

    def draw_rectangles(self):
        """Draw rectangles from YAML file on the current image."""
        if self.rect_data is None or "rects" not in self.rect_data or "targets" not in self.rect_data:
            return
        for rect, rect_name in zip(self.rect_data["rects"], self.rect_data["targets"]):
            x1 = int(rect[0] * self.scale_factor)
            y1 = int(rect[1] * self.scale_factor)
            x2 = int(rect[2] * self.scale_factor)
            y2 = int(rect[3] * self.scale_factor)
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)
            self.canvas.create_text(x1, y1 - 10, text=rect_name, anchor=tk.SW, fill="blue", font=("Arial", 12, "bold"))

            # Save cropped region
            if self.save_directory:
                self.save_cropped_region(rect, rect_name)

    def save_cropped_region(self, rect, name):
        """Save the cropped region based on the rectangle coordinates."""
        x1, y1, x2, y2 = rect[0:4]
        cropped = self.image[int(y1) : int(y2), int(x1) : int(x2)]

        # Increment counter for the rect name
        self.rect_counters[name] += 1
        save_name = f"{name}_{self.rect_counters[name]:03d}.jpg"
        save_path = os.path.join(self.save_directory, save_name)
        cv2.imwrite(save_path, cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))

    def show_next_image(self):
        self.current_index += 1
        if self.current_index < len(self.image_files):
            self.load_image()
        else:
            messagebox.showinfo("End", "No more images to display.")
            self.next_button.config(state=tk.DISABLED)


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = RectViewerApp(root)
    root.mainloop()
