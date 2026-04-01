import cv2
import argparse

from config_loader import load_config, resolve_path

def print_image_details_cv2(image_path, print_width_in=None, print_height_in=None):
    print(f"File: {image_path}")
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("Error: Unable to open image with cv2.")
        return
    height, width = img.shape[:2]
    print(f"Shape (HxWxC): {img.shape}")
    print(f"Resolution: {width} x {height} pixels")
    print(f"Channels: {img.shape[2] if len(img.shape) == 3 else 1}")
    print(f"Data type: {img.dtype}")

    # Calculate uncompressed image size in KB
    channels = img.shape[2] if len(img.shape) == 3 else 1
    dtype = img.dtype
    bytes_per_channel = 1 if dtype == 'uint8' else 4 if dtype == 'float32' else 2 if dtype == 'uint16' else 1
    size_bytes = width * height * channels * bytes_per_channel
    size_kb = size_bytes / 1024
    print(f"Uncompressed image size (Bytes): {size_bytes:.2f} bytes")
    print(f"Uncompressed image size: {size_kb:.2f} KB")

    if print_width_in and print_height_in:
        dpi_x = width / print_width_in
        dpi_y = height / print_height_in
        print(f"Calculated DPI: {dpi_x:.2f} x {dpi_y:.2f}")
    else:
        print("To calculate DPI, provide print_width_in and print_height_in (in inches).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print image details using central config")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args()

    config, config_path = load_config(args.config)
    image_path = resolve_path(config_path, config["paths"]["input_image"])
    details = config.get("image_details", {})
    print_image_details_cv2(
        str(image_path),
        print_width_in=details.get("print_width_in"),
        print_height_in=details.get("print_height_in")
    )