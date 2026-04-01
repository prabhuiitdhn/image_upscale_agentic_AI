import argparse

from config_loader import load_config
from main import print_image_details_cv2
from image_resize import process_image
from image_quality_check import compare_dimensions, show_edge_comparison
from partition_and_upscale import process_large_image
from uncompressed_image import convert_to_uncompressed
from config_loader import resolve_path
from github_sync_agent import run_github_sync_agent


def run_task(task_name, config, config_path):
    paths_cfg = config["paths"]

    if task_name == "image_details":
        image_path = resolve_path(config_path, paths_cfg["input_image"])
        details = config.get("image_details", {})
        print_image_details_cv2(
            str(image_path),
            print_width_in=details.get("print_width_in"),
            print_height_in=details.get("print_height_in"),
        )
        return

    if task_name == "uncompressed":
        image_path = resolve_path(config_path, paths_cfg["input_image"])
        output_path = resolve_path(config_path, paths_cfg["uncompressed_output"])
        convert_to_uncompressed(str(image_path), str(output_path))
        return

    if task_name == "upscale":
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
        return

    if task_name == "resize":
        resize_cfg = config.get("resize", {})
        input_image_path = resolve_path(config_path, paths_cfg["upscaled_output_image"])
        output_dir = resolve_path(config_path, paths_cfg["resize_output_dir"])
        output_name = resize_cfg.get("output_name", "resized_output.png")
        output_image_path = output_dir / output_name
        process_image(
            str(input_image_path),
            width=resize_cfg.get("width"),
            height=resize_cfg.get("height"),
            unit=resize_cfg.get("unit", "pixels"),
            dpi=resize_cfg.get("dpi", 96),
            output_path=str(output_image_path),
        )
        return

    if task_name == "quality_check":
        quality_cfg = config.get("quality_check", {})
        original_path = resolve_path(config_path, paths_cfg["upscaled_input_image"])
        upscaled_path = resolve_path(config_path, paths_cfg["upscaled_output_image"])
        compare_dimensions(str(original_path), str(upscaled_path))
        if quality_cfg.get("show_edges", True):
            show_edge_comparison(str(original_path), str(upscaled_path))
        return

    if task_name == "github_sync":
        git_cfg = config.get("git", {})
        run_github_sync_agent(
            default_repo_link=git_cfg.get("default_repo_link", ""),
            default_visibility=git_cfg.get("visibility", "private"),
        )
        return

    raise ValueError(f"Unknown task: {task_name}")


def run_agent(config_path):
    config, cfg_path = load_config(config_path)
    tasks = config.get("agent", {}).get("tasks", [])
    if not tasks:
        raise ValueError("No tasks found in config under 'agent.tasks'")

    for task in tasks:
        print(f"Running task: {task}")
        run_task(task, config, cfg_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Central workflow agent")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    args = parser.parse_args()
    run_agent(args.config)
