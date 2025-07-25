import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

class CoordinateTransformerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Transformer with Zoom, Pan, Undo/Redo")

        # --- Frames ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        main_frame = tk.Frame(root)
        main_frame.pack(padx=10, pady=10)

        # --- Buttons ---
        self.upload_cctv_btn = tk.Button(top_frame, text="Upload CCTV", command=self.upload_cctv)
        self.upload_cctv_btn.pack(side=tk.LEFT, padx=5)

        self.upload_drone_btn = tk.Button(top_frame, text="Upload Drone", command=self.upload_drone)
        self.upload_drone_btn.pack(side=tk.LEFT, padx=5)

        self.undo_btn = tk.Button(top_frame, text="Undo", command=self.undo_point)
        self.undo_btn.pack(side=tk.LEFT, padx=5)

        self.redo_btn = tk.Button(top_frame, text="Redo", command=self.redo_point)
        self.redo_btn.pack(side=tk.LEFT, padx=5)

        self.ok_btn = tk.Button(top_frame, text="OK", command=self.process_images)
        self.ok_btn.pack(side=tk.LEFT, padx=5)

        # --- Canvas ---
        self.cctv_canvas = tk.Canvas(main_frame, bg="lightgray", width=640, height=480)
        self.cctv_canvas.pack(side=tk.LEFT, padx=5)

        self.drone_canvas = tk.Canvas(main_frame, bg="lightgray", width=640, height=480)
        self.drone_canvas.pack(side=tk.LEFT, padx=5)

        # --- Bindings ---
        self.cctv_canvas.bind("<Button-1>", self.select_cctv_point)
        self.drone_canvas.bind("<Button-1>", self.select_drone_point)

        # Zoom & Pan
        self.cctv_canvas.bind("<MouseWheel>", lambda e: self.zoom(e, 'cctv'))
        self.drone_canvas.bind("<MouseWheel>", lambda e: self.zoom(e, 'drone'))
        self.cctv_canvas.bind("<Button-3>", lambda e: self.start_pan(e, 'cctv'))
        self.cctv_canvas.bind("<B3-Motion>", lambda e: self.pan(e, 'cctv'))
        self.drone_canvas.bind("<Button-3>", lambda e: self.start_pan(e, 'drone'))
        self.drone_canvas.bind("<B3-Motion>", lambda e: self.pan(e, 'drone'))

        # --- Image Data ---
        self.cctv_image = None
        self.drone_image = None
        self.cctv_photo = None
        self.drone_photo = None

        # --- State ---
        self.cctv_points = []
        self.drone_points = []
        self.undo_stack_cctv = []
        self.undo_stack_drone = []
        self.redo_stack_cctv = []
        self.redo_stack_drone = []

        # Zoom & Pan variables
        self.zoom_factor_cctv = 1.0
        self.zoom_factor_drone = 1.0
        self.pan_offset_cctv = [0, 0]
        self.pan_offset_drone = [0, 0]
        self.drag_start = None

    def upload_cctv(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return
        self.cctv_image = cv2.imread(filepath)
        self.display_image('cctv')

    def upload_drone(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return
        self.drone_image = cv2.imread(filepath)
        self.display_image('drone')

    def display_image(self, image_type):
        if image_type == 'cctv' and self.cctv_image is not None:
            img = cv2.cvtColor(self.cctv_image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            w, h = img_pil.size
            img_pil = img_pil.resize((int(w * self.zoom_factor_cctv), int(h * self.zoom_factor_cctv)))
            self.cctv_photo = ImageTk.PhotoImage(img_pil)
            self.cctv_canvas.delete("all")
            self.cctv_canvas.create_image(self.pan_offset_cctv[0], self.pan_offset_cctv[1], anchor=tk.NW, image=self.cctv_photo)

        elif image_type == 'drone' and self.drone_image is not None:
            img = cv2.cvtColor(self.drone_image, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            w, h = img_pil.size
            img_pil = img_pil.resize((int(w * self.zoom_factor_drone), int(h * self.zoom_factor_drone)))
            self.drone_photo = ImageTk.PhotoImage(img_pil)
            self.drone_canvas.delete("all")
            self.drone_canvas.create_image(self.pan_offset_drone[0], self.pan_offset_drone[1], anchor=tk.NW, image=self.drone_photo)

    def zoom(self, event, image_type):
        if image_type == 'cctv':
            self.zoom_factor_cctv *= 1.1 if event.delta > 0 else 0.9
            self.display_image('cctv')
        else:
            self.zoom_factor_drone *= 1.1 if event.delta > 0 else 0.9
            self.display_image('drone')

    def start_pan(self, event, image_type):
        self.drag_start = (event.x, event.y)

    def pan(self, event, image_type):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            if image_type == 'cctv':
                self.pan_offset_cctv[0] += dx
                self.pan_offset_cctv[1] += dy
                self.display_image('cctv')
            else:
                self.pan_offset_drone[0] += dx
                self.pan_offset_drone[1] += dy
                self.display_image('drone')
            self.drag_start = (event.x, event.y)

    def select_cctv_point(self, event):
        self.cctv_points.append((event.x, event.y))
        self.undo_stack_cctv.append((event.x, event.y))
        self.cctv_canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="red")

    def select_drone_point(self, event):
        self.drone_points.append((event.x, event.y))
        self.undo_stack_drone.append((event.x, event.y))
        self.drone_canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="blue")

    def undo_point(self):
        if self.undo_stack_cctv and self.undo_stack_drone:
            self.redo_stack_cctv.append(self.undo_stack_cctv.pop())
            self.redo_stack_drone.append(self.undo_stack_drone.pop())
            self.cctv_points.pop()
            self.drone_points.pop()
            self.display_image('cctv')
            self.display_image('drone')
            for x, y in self.cctv_points:
                self.cctv_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")
            for x, y in self.drone_points:
                self.drone_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="blue")

    def redo_point(self):
        if self.redo_stack_cctv and self.redo_stack_drone:
            point_cctv = self.redo_stack_cctv.pop()
            point_drone = self.redo_stack_drone.pop()
            self.cctv_points.append(point_cctv)
            self.drone_points.append(point_drone)
            self.undo_stack_cctv.append(point_cctv)
            self.undo_stack_drone.append(point_drone)
            self.display_image('cctv')
            self.display_image('drone')
            for x, y in self.cctv_points:
                self.cctv_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")
            for x, y in self.drone_points:
                self.drone_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="blue")

    def process_images(self):
        if len(self.cctv_points) != len(self.drone_points) or len(self.cctv_points) < 4:
            print("Error: Select at least 4 corresponding points.")
            return

        cctv_pts = np.array([self.canvas_to_image_coords(p, 'cctv') for p in self.cctv_points], dtype=np.float32)
        drone_pts = np.array([self.canvas_to_image_coords(p, 'drone') for p in self.drone_points], dtype=np.float32)

        H, _ = cv2.findHomography(cctv_pts, drone_pts, cv2.RANSAC, 5.0)
        print("Homography Matrix:\n", H)

        h, w, _ = self.drone_image.shape
        transformed_image = cv2.warpPerspective(self.cctv_image, H, (w, h))

        self.show_transformed_image_window(transformed_image)

    def canvas_to_image_coords(self, point, image_type):
        if image_type == 'cctv':
            x = (point[0] - self.pan_offset_cctv[0]) / self.zoom_factor_cctv
            y = (point[1] - self.pan_offset_cctv[1]) / self.zoom_factor_cctv
        else:
            x = (point[0] - self.pan_offset_drone[0]) / self.zoom_factor_drone
            y = (point[1] - self.pan_offset_drone[1]) / self.zoom_factor_drone
        return (x, y)

    def show_transformed_image_window(self, image):
        result_window = tk.Toplevel(self.root)
        result_window.title("Transformed CCTV Image")

        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)

        canvas = tk.Canvas(result_window, width=img_tk.width(), height=img_tk.height())
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        canvas.image = img_tk

        def save_action():
            filepath = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")])
            if filepath:
                cv2.imwrite(filepath, image)
                print(f"Image saved to {filepath}")

        save_btn = tk.Button(result_window, text="Save Image", command=save_action)
        save_btn.pack(pady=10)


if __name__ == '__main__':
    root = tk.Tk()
    app = CoordinateTransformerApp(root)
    root.mainloop()
