import cv2
import numpy as np

# --- Global variables for GUI interactions ---
cctv_points_selection = []
drone_points_selection = []
scaling_points_selection = []

def select_points_callback(event, x, y, flags, param):
    """Callback for point selection GUI."""
    global cctv_points_selection, drone_points_selection
    combined_image, cctv_image, _ = param

    if event == cv2.EVENT_LBUTTONDOWN:
        if x < cctv_image.shape[1]:
            cctv_points_selection.append((x, y))
            cv2.circle(combined_image, (x, y), 5, (0, 255, 0), -1)
        else:
            drone_x = x - cctv_image.shape[1]
            drone_points_selection.append((drone_x, y))
            cv2.circle(combined_image, (x, y), 5, (0, 0, 255), -1)

def point_selection_gui(cctv_image, drone_image):
    """GUI for selecting corresponding points."""
    global cctv_points_selection, drone_points_selection
    cctv_points_selection, drone_points_selection = [], []

    height = max(cctv_image.shape[0], drone_image.shape[0])
    cctv_image_resized = cv2.resize(cctv_image, (int(cctv_image.shape[1] * height / cctv_image.shape[0]), height))
    drone_image_resized = cv2.resize(drone_image, (int(drone_image.shape[1] * height / drone_image.shape[0]), height))
    combined_image = np.hstack((cctv_image_resized, drone_image_resized))

    cv2.namedWindow("Point Selection")
    cv2.setMouseCallback("Point Selection", select_points_callback, (combined_image, cctv_image_resized, drone_image_resized))

    print("Select corresponding points on the images. Press 'o' when done, 'q' to quit.")
    while True:
        cv2.imshow("Point Selection", combined_image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('o'):
            if len(cctv_points_selection) == len(drone_points_selection) and len(cctv_points_selection) >= 4:
                break
            else:
                print("Please select at least 4 pairs of corresponding points.")
        elif key == ord('q'):
            cv2.destroyAllWindows()
            return None, None

    cv2.destroyAllWindows()
    return np.array(cctv_points_selection), np.array(drone_points_selection)

def select_scaling_points_callback(event, x, y, flags, param):
    """Callback for scaling points GUI."""
    global scaling_points_selection
    transformed_image = param[0]
    if event == cv2.EVENT_LBUTTONDOWN and len(scaling_points_selection) < 2:
        scaling_points_selection.append((x, y))
        cv2.circle(transformed_image, (x, y), 5, (0, 255, 255), -1)
        if len(scaling_points_selection) == 2:
            cv2.line(transformed_image, scaling_points_selection[0], scaling_points_selection[1], (255, 0, 0), 2)

def scaling_gui(transformed_image):
    """GUI for selecting scaling points and getting distance."""
    global scaling_points_selection
    scaling_points_selection = []

    cv2.namedWindow("Select Scaling Points")
    cv2.setMouseCallback("Select Scaling Points", select_scaling_points_callback, (transformed_image,))

    print("\nSelect two points on the transformed image for scaling. Press 's' to save.")
    while True:
        cv2.imshow("Select Scaling Points", transformed_image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            if len(scaling_points_selection) == 2:
                break
            else:
                print("Please select exactly two points.")
        elif key == ord('q'):
            cv2.destroyAllWindows()
            return None

    cv2.destroyAllWindows()
    try:
        distance_str = input("Enter real-world distance in meters: ")
        return float(distance_str)
    except ValueError:
        print("Invalid distance.")
        return None

def calculate_speed(points_data, homography_matrix, scale):
    """Calculates speed from a series of points and timestamps."""
    if len(points_data) < 2:
        return 0

    cctv_pts = np.array([[p[0], p[1]] for p in points_data])
    transformed_pts = cv2.perspectiveTransform(cctv_pts.reshape(-1, 1, 2).astype(np.float32), homography_matrix).reshape(-1, 2)

    total_distance = 0
    total_time = 0
    for i in range(len(transformed_pts) - 1):
        dist = np.linalg.norm(transformed_pts[i] - transformed_pts[i+1]) * scale
        time_diff = points_data[i+1][2] - points_data[i][2]
        if time_diff > 0:
            total_distance += dist
            total_time += time_diff

    return total_distance / total_time if total_time > 0 else 0

def main():
    """Main function to run the coordinate transformation tool."""
    cctv_image_path = input("Enter the path to the CCTV image: ")
    drone_image_path = input("Enter the path to the drone image: ")

    cctv_image = cv2.imread(cctv_image_path)
    drone_image = cv2.imread(drone_image_path)

    if cctv_image is None or drone_image is None:
        print("Error: Could not load one or both images. Please check the paths.")
        return

    # 1. Point Selection
    cctv_pts, drone_pts = point_selection_gui(cctv_image, drone_image)
    if cctv_pts is None:
        return

    # 2. Homography and Transformation
    homography_matrix, _ = cv2.findHomography(cctv_pts, drone_pts, cv2.RANSAC, 5.0)
    height, width, _ = drone_image.shape
    transformed_image = cv2.warpPerspective(cctv_image, homography_matrix, (width, height))

    # 3. Scaling
    real_distance = scaling_gui(transformed_image.copy())
    if real_distance is None:
        return

    pixel_distance = np.linalg.norm(np.array(scaling_points_selection[0]) - np.array(scaling_points_selection[1]))
    scale = real_distance / pixel_distance
    print(f"Calculated scale: {scale} meters/pixel")

    # 4. Speed Calculation
    points_for_speed = []
    print("\nEnter coordinates and timestamps for speed calculation (format: x,y,timestamp).")
    print("Enter 'done' when you are finished.")
    while True:
        try:
            line = input("> ")
            if line.lower() == 'done':
                break
            x, y, t = map(float, line.split(','))
            points_for_speed.append((x, y, t))
        except ValueError:
            print("Invalid input.")

    if points_for_speed:
        speed = calculate_speed(points_for_speed, homography_matrix, scale)
        print(f"\nCalculated average speed: {speed:.2f} m/s")

if __name__ == '__main__':
    main()
