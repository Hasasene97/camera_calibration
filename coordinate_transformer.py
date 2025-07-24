import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

class CoordinateTransformerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Transformer")

        # --- Frames ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        main_frame = tk.Frame(root)
        main_frame.pack(padx=10, pady=10)

        # --- Widgets ---
        self.upload_cctv_btn = tk.Button(top_frame, text="Upload CCTV Image", command=self.upload_cctv)
        self.upload_cctv_btn.pack(side=tk.LEFT, padx=5)

        self.upload_drone_btn = tk.Button(top_frame, text="Upload Drone Image", command=self.upload_drone)
        self.upload_drone_btn.pack(side=tk.LEFT, padx=5)

        self.ok_btn = tk.Button(top_frame, text="OK", command=self.process_images)
        self.ok_btn.pack(side=tk.LEFT, padx=5)

        self.cctv_canvas = tk.Canvas(main_frame, bg="lightgray", width=640, height=480)
        self.cctv_canvas.pack(side=tk.LEFT, padx=5)

        self.drone_canvas = tk.Canvas(main_frame, bg="lightgray", width=640, height=480)
        self.drone_canvas.pack(side=tk.LEFT, padx=5)

        self.cctv_canvas.bind("<Button-1>", self.select_cctv_point)
        self.drone_canvas.bind("<Button-1>", self.select_drone_point)

        # --- Image data ---
        self.cctv_image = None
        self.drone_image = None
        self.cctv_photo = None
        self.drone_photo = None
        self.cctv_points = []
        self.drone_points = []
        self.cctv_image_resized_ratio = 1
        self.drone_image_resized_ratio = 1


    def upload_cctv(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.cctv_image = cv2.imread(filepath)
        self.display_image(self.cctv_image, self.cctv_canvas, 'cctv')

    def upload_drone(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.drone_image = cv2.imread(filepath)
        self.display_image(self.drone_image, self.drone_canvas, 'drone')

    def display_image(self, image, canvas, image_type):
        canvas.delete("all")

        # Resize image to fit canvas
        h, w, _ = image.shape
        h_ratio = 480 / h
        w_ratio = 640 / w
        ratio = min(h_ratio, w_ratio)

        if image_type == 'cctv':
            self.cctv_image_resized_ratio = ratio
        else:
            self.drone_image_resized_ratio = ratio

        new_h, new_w = int(h * ratio), int(w * ratio)
        resized_image = cv2.resize(image, (new_w, new_h))

        # Convert for Tkinter
        image_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)

        if image_type == 'cctv':
            self.cctv_photo = ImageTk.PhotoImage(image_pil)
            canvas.create_image(0, 0, anchor=tk.NW, image=self.cctv_photo)
        else:
            self.drone_photo = ImageTk.PhotoImage(image_pil)
            canvas.create_image(0, 0, anchor=tk.NW, image=self.drone_photo)

    def select_cctv_point(self, event):
        # Store original coordinates
        original_x = event.x / self.cctv_image_resized_ratio
        original_y = event.y / self.cctv_image_resized_ratio
        self.cctv_points.append((original_x, original_y))

        # Draw point on canvas
        self.cctv_canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="red", outline="red")

    def select_drone_point(self, event):
        # Store original coordinates
        original_x = event.x / self.drone_image_resized_ratio
        original_y = event.y / self.drone_image_resized_ratio
        self.drone_points.append((original_x, original_y))

        # Draw point on canvas
        self.drone_canvas.create_oval(event.x - 3, event.y - 3, event.x + 3, event.y + 3, fill="blue", outline="blue")

    def process_images(self):
        if len(self.cctv_points) != len(self.drone_points) or len(self.cctv_points) < 4:
            print("Error: Please select at least 4 corresponding points for both images.")
            return

        cctv_pts = np.array(self.cctv_points)
        drone_pts = np.array(self.drone_points)

        homography_matrix, _ = cv2.findHomography(cctv_pts, drone_pts, cv2.RANSAC, 5.0)

        h, w, _ = self.drone_image.shape
        self.transformed_image = cv2.warpPerspective(self.cctv_image, homography_matrix, (w, h))

        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = CoordinateTransformerApp(root)
    root.mainloop()

    # After the main loop is destroyed, check if there is a transformed image
    if hasattr(app, 'transformed_image'):
        transformed_window = tk.Tk()
        transformed_window.title("Transformed Image")

        # Convert for Tkinter
        image_rgb = cv2.cvtColor(app.transformed_image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        photo = ImageTk.PhotoImage(image_pil)

        canvas = tk.Canvas(transformed_window, width=photo.width(), height=photo.height())
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)

        def save_image():
            filepath = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")])
            if not filepath:
                return
            cv2.imwrite(filepath, app.transformed_image)
            print(f"Image saved to {filepath}")

        save_btn = tk.Button(transformed_window, text="Save Image", command=save_image)
        save_btn.pack(pady=5)

        transformed_window.mainloop()
