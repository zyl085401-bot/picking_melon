import yaml
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from rect_extractor import JsonBBoxExtractor


class RectGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rect Viewer")

        # Main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas for image display
        self.canvas = tk.Canvas(self.main_frame, cursor="arrow", bg="gray")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right panel for controls
        self.control_panel = tk.Frame(self.main_frame, width=200, bg="lightgray")
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Variables
        self.rect_data = {}  # Rectangle data from JSON file
        self.rects = []  # List of rectangles to draw
        self.rect_names = []  # List of rectangle names
        self.save_directory = None  # Directory to save cropped images
        self.tk_image = None  # Tkinter image for display
        self.image = None  # Current image (OpenCV format)
        self.resized_image = None  # Resized image for display
        self.scale_factor = 1.0  # Scale factor for resizing
        self.rect_prefix = tk.StringVar()  # Prefix for rectangle naming
        self.rect_rows = tk.IntVar()  # Rows
        self.rect_cols = tk.IntVar()  # Cols

        # Load Image button
        self.load_image_button = tk.Button(self.control_panel, text="Load Image", command=self.load_image)
        self.load_image_button.pack(fill=tk.X, padx=5, pady=5)

        # Load JSON button
        self.load_json_button = tk.Button(self.control_panel, text="Load JSON", command=self.load_json)
        self.load_json_button.pack(fill=tk.X, padx=5, pady=5)

        # Draw Rectangles button
        self.draw_rectangles_button = tk.Button(self.control_panel, text="Draw Rectangles", command=self.draw_rectangles)
        self.draw_rectangles_button.pack(fill=tk.X, padx=5, pady=5)

        # Filter Rectangles button
        self.filter_rectangles_button = tk.Button(self.control_panel, text="Filter Rectangles", command=self.filter_rectangles)
        self.filter_rectangles_button.pack(fill=tk.X, padx=5, pady=5)

        # Textbox for Rect Prefix
        tk.Label(self.control_panel, text="Rect Prefix:", bg="lightgray").pack(padx=5, pady=(10, 0))
        self.rect_prefix_entry = tk.Entry(self.control_panel, textvariable=self.rect_prefix)
        self.rect_prefix_entry.pack(fill=tk.X, padx=5, pady=5)

        # Textbox for Rect Rows
        tk.Label(self.control_panel, text="Rows:", bg="lightgray").pack(padx=5, pady=(10, 0))
        self.rect_rows_entry = tk.Entry(self.control_panel, textvariable=self.rect_rows)
        self.rect_rows_entry.pack(fill=tk.X, padx=5, pady=5)

        # Textbox for Rect Prefix
        tk.Label(self.control_panel, text="Cols:", bg="lightgray").pack(padx=5, pady=(10, 0))
        self.rect_cols_entry = tk.Entry(self.control_panel, textvariable=self.rect_cols)
        self.rect_cols_entry.pack(fill=tk.X, padx=5, pady=5)

        # Generate Rect button
        self.generate_rects_button = tk.Button(self.control_panel, text="Generate Rects", command=self.generate_rects)
        self.generate_rects_button.pack(fill=tk.X, padx=5, pady=5)

        # Save Rect button
        self.save_rect_button = tk.Button(self.control_panel, text="Save to Yaml", command=self.save_rects)
        self.save_rect_button.pack(fill=tk.X, padx=5, pady=5)

    def load_json(self):
        json_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not json_path:
            return
        with open(json_path, "r") as file:
            bbox_extractor = JsonBBoxExtractor(json_path)
            rects = bbox_extractor.get_bboxes()
            self.rect_data = bbox_extractor.sort_bboxes_by_sum(rects)
        messagebox.showinfo("Success", "JSON file loaded successfully.")

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.bmp *.tiff")])
        if not file_path:
            return
        self.image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
        self.resized_image = self.resize_image(self.image, width=960)
        self.display_image()
        messagebox.showinfo("Success", "Image file loaded successfully.")

    def resize_image(self, image, width):
        """Resize the image to the given width while maintaining aspect ratio."""
        h, w, _ = image.shape
        self.scale_factor = width / w
        new_height = int(h * self.scale_factor)
        resized = cv2.resize(image, (width, new_height), interpolation=cv2.INTER_AREA)
        return resized

    def display_image(self):
        image = Image.fromarray(self.resized_image)
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def draw_rectangles(self):
        """Draw rectangles from JSON file on the current image."""
        for rect in self.rect_data:
            self.draw_rectangle(rect)
        messagebox.showinfo("Success", "Draw rects successfully.")

    def filter_rectangles(self):
        """Filter rectangles on the current image."""
        self.display_image()
        if self.rect_data:
            self.draw_rectangle(self.rect_data[0])
            self.draw_rectangle(self.rect_data[-1])
        messagebox.showinfo("Success", "Filter rects successfully.")

    def draw_rectangle(self, rect, color="red", name=None):
        """Draw rectangle on the current image."""
        x1, y1, x2, y2 = rect[0:4]
        x1 = int(x1 * self.scale_factor)
        y1 = int(y1 * self.scale_factor)
        x2 = int(x2 * self.scale_factor)
        y2 = int(y2 * self.scale_factor)
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
        if name is not None:
            self.canvas.create_text(x1, (y1 + y2) // 2, text=name, anchor=tk.SW, fill="blue", font=("Arial", 12, "bold"))

    def generate_rects(self):
        """Generate rectangles based on JSON data."""
        if not self.rect_data:
            messagebox.showwarning("Warning", "No JSON data loaded.")
            return
        if self.rect_data and len(self.rect_data) >= 2:
            rect_lt = self.rect_data[0]
            rect_br = self.rect_data[-1]
            rect_w = rect_br[2] - rect_br[0]
            rect_h = rect_br[3] - rect_br[1]
            rows = self.rect_rows.get() or 1
            cols = self.rect_cols.get() or 1
            start_point = [(rect_lt[0] + rect_lt[2]) // 2, (rect_lt[1] + rect_lt[3]) // 2]
            end_point = [(rect_br[0] + rect_br[2]) // 2, (rect_br[1] + rect_br[3]) // 2]
            row_step = (end_point[0] - start_point[0]) // (cols - 1)
            col_step = (end_point[1] - start_point[1]) // (rows - 1)
            self.rect_names = []
            self.rects = []
            for i in range(rows):
                for j in range(cols):
                    cx = start_point[0] + j * row_step
                    cy = start_point[1] + i * col_step
                    rect = [cx - rect_w // 2, cy - rect_h // 2, cx + rect_w // 2, cy + rect_h // 2]
                    self.rects.append(rect)
                    self.rect_names.append(f"{self.rect_prefix.get()}_{i+1}_{j+1}")
                    self.draw_rectangle(rect, color="green", name=self.rect_names[-1])
        messagebox.showinfo("Success", "Rectangles generated successfully.")

    def save_rects(self):
        """Save rectangles to the specified file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return
        data = {"rect": self.rects, "target": [{"name": name} for name in self.rect_names]}
        with open(file_path, "w") as file:
            yaml.dump(data, file)
        messagebox.showinfo("Saved", f"Rectangles saved to {file_path}")

    def set_save_directory(self):
        """Set the directory to save cropped rectangles."""
        save_dir = filedialog.askdirectory()
        if save_dir:
            self.save_directory = save_dir
            messagebox.showinfo("Success", f"Save directory set to: {save_dir}")


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = RectGeneratorApp(root)
    root.mainloop()
