import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple
from recognizer import Recognizer
from templates import templates as raw_templates

Point = Tuple[float, float]

class StrokePanel(tk.Canvas):
    def __init__(self, master, recognizer: Recognizer, highlight_callback, *args, **kwargs):
        super().__init__(master, bg='white', *args, **kwargs)
        self.recognizer = recognizer
        self.highlight_callback = highlight_callback  # Store the callback
        self.bind("<ButtonPress-1>", self.on_button_press)
        self.bind("<B1-Motion>", self.on_move_press)
        self.bind("<ButtonRelease-1>", self.on_button_release)
        self.points: List[Point] = []
        self.current_line = None

    def on_button_press(self, event):
        self.points = [(event.x, event.y)]
        self.current_line = self.create_line(event.x, event.y, event.x, event.y, fill='black', width=2)

    def on_move_press(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        if self.current_line:
            self.coords(self.current_line, *self.flatten_points(self.points))
    
    def on_button_release(self, event):
        if len(self.points) < 10:
            messagebox.showinfo("Too Short", "Stroke is too short, please try again.")
            self.clear()
            return
        try:
            result, score, best_index = self.recognizer.recognize(self.points)
            messagebox.showinfo("Result", f"Recognized as: {result} (Score: {score:.2f})")
            # Use the callback to highlight the matched template
            self.highlight_callback(best_index)
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        self.clear()

    def clear(self):
        # print("Clearing the StrokePanel...")
        self.delete("all")
        self.points = []
        self.current_line = None

    def flatten_points(self, points: List[Point]) -> List[float]:
        return [coord for point in points for coord in point]

class TemplatePanel(tk.Frame):
    def __init__(self, master, recognizer: Recognizer, templates: List[dict], num_samples: int, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.templates = templates
        self.recognizer = recognizer
        self.num_samples = num_samples
        self.canvases = []
        self.create_template_canvases()

    def create_template_canvases(self):
        # Create a grid to display templates
        rows = 2
        cols = 5
        for index, template in enumerate(self.templates):
            frame = tk.Frame(self, padx=5, pady=5, bd=2, relief=tk.RIDGE)
            frame.grid(row=index // cols, column=index % cols, padx=5, pady=5)
            label = tk.Label(frame, text=f"Digit {template['name']}")
            label.pack()
            canvas_size = 100
            canvas = tk.Canvas(frame, width=canvas_size, height=canvas_size, bg='lightgray')
            canvas.pack()

            # Draw the template on the canvas
            points = raw_templates[index]['points']
            points = self.recognizer.resample(points, self.num_samples)
            # Rotate back to prevent rotation showing on the screen
            # radians = self.recognizer.indicative_angle(points)
            # points = self.recognizer.rotate_by(points, -radians)
            points = self.recognizer.scale_to_square(points, 250)
            points = self.recognizer.translate_to_origin(points)

            self.draw_template(canvas, points, canvas_size)
            self.canvases.append(canvas)

    def draw_template(self, canvas: tk.Canvas, points: List[Point], size: int):
        if not points:
            return
        
        # Find the bounding box of the points
        # Fixed minx, miny to 0, 0 and maxx, maxy to 100, 100
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        width = max_x - min_x
        height = max_y - min_y

        # Prevent division by zero
        if width == 0:
            width = 1
        if height == 0:
            height = 1

        # Calculate scale to fit the canvas with padding
        padding = 10
        scale_x = (size - 2 * padding) / width
        scale_y = (size - 2 * padding) / height
        scale = min(scale_x, scale_y)

        # Transform points
        transformed = [
            ((p[0] - min_x) * scale + padding, (p[1] - min_y) * scale + padding)
            for p in points
        ]

        # Flatten the list of points for create_line or create_polygon
        flattened = [coord for point in transformed for coord in point]
        # Draw lines or polygons
        if points[0] == points[-1]:
            # Closed shape, use create_polygon
            canvas.create_polygon(*flattened, fill='', outline='blue', width=2)
        else:
            # Open shape, use create_line
            canvas.create_line(*flattened, fill='blue', width=2)


    def highlight_template(self, index: int):
        # Reset all canvases
        for canvas in self.canvases:
            canvas.config(bg='lightgray')
        # Highlight the selected template
        if 0 <= index < len(self.canvases):
            self.canvases[index].config(bg='yellow')

class App(tk.Tk):
    def __init__(self, recognizer: Recognizer):
        super().__init__()
        self.title("1$ Unistroke Recognizer")
        self.geometry("1000x600")  # Increased size to better accommodate templates
        self.recognizer = recognizer

        # Main frame to hold drawing and templates
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # TemplatePanel for displaying templates
        template_frame = tk.Frame(main_frame, width=400, height=600)
        template_frame.pack(side=tk.RIGHT, fill=tk.Y)
        template_label = tk.Label(template_frame, text="Templates", font=("Arial", 16))
        template_label.pack(pady=10)
        self.template_panel = TemplatePanel(template_frame, self.recognizer, self.recognizer.templates, self.recognizer.num_samples)
        self.template_panel.pack(fill=tk.BOTH, expand=True)

        # StrokePanel for user drawing (passed the highlight callback)
        self.panel = StrokePanel(main_frame, self.recognizer, self.template_panel.highlight_template, width=600, height=600)
        self.panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=file_menu)
        file_menu.add_command(label="Clear Drawing", command=self.panel.clear)
        file_menu.add_command(label="Exit", command=self.quit)

def create_app(num_samples: int) -> App:
    recognizer = Recognizer(raw_templates, num_samples=num_samples)
    app = App(recognizer)
    return app