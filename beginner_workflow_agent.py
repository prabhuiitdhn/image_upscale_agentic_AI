import argparse
import json
import subprocess
from pathlib import Path


PRESETS = {
    "fast": {
        "upscale": {
            "tile_size": 256,
            "overlap": 16,
            "merge_method": "pil",
            "model_name": "realesr-animevideov3",
            "scale": 2,
        },
        "tasks": ["upscale", "resize", "quality_check"],
    },
    "balanced": {
        "upscale": {
            "tile_size": 512,
            "overlap": 32,
            "merge_method": "pil",
            "model_name": "realesrgan-x4plus",
            "scale": 4,
        },
        "tasks": ["upscale", "resize", "quality_check"],
    },
    "quality": {
        "upscale": {
            "tile_size": 768,
            "overlap": 48,
            "merge_method": "pil",
            "model_name": "realesrgan-x4plus",
            "scale": 4,
        },
        "tasks": ["upscale", "resize", "quality_check"],
    },
}


def _ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, payload):
    with Path(path).open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def _build_runtime_config(base_config):
    config = dict(base_config)
    config["paths"] = dict(base_config.get("paths", {}))
    config["upscale"] = dict(base_config.get("upscale", {}))
    config["resize"] = dict(base_config.get("resize", {}))
    config["quality_check"] = dict(base_config.get("quality_check", {}))
    config["agent"] = dict(base_config.get("agent", {}))

    preset_name = _ask("Choose preset (fast/balanced/quality)", "balanced").lower()
    if preset_name not in PRESETS:
        print(f"Unknown preset '{preset_name}', using balanced.")
        preset_name = "balanced"

    preset = PRESETS[preset_name]
    config["upscale"].update(preset["upscale"])
    config["agent"]["tasks"] = list(preset["tasks"])

    input_image = _ask("Input image path", config["paths"].get("upscaled_input_image", "images/original/ABS1_4x.png"))
    output_image = _ask("Upscaled output image path", config["paths"].get("upscaled_output_image", "upscaled_merged_pil.png"))
    config["paths"]["upscaled_input_image"] = input_image
    config["paths"]["upscaled_output_image"] = output_image

    run_github_sync = _ask("Run GitHub sync after processing? (yes/no)", "no").lower()
    if run_github_sync in ("yes", "y"):
        config["agent"]["tasks"].append("github_sync")

    return config


def run_beginner_agent(config_path="config.json", runtime_config_path="config.runtime.json"):
    base_config = _load_json(config_path)
    runtime_config = _build_runtime_config(base_config)
    _write_json(runtime_config_path, runtime_config)

    print(f"Saved runtime config to {runtime_config_path}")
    cmd = ["python", "workflow_agent.py", "--config", runtime_config_path]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Beginner-friendly workflow runner")
    parser.add_argument("--config", default="config.json", help="Base config file")
    parser.add_argument("--runtime-config", default="config.runtime.json", help="Generated runtime config file")
    args = parser.parse_args()
    run_beginner_agent(args.config, args.runtime_config)
