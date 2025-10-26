import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import yaml
import cv2
from PIL import Image, ImageTk


class RectSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rect Selector")

        # Canvas for image display
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Variables
        self.image = None
        self.resized_image = None
        self.tk_image = None
        self.rectangles = []  # Store rectangles as [(x1, y1, x2, y2, name), ...]
        self.start_x = self.start_y = None
        self.rect_id = None
        self.scale_factor = 1.0  # Scale factor for resizing

        # Load image button
        self.load_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Save YAML button
        self.save_button = tk.Button(root, text="Save to YAML", command=self.save_to_yaml, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.bmp *.tiff")])
        if not file_path:
            return
        # Load the original image
        self.image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
        # Resize the image for display
        self.resized_image = self.resize_image(self.image, width=960)
        self.display_image()
        self.save_button.config(state=tk.NORMAL)

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
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def on_mouse_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_release(self, event):
        end_x, end_y = event.x, event.y
        name = simpledialog.askstring("Input", "Enter name for this rectangle:")
        if name:
            # Draw the name above the rectangle
            text_x = self.start_x
            text_y = min(self.start_y, end_y) - 10  # Position text above the rectangle
            self.canvas.create_text(text_x, text_y, text=name, anchor=tk.SW, fill="blue", font=("Arial", 12, "bold"))
            self.rectangles.append((self.start_x, self.start_y, end_x, end_y, name))
        else:
            self.canvas.delete(self.rect_id)  # Remove the rectangle if no name is provided

    def save_to_yaml(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return
        # Map rectangles back to original image coordinates
        rects = [
            [int(rect[0] / self.scale_factor), int(rect[1] / self.scale_factor), int(rect[2] / self.scale_factor), int(rect[3] / self.scale_factor)]
            for rect in self.rectangles
        ]
        rect_names = [rect[4] for rect in self.rectangles]
        data = {"rects": rects, "targets": rect_names}
        with open(file_path, "w") as file:
            yaml.dump(data, file)
        messagebox.showinfo("Saved", f"Rectangles saved to {file_path}")


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = RectSelectorApp(root)
    root.mainloop()
