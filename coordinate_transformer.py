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
        self.cctv_canvas.bind("<MouseWheel>", self.zoom_cctv)
        self.drone_canvas.bind("<MouseWheel>", self.zoom_drone)
        self.cctv_canvas.bind("<B2-Motion>", self.pan_cctv)
        self.drone_canvas.bind("<B2-Motion>", self.pan_drone)

        # --- Image data ---
        self.cctv_image = None
        self.drone_image = None
        self.cctv_photo = None
        self.drone_photo = None
        self.cctv_points = []
        self.drone_points = []

        # --- Zoom/Pan Data ---
        self.cctv_scale = 1.0
        self.drone_scale = 1.0
        self.cctv_center_x = 0
        self.cctv_center_y = 0
        self.drone_center_x = 0
        self.drone_center_y = 0


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

    def display_image(self, image, canvas, image_type, scale, center_x, center_y):
        canvas.delete("all")
        if image is None:
            return

        h, w, _ = image.shape

        # New dimensions based on scale
        new_w, new_h = int(w * scale), int(h * scale)

        # Resizing the image
        resized_image = cv2.resize(image, (new_w, new_h))

        # Determine the region to display
        display_x1 = center_x - 640 // 2
        display_y1 = center_y - 480 // 2
        display_x2 = center_x + 640 // 2
        display_y2 = center_y + 480 // 2

        # Crop the resized image to the canvas size
        crop_x1 = max(0, display_x1)
        crop_y1 = max(0, display_y1)
        crop_x2 = min(new_w, display_x2)
        crop_y2 = min(new_h, display_y2)

        cropped_image_cv = resized_image[crop_y1:crop_y2, crop_x1:crop_x2]

        # Convert for Tkinter
        image_rgb = cv2.cvtColor(cropped_image_cv, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)

        photo = ImageTk.PhotoImage(image_pil)

        # Calculate where to place the image on the canvas
        canvas_x = (640 - (crop_x2 - crop_x1)) // 2
        canvas_y = (480 - (crop_y2 - crop_y1)) // 2

        if image_type == 'cctv':
            self.cctv_photo = photo
            canvas.create_image(canvas_x, canvas_y, anchor=tk.NW, image=self.cctv_photo)
        else:
            self.drone_photo = photo
            canvas.create_image(canvas_x, canvas_y, anchor=tk.NW, image=self.drone_photo)


    def select_cctv_point(self, event):
        # Adjust for panning and scaling
        canvas_x = event.x
        canvas_y = event.y

        # Calculate the position on the scaled image
        img_x = self.cctv_center_x - (320 - canvas_x)
        img_y = self.cctv_center_y - (240 - canvas_y)

        # Convert to original image coordinates
        original_x = img_x / self.cctv_scale
        original_y = img_y / self.cctv_scale

        self.cctv_points.append((original_x, original_y))

        # Draw point on canvas
        self.cctv_canvas.create_oval(canvas_x - 3, canvas_y - 3, canvas_x + 3, canvas_y + 3, fill="red", outline="red")

    def select_drone_point(self, event):
        # Adjust for panning and scaling
        canvas_x = event.x
        canvas_y = event.y

        # Calculate the position on the scaled image
        img_x = self.drone_center_x - (320 - canvas_x)
        img_y = self.drone_center_y - (240 - canvas_y)

        # Convert to original image coordinates
        original_x = img_x / self.drone_scale
        original_y = img_y / self.drone_scale

        self.drone_points.append((original_x, original_y))

        # Draw point on canvas
        self.drone_canvas.create_oval(canvas_x - 3, canvas_y - 3, canvas_x + 3, canvas_y + 3, fill="blue", outline="blue")

    def zoom_cctv(self, event):
        if event.delta > 0:
            self.cctv_scale *= 1.1
        else:
            self.cctv_scale /= 1.1
        self.display_image(self.cctv_image, self.cctv_canvas, 'cctv', self.cctv_scale, event.x, event.y)

    def zoom_drone(self, event):
        if event.delta > 0:
            self.drone_scale *= 1.1
        else:
            self.drone_scale /= 1.1
        self.display_image(self.drone_image, self.drone_canvas, 'drone', self.drone_scale, event.x, event.y)

    def pan_cctv(self, event):
        self.cctv_center_x -= event.x - self.cctv_canvas.winfo_width() / 2
        self.cctv_center_y -= event.y - self.cctv_canvas.winfo_height() / 2
        self.display_image(self.cctv_image, self.cctv_canvas, 'cctv', self.cctv_scale, self.cctv_center_x, self.cctv_center_y)

    def pan_drone(self, event):
        self.drone_center_x -= event.x - self.drone_canvas.winfo_width() / 2
        self.drone_center_y -= event.y - self.drone_canvas.winfo_height() / 2
        self.display_image(self.drone_image, self.drone_canvas, 'drone', self.drone_scale, self.drone_center_x, self.drone_center_y)

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
