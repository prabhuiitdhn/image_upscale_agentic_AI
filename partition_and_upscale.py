


import os
import subprocess
import tempfile
import uuid
import argparse
import numpy as np
from PIL import Image

from config_loader import load_config, resolve_path

def split_image_into_tiles(image, tile_size, overlap):
    """Split image into overlapping tiles."""
    h, w = image.shape[:2]
    tiles, positions = [], []
    for y in range(0, h, tile_size - overlap):
        for x in range(0, w, tile_size - overlap):
            tile = image[y:min(y+tile_size, h), x:min(x+tile_size, w)]
            tiles.append(tile)
            positions.append((x, y))
    return tiles, positions
# def merge_tiles(tiles, positions, image_shape, tile_size, overlap):

def merge_tiles_pil(tiles, positions, image_shape, tile_size, overlap):
    """Merge tiles using PIL to minimize RAM usage."""
    h, w = image_shape[:2]
    channels = tiles[0].shape[2] if len(tiles[0].shape) == 3 else 1
    dtype = tiles[0].dtype
    if channels == 1:
        mode = 'L' if dtype == np.uint8 else 'I;16' if dtype == np.uint16 else 'F'
    elif channels == 3:
        mode = 'RGB'
    elif channels == 4:
        mode = 'RGBA'
    else:
        raise ValueError('Unsupported channel count for saving image.')
    result_img = Image.new(mode, (w, h))
    for tile, (x, y) in zip(tiles, positions):
        tile_pil = Image.fromarray(tile, mode=mode)
        result_img.paste(tile_pil, (x, y))
    return np.array(result_img)

def merge_tiles_numpy(tiles, positions, image_shape, tile_size, overlap):
    """Merge tiles using numpy arrays (high RAM usage)."""
    h, w = image_shape[:2]
    result = np.zeros((h, w, tiles[0].shape[2]), dtype=tiles[0].dtype)
    count = np.zeros((h, w, 1), dtype=np.float32)
    for tile, (x, y) in zip(tiles, positions):
        h_tile, w_tile = tile.shape[:2]
        result[y:y+h_tile, x:x+w_tile] += tile
        count[y:y+h_tile, x:x+w_tile] += 1
    result = (result / np.maximum(count, 1)).astype(tiles[0].dtype)
    return result

def upscale_tile(tile, exe_path, temp_dir, model_name=None, scale=None):
    """Save tile using PIL, run external upscaler, and reload result as numpy array."""
    channels = tile.shape[2] if len(tile.shape) == 3 else 1
    dtype = tile.dtype
    if channels == 1:
        mode = 'L' if dtype == np.uint8 else 'I;16' if dtype == np.uint16 else 'F'
    elif channels == 3:
        mode = 'RGB'
    elif channels == 4:
        mode = 'RGBA'
    else:
        raise ValueError('Unsupported channel count for saving tile.')

    unique_id = uuid.uuid4().hex
    temp_input = os.path.join(temp_dir, f"tile_in_{unique_id}.png")
    temp_output = os.path.join(temp_dir, f"tile_out_{unique_id}.png")

    tile_pil = Image.fromarray(tile, mode=mode)
    tile_pil.save(temp_input)
    cmd = [exe_path, '-i', temp_input, '-o', temp_output]
    if model_name:
        cmd.extend(['-n', model_name])
    if scale:
        cmd.extend(['-s', str(scale)])

    subprocess.run(cmd, check=True)
    upscaled_pil = Image.open(temp_output)
    upscaled = np.array(upscaled_pil)
    os.remove(temp_input)
    os.remove(temp_output)
    return upscaled

def process_large_image(image_path, exe_path, output_path, tile_size=512, overlap=32, merge_method='pil', model_name=None, scale=None):
    """Main pipeline: split, upscale, and merge large image."""
    pil_img = Image.open(image_path)
    image = np.array(pil_img)
    if image is None:
        print("Error: Unable to open image.")
        return
    tiles, positions = split_image_into_tiles(image, tile_size, overlap)
    with tempfile.TemporaryDirectory(prefix="upscale_tiles_") as temp_dir:
        upscaled_tiles = [upscale_tile(tile, exe_path, temp_dir, model_name=model_name, scale=scale) for tile in tiles]

    scale = upscaled_tiles[0].shape[0] // tiles[0].shape[0]
    upscaled_positions = [(x*scale, y*scale) for (x, y) in positions]
    upscaled_shape = (image.shape[0]*scale, image.shape[1]*scale, image.shape[2])

    if merge_method == 'numpy':
        merged = merge_tiles_numpy(upscaled_tiles, upscaled_positions, upscaled_shape, tile_size*scale, overlap*scale)
        Image.fromarray(merged).save(output_path)
        print(f'Upscaled and merged image saved as {output_path}')
    else:
        merged = merge_tiles_pil(upscaled_tiles, upscaled_positions, upscaled_shape, tile_size*scale, overlap*scale)
        channels = merged.shape[2] if len(merged.shape) == 3 else 1
        dtype = merged.dtype
        if channels == 1:
            mode = 'L' if dtype == np.uint8 else 'I;16' if dtype == np.uint16 else 'F'
        elif channels == 3:
            mode = 'RGB'
        elif channels == 4:
            mode = 'RGBA'
        else:
            raise ValueError('Unsupported channel count for saving image.')
        Image.fromarray(merged, mode=mode).save(output_path)
        print(f'Upscaled and merged image saved as {output_path}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tile-based upscaling using central config")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args()

    config, config_path = load_config(args.config)
    paths_cfg = config["paths"]
    upscale_cfg = config.get("upscale", {})

    image_path = resolve_path(config_path, paths_cfg["upscaled_input_image"])
    exe_path = resolve_path(config_path, paths_cfg["realesrgan_exe"])
    output_path = resolve_path(config_path, paths_cfg["upscaled_output_image"])

    process_large_image(
        str(image_path),
        str(exe_path),
        str(output_path),
        tile_size=upscale_cfg.get("tile_size", 512),
        overlap=upscale_cfg.get("overlap", 32),
        merge_method=upscale_cfg.get("merge_method", "pil"),
        model_name=upscale_cfg.get("model_name"),
        scale=upscale_cfg.get("scale"),
    )
