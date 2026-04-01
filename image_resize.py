from PIL import Image
import os
import argparse

from config_loader import load_config, resolve_path

# Increase PIL's decompression bomb limit for large images
Image.MAX_IMAGE_PIXELS = None


def process_image(image_path, width=None, height=None, unit="pixels", dpi=96, output_path=None):
    """
    Detect image dimensions and optionally resize.
    Args:
        image_path: Path to the input image
        width: Target width (optional)
        height: Target height (optional)
        unit: "pixels", "cm", or "inches"
        dpi: Dots per inch (default 96)
        output_path: Path to save resized image (optional)
    """
    # Get dimensions
    orig_height, orig_width = get_dimensions(image_path, unit=unit, dpi=dpi)
    print(f"Original image height x width in {unit}: {orig_height:.2f} x {orig_width:.2f}")
    # Resize if requested
    if width is not None and height is not None:
        resize_image(image_path, width, height, unit=unit, dpi=dpi, output_path=output_path)
        print(f"Resized image to {height} x {width} {unit} and saved to {output_path}")

def get_dimensions(image_path, unit="pixels", dpi=96):
    """
    Get image height and width in specified units.
    Args:
        image_path: Path to the input image
        unit: "pixels", "cm", or "inches"
        dpi: Dots per inch (default 96)
    Returns:
        (height, width) in specified unit
    """
    img = Image.open(image_path)
    width_px, height_px = img.size
    if unit.lower() == "cm":
        pixels_per_cm = dpi / 2.54
        width = width_px / pixels_per_cm
        height = height_px / pixels_per_cm
    elif unit.lower() == "inches":
        width = width_px / dpi
        height = height_px / dpi
    else:
        width = width_px
        height = height_px
    return height, width

def resize_image(image_path, width, height, unit="pixels", dpi=96, output_path=None):
    """
    Resize an image based on specified units.
    
    Args:
        image_path: Path to the input image
        width: Target width
        height: Target height
        unit: "pixels", "cm", or "inches"
        dpi: Dots per inch (default 96)
        output_path: Path to save resized image
    """
    # Open image
    img = Image.open(image_path)
    
    # Convert dimensions to pixels
    if unit.lower() == "cm":
        pixels_per_cm = dpi / 2.54
        width_px = int(width * pixels_per_cm)
        height_px = int(height * pixels_per_cm)
    elif unit.lower() == "inches":
        width_px = int(width * dpi)
        height_px = int(height * dpi)
    else:  # pixels
        width_px = int(width)
        height_px = int(height)
    
    # Resize image
    resized_img = img.resize((width_px, height_px), Image.Resampling.LANCZOS)
    
    # Save if output path provided
    if output_path:
        resized_img.save(output_path)
        print(f"Image saved to {output_path}")
    
    return resized_img

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resize image using central config")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args()

    config, config_path = load_config(args.config)
    resize_cfg = config.get("resize", {})
    paths_cfg = config["paths"]

    input_image_path = resolve_path(config_path, paths_cfg["upscaled_output_image"])
    output_dir = resolve_path(config_path, paths_cfg["resize_output_dir"])
    output_name = resize_cfg.get("output_name", "resized_output.png")
    output_image_path = os.path.join(str(output_dir), output_name)

    process_image(
        str(input_image_path),
        width=resize_cfg.get("width"),
        height=resize_cfg.get("height"),
        unit=resize_cfg.get("unit", "pixels"),
        dpi=resize_cfg.get("dpi", 96),
        output_path=output_image_path,
    )