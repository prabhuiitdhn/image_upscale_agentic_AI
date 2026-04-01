import cv2
import os
import argparse

from config_loader import load_config, resolve_path

def convert_to_uncompressed(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("Error: Unable to open image with cv2.")
        return
    cv2.imwrite(output_path, img)
    print(f"Saved uncompressed image to: {output_path}")
    size_bytes = os.path.getsize(output_path)
    size_kb = size_bytes / 1024
    print(f"Uncompressed file size: {size_kb:.2f} KB ({size_bytes} bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert image to uncompressed format")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args()

    config, config_path = load_config(args.config)
    image_path = resolve_path(config_path, config["paths"]["input_image"])
    output_path = resolve_path(config_path, config["paths"]["uncompressed_output"])
    convert_to_uncompressed(str(image_path), str(output_path))
