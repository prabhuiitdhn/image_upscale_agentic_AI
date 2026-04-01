import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import argparse

from config_loader import load_config, resolve_path

def compare_dimensions(orig_path, upscaled_path):
    orig = Image.open(orig_path)
    upscaled = Image.open(upscaled_path)
    print(f"Original size: {orig.size} (W x H)")
    print(f"Upscaled size: {upscaled.size} (W x H)")
    scale_x = upscaled.size[0] / orig.size[0]
    scale_y = upscaled.size[1] / orig.size[1]
    print(f"Scale factor: {scale_x:.2f}x (width), {scale_y:.2f}x (height)")

def show_edge_comparison(orig_path, upscaled_path):
    import cv2
    orig = np.array(Image.open(orig_path).convert('L'))
    upscaled = np.array(Image.open(upscaled_path).convert('L'))
    edges_orig = cv2.Canny(orig, 100, 200)
    edges_upscaled = cv2.Canny(upscaled, 100, 200)
    plt.figure(figsize=(10,5))
    plt.subplot(1,2,1)
    plt.title('Original Edges')
    plt.imshow(edges_orig, cmap='gray')
    plt.axis('off')
    plt.subplot(1,2,2)
    plt.title('Upscaled Edges')
    plt.imshow(edges_upscaled, cmap='gray')
    plt.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quality checks using central config")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args()

    config, config_path = load_config(args.config)
    paths_cfg = config["paths"]
    quality_cfg = config.get("quality_check", {})

    original_path = resolve_path(config_path, paths_cfg["upscaled_input_image"])
    upscaled_path = resolve_path(config_path, paths_cfg["upscaled_output_image"])

    compare_dimensions(str(original_path), str(upscaled_path))
    if quality_cfg.get("show_edges", True):
        show_edge_comparison(str(original_path), str(upscaled_path))
