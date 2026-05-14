import cv2
import h5py
import json
import numpy
from typing import List, Dict, Tuple, Optional


def load_h5(file_path):
    result = dict()

    with h5py.File(file_path, 'r') as h5_file:
        for key in h5_file.keys():
            result[key] = numpy.array(h5_file.get(key))

    return result


def write_h5(sample: Dict[str, numpy.ndarray], path: str, compression: str ="gzip") -> None:
    with h5py.File(path, "w") as file:
        for key, value in sample.items():
            file.create_dataset(key, data=value, compression=compression)


def load_calibration(calibration_path: str) -> Dict:
    with open(calibration_path) as file:
        return json.load(file)


def write_calibration(calibration: Dict, json_path: str) -> None:
    write_json(calibration, json_path)


def write_json(dict: Dict, json_path: str) -> None:
    with open(json_path, 'w') as f:
        json.dump(dict, f, sort_keys=True, indent=2)


def project_point_cloud(height: int, width: int, points: numpy.ndarray, intrinsics: numpy.ndarray, extrinsics: numpy.ndarray):
    points_cam = numpy.matmul(extrinsics, points.T).T
    points_proj = numpy.matmul(intrinsics, points_cam.T).T

    depth = numpy.zeros(shape=(height, width), dtype=numpy.float32)
    pixel_coords = []

    for i in range(points_proj.shape[0]):
        z = points_cam[i, 2]

        if not numpy.isfinite(z) or z <= 0:
            pixel_coords.append(None)
            continue

        x = int(round(points_proj[i, 0] / points_proj[i, 2]))
        y = int(round(points_proj[i, 1] / points_proj[i, 2]))

        if y < 0 or y >= height or x < 0 or x >= width:
            pixel_coords.append(None)
            continue

        depth[y, x] = points_proj[i, 2]
        pixel_coords.append((x, y))

    return depth, pixel_coords
    

def visualization_color_overlay(image: numpy.ndarray,
                                pixel_coords: list,
                                color_mask: numpy.ndarray,
                                radius: int = 2) -> numpy.ndarray:
    """
    Draw colored points onto an RGB image.
    - image: RGB uint8
    - color_mask: Nx3 colors in RGB uint8
    Returns: RGB uint8
    """

    img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    for i, coord in enumerate(pixel_coords):
        if coord is None:
            continue
        x, y = coord
        r, g, b = color_mask[i]
        cv2.circle(img_bgr, (x, y), radius, (int(b), int(g), int(r)), -1)
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def project_and_overlay(points_xyz: numpy.ndarray, colors_rgb_float: numpy.ndarray, image_rgb: numpy.ndarray,
                        intrinsics: numpy.ndarray, extrinsics: numpy.ndarray, point_radius: int) -> Tuple[numpy.ndarray, List[Optional[Tuple[int,int]]]]:
    """
    Project 3D points and overlay colored circles onto a copy of image.
    - points_xyz: Nx3 XYZ
    - colors_rgb_float: Nx3 colors in RGB float [0,1]
    Returns: (overlay_image_rgb, pixel_coords_list)
    """
    points_h = numpy.append(points_xyz, numpy.ones((points_xyz.shape[0], 1)), axis=1)
    h, w = image_rgb.shape[:2]
    _, pix = project_point_cloud(h, w, points_h, intrinsics, extrinsics)

    colors_rgb_uint8 = (colors_rgb_float * 255).clip(0, 255).astype(numpy.uint8)
    overlay_img = visualization_color_overlay(image_rgb, pix, colors_rgb_uint8, radius=point_radius)
    return overlay_img, pix


def projection_to_point_cloud(depth: numpy.ndarray, intrinsics: numpy.ndarray, extrinsics: numpy.ndarray) -> numpy.ndarray:
    y, x = numpy.where(depth > 0)
    depth_values = depth[y, x]

    x_norm = (x - intrinsics[0, 2]) / intrinsics[0, 0]
    y_norm = (y - intrinsics[1, 2]) / intrinsics[1, 1]

    X_cam = x_norm * depth_values
    Y_cam = y_norm * depth_values
    Z_cam = depth_values

    X_cam = X_cam.flatten()
    Y_cam = Y_cam.flatten()
    Z_cam = Z_cam.flatten()

    points_cam = numpy.vstack((X_cam, Y_cam, Z_cam, numpy.ones_like(Z_cam)))

    T_world_inv = numpy.linalg.inv(extrinsics)
    points_world = T_world_inv @ points_cam

    points_world = points_world[:3].T

    return points_world

