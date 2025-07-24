import cv2
import numpy as np

def calculate_homography(cctv_points, drone_points):
    """
    Calculates the homography matrix from CCTV to drone coordinates.

    Args:
        cctv_points (np.ndarray): A numpy array of shape (n, 2) representing
                                 the coordinates of points in the CCTV footage.
        drone_points (np.ndarray): A numpy array of shape (n, 2) representing
                                  the corresponding coordinates of points in the
                                  drone footage.

    Returns:
        np.ndarray: The 3x3 homography matrix.
    """
    homography_matrix, _ = cv2.findHomography(cctv_points, drone_points)
    return homography_matrix

def transform_points(points, homography_matrix):
    """
    Transforms points using a homography matrix.

    Args:
        points (np.ndarray): A numpy array of shape (n, 2) representing the
                             points to be transformed.
        homography_matrix (np.ndarray): The 3x3 homography matrix.

    Returns:
        np.ndarray: The transformed points.
    """
    transformed_points = cv2.perspectiveTransform(points.reshape(-1, 1, 2).astype(np.float32), homography_matrix)
    return transformed_points.reshape(-1, 2)

def calculate_scale(drone_points, real_world_distance_meters):
    """
    Calculates the pixel-to-meter scale from the drone footage.

    Args:
        drone_points (np.ndarray): A numpy array of shape (2, 2) representing
                                  two points in the drone footage with a known
                                  real-world distance.
        real_world_distance_meters (float): The real-world distance between the
                                           two points in meters.

    Returns:
        float: The pixel-to-meter ratio.
    """
    pixel_distance = np.linalg.norm(drone_points[0] - drone_points[1])
    return real_world_distance_meters / pixel_distance

def to_meters(points, scale):
    """
    Converts pixel coordinates to meters.

    Args:
        points (np.ndarray): The points in pixel coordinates.
        scale (float): The pixel-to-meter ratio.

    Returns:
        np.ndarray: The points in meter coordinates.
    """
    return points * scale

if __name__ == '__main__':
    # --- Example Usage ---

    # 1. Define corresponding points between CCTV and drone footage.
    #    (These would be manually selected or found using feature matching)
    cctv_points = np.array([[100, 150], [500, 150], [100, 400], [500, 400]])
    drone_points = np.array([[50, 50], [450, 50], [50, 350], [450, 350]])

    # 2. Calculate the homography matrix.
    homography_matrix = calculate_homography(cctv_points, drone_points)
    print("Homography Matrix:\n", homography_matrix)

    # 3. Transform a point from CCTV to drone coordinates.
    cctv_point_to_transform = np.array([[250, 275]])
    drone_point = transform_points(cctv_point_to_transform, homography_matrix)
    print(f"\nTransformed point from CCTV to drone: {drone_point[0]}")

    # 4. Define two points in the drone footage with a known real-world distance.
    #    (e.g., the width of a crosswalk)
    drone_ref_points = np.array([[50, 50], [450, 50]])
    crosswalk_width_meters = 5.0  # meters

    # 5. Calculate the pixel-to-meter scale.
    scale = calculate_scale(drone_ref_points, crosswalk_width_meters)
    print(f"\nPixel-to-meter scale: {scale}")

    # 6. Convert the transformed drone point to meters.
    point_in_meters = to_meters(drone_point, scale)
    print(f"\nPoint in meters: {point_in_meters[0]}")
